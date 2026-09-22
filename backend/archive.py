"""Owner-visible archive of product submissions.

This is deliberately separate from ``saved_readings`` (the signed-in user's own
private history). Writes and reads here happen only through this trusted server
process using the Supabase service-role key, which is never shipped to the
browser. The browser has no grant on these tables at all.

Design rules enforced here:
  * explicit per-product field allowlists — arbitrary payloads are never stored;
  * sensitive keys (passwords, tokens, cookies, headers, secrets) are rejected;
  * results are the customer-facing DTO only, with internal keys stripped;
  * archiving is fail-open: it must never break or delay a product response.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import time
from contextvars import ContextVar
from pathlib import Path
from typing import Any, Optional

import httpx

# Load backend/.env once, by explicit path so it does not depend on the process
# working directory. Nothing else in the backend loads this file at startup;
# chat/gemini.py loads it lazily and only for its own Gemini call. Values already
# present in the real environment always win (override=False), and a missing
# file or absent dotenv is not an error.
try:
    from dotenv import load_dotenv as _load_dotenv

    _load_dotenv(Path(__file__).resolve().with_name(".env"), override=False)
except Exception:  # pragma: no cover - dotenv is optional
    pass

logger = logging.getLogger("kavach.archive")

SCHEMA_VERSION = 1
TABLE = "product_submissions"
ADMIN_TABLE = "admin_users"

# "Today" for the admin dashboard is the UTC calendar day (00:00 to 24:00 UTC).
# UTC is deliberate: deterministic, no DST ambiguity, and the same boundary the
# database itself uses for timestamptz. The admin UI labels the tile "Today (UTC)".
STATS_TIMEZONE = "UTC"

# Escape hatch for operators: KAVACH_ARCHIVE=0 stops all archive writes.
def archiving_enabled() -> bool:
    return (os.environ.get("KAVACH_ARCHIVE") or "").strip() != "0"

PRODUCTS = ("kundli", "reading", "daily", "weekly", "life_summary", "dasha", "ask", "panchang")

STATUS_SUCCEEDED = "SUCCEEDED"
STATUS_FAILED = "FAILED"

MAX_INPUT_BYTES = 8_192
MAX_RESULT_BYTES = 262_144
MAX_STRING = 2_000
MAX_LIST = 200
MAX_DEPTH = 8
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200

BIRTH_FIELDS = ("name", "date", "time", "place", "latitude", "longitude", "timezone")

# Only these fields are ever persisted per product. Anything else is dropped.
INPUT_FIELDS: dict[str, tuple[str, ...]] = {
    "kundli": BIRTH_FIELDS,
    "reading": BIRTH_FIELDS,
    "life_summary": ("date", "time", "place", "latitude", "longitude", "timezone"),
    "panchang": ("date", "latitude", "longitude", "timezone", "label"),
    "daily": ("natal_moon", "at", "date", "time", "place", "latitude", "longitude", "timezone"),
    "ask": ("question", "conversation_id", "timestamp", "location_label"),
    "weekly": ("birth", "forecast"),
    "dasha": ("birth", "asOf"),
}

NESTED_INPUT_FIELDS: dict[str, dict[str, tuple[str, ...]]] = {
    "weekly": {
        "birth": BIRTH_FIELDS,
        "forecast": ("startDate", "place", "latitude", "longitude", "timezone"),
    },
    "dasha": {"birth": BIRTH_FIELDS},
}

_DENY_NORMALISED = {
    "password", "passwordconfirmation", "confirmpassword", "passwd", "pass",
    "token", "accesstoken", "refreshtoken", "idtoken", "resettoken", "jwttoken", "jwt",
    "authorization", "authheader", "cookie", "cookies", "setcookie",
    "apikey", "key", "secret", "clientsecret", "servicerole", "servicerolekey",
    "session", "sessionid", "localstorage", "localstoragedata", "fingerprint",
    "devicefingerprint", "ip", "ipaddress", "xforwardedfor", "headers", "rawheaders",
    "card", "cardnumber", "creditcard", "cvv", "cvc", "payment", "paymentmethod",
    "privatekey", "env", "environment",
}

# Never persisted inside a stored result either.
_DENY_RESULT_NORMALISED = _DENY_NORMALISED | {
    "reasoning", "chainofthought", "internalreasoning", "hiddenreasoning",
    "systemprompt", "developerprompt", "prompt", "prompts", "instruction",
    "instructions", "trace", "traces", "internaltrace", "provider", "providermetadata",
    "internaltrace", "ruleTrace", "rules", "internalenginestatus", "internal",
}

_SESSION_HEADER = "x-kavach-session"
# Guest session ids are non-identifying random values; only this shape is kept.
_SESSION_PATTERN = re.compile(r"[A-Za-z0-9_-]{8,64}")

_identity: ContextVar[dict[str, Optional[str]]] = ContextVar("kavach_identity", default={})


def _normalise(key: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(key).lower())


def _is_sensitive(key: str) -> bool:
    return _normalise(key) in _DENY_NORMALISED


def _is_internal_key(key: str) -> bool:
    return _normalise(key) in _DENY_RESULT_NORMALISED


def find_sensitive_paths(payload: Any, prefix: str = "", depth: int = 0) -> list[str]:
    """Returns dotted paths of any sensitive key found anywhere in a payload."""
    if depth > MAX_DEPTH:
        return []
    found: list[str] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            if _is_sensitive(key):
                found.append(path)
            else:
                found.extend(find_sensitive_paths(value, path, depth + 1))
    elif isinstance(payload, list):
        for index, value in enumerate(payload[:MAX_LIST]):
            found.extend(find_sensitive_paths(value, f"{prefix}[{index}]", depth + 1))
    return found


class RejectedInput(ValueError):
    """Raised when a submission must not be stored at all."""


def _clean_scalar(value: Any) -> Any:
    if isinstance(value, str):
        return value[:MAX_STRING]
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return None


def sanitise_input(product: str, raw: Any) -> dict[str, Any]:
    """Allowlist the permitted input fields for one product."""
    if product not in INPUT_FIELDS:
        raise RejectedInput(f"unsupported product: {product}")
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise RejectedInput("input must be an object")
    if _encoded_size(raw) > MAX_INPUT_BYTES:
        raise RejectedInput("input too large")

    sensitive = find_sensitive_paths(raw)
    if sensitive:
        raise RejectedInput("sensitive field rejected: " + ", ".join(sorted(set(sensitive))))

    allowed = INPUT_FIELDS[product]
    nested = NESTED_INPUT_FIELDS.get(product, {})
    clean: dict[str, Any] = {}

    for key in allowed:
        if key not in raw:
            continue
        value = raw[key]
        if key in nested:
            if isinstance(value, dict):
                inner = {}
                sensitive_inner = find_sensitive_paths(value)
                if sensitive_inner:
                    raise RejectedInput("sensitive field rejected: " + ", ".join(sorted(set(sensitive_inner))))
                for inner_key in nested[key]:
                    if inner_key in value and not _is_sensitive(inner_key):
                        inner[inner_key] = _clean_scalar(value[inner_key])
                if inner:
                    clean[key] = inner
            continue
        clean[key] = _clean_scalar(value)

    return clean


def sanitise_result(product: str, raw: Any, depth: int = 0) -> Any:
    """Keep the customer-facing result, dropping internal/secret keys."""
    if raw is None or depth > MAX_DEPTH:
        return None
    if isinstance(raw, dict):
        out: dict[str, Any] = {}
        for key, value in raw.items():
            if _is_internal_key(key):
                continue
            out[str(key)[:120]] = sanitise_result(product, value, depth + 1)
        return out
    if isinstance(raw, list):
        return [sanitise_result(product, item, depth + 1) for item in raw[:MAX_LIST]]
    return _clean_scalar(raw)


def _encoded_size(payload: Any) -> int:
    try:
        return len(json.dumps(payload, default=str).encode("utf-8"))
    except (TypeError, ValueError):
        return MAX_INPUT_BYTES + 1


def set_request_identity(token: Optional[str], session_id: Optional[str]) -> None:
    _identity.set({"token": token or None, "session_id": (session_id or None)})


def current_identity() -> dict[str, Optional[str]]:
    return _identity.get() or {}


# ---------------------------------------------------------------------------
# Supabase (service-role) transport
# ---------------------------------------------------------------------------
def _env(*names: str) -> Optional[str]:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value.strip()
    return None


class SupabaseStore:
    """Thin PostgREST/admin-API client. Server-side only."""

    def __init__(self) -> None:
        self._token_cache: dict[str, tuple[float, Optional[str]]] = {}
        self._admin_cache: dict[str, tuple[float, bool]] = {}

    # -- configuration ----------------------------------------------------
    @property
    def url(self) -> Optional[str]:
        return _env("SUPABASE_URL")

    @property
    def service_key(self) -> Optional[str]:
        return _env("SUPABASE_SERVICE_ROLE_KEY")

    def configured(self) -> bool:
        return bool(self.url and self.service_key)

    def _headers(self, prefer: Optional[str] = None) -> dict[str, str]:
        key = self.service_key or ""
        headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        if prefer:
            headers["Prefer"] = prefer
        return headers

    def _request(self, method: str, path: str, **kwargs) -> Optional[httpx.Response]:
        if not self.configured():
            return None
        try:
            with httpx.Client(timeout=4.0) as client:
                return client.request(method, f"{self.url}{path}", **kwargs)
        except Exception as exc:  # never let archiving break a product
            logger.warning("Archive transport error: %s", type(exc).__name__)
            return None

    # -- archive writes ---------------------------------------------------
    def insert(self, row: dict[str, Any]) -> Optional[str]:
        response = self._request(
            "POST",
            f"/rest/v1/{TABLE}",
            headers=self._headers("return=representation"),
            json=row,
        )
        if response is None or response.status_code >= 300:
            logger.warning("Archive insert skipped (status %s)", getattr(response, "status_code", "n/a"))
            return None
        try:
            data = response.json()
            return data[0]["id"] if data else None
        except Exception:
            return None

    # -- admin reads ------------------------------------------------------
    def query(
        self,
        filters: dict[str, str],
        select: str,
        limit: int,
        offset: int,
        count: bool = False,
    ) -> tuple[list[dict[str, Any]], int]:
        params = {"select": select, "order": "created_at.desc", "limit": str(limit), "offset": str(offset)}
        params.update(filters)
        headers = self._headers("count=exact" if count else None)
        response = self._request("GET", f"/rest/v1/{TABLE}", headers=headers, params=params)
        if response is None or response.status_code >= 300:
            return [], 0
        try:
            rows = response.json()
        except Exception:
            return [], 0
        total = len(rows)
        content_range = response.headers.get("content-range", "")
        if "/" in content_range:
            tail = content_range.split("/")[-1]
            if tail.isdigit():
                total = int(tail)
        return rows if isinstance(rows, list) else [], total

    def get(self, submission_id: str) -> Optional[dict[str, Any]]:
        response = self._request(
            "GET",
            f"/rest/v1/{TABLE}",
            headers=self._headers(),
            params={"id": f"eq.{submission_id}", "select": "*", "limit": "1"},
        )
        if response is None or response.status_code >= 300:
            return None
        try:
            rows = response.json()
            return rows[0] if rows else None
        except Exception:
            return None

    def delete(self, submission_id: str) -> bool:
        response = self._request(
            "DELETE",
            f"/rest/v1/{TABLE}",
            headers=self._headers("return=minimal"),
            params={"id": f"eq.{submission_id}"},
        )
        return response is not None and response.status_code < 300

    def stats(self, since_iso: str) -> dict[str, int]:
        def count_of(filters: dict[str, str]) -> int:
            rows, total = self.query(filters, select="id", limit=1, offset=0, count=True)
            return total if total else len(rows)

        empty: dict[str, str] = {}
        today: dict[str, str] = {"created_at": f"gte.{since_iso}"}
        out = {
            "total": count_of(empty),
            "today": count_of(today),
            "guests": count_of({"user_id": "is.null"}),
            "accounts": count_of({"user_id": "not.is.null"}),
        }
        for product in PRODUCTS:
            out[product] = count_of({"product": f"eq.{product}"})
        return out

    def is_admin(self, user_id: str) -> bool:
        cached = self._admin_cache.get(user_id)
        now = time.time()
        if cached and now - cached[0] < 60:
            return cached[1]

        response = self._request(
            "GET",
            f"/rest/v1/{ADMIN_TABLE}",
            headers=self._headers(),
            params={"user_id": f"eq.{user_id}", "select": "user_id", "limit": "1"},
        )
        allowed = False
        if response is not None and response.status_code < 300:
            try:
                allowed = bool(response.json())
            except Exception:
                allowed = False
        self._admin_cache[user_id] = (now, allowed)
        return allowed

    def email_for(self, user_id: str) -> Optional[str]:
        response = self._request(
            "GET",
            f"/auth/v1/admin/users/{user_id}",
            headers=self._headers(),
        )
        if response is None or response.status_code >= 300:
            return None
        try:
            email = response.json().get("email")
            return email if isinstance(email, str) else None
        except Exception:
            return None

    def verify_token(self, token: str) -> Optional[str]:
        """Resolve a Supabase access token to its user id (verified server-side)."""
        digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
        now = time.time()
        cached = self._token_cache.get(digest)
        if cached and now - cached[0] < 60:
            return cached[1]

        response = self._request(
            "GET",
            "/auth/v1/user",
            headers={"apikey": self.service_key or "", "Authorization": f"Bearer {token}"},
        )
        user_id: Optional[str] = None
        if response is not None and response.status_code < 300:
            try:
                candidate = response.json().get("id")
                user_id = candidate if isinstance(candidate, str) else None
            except Exception:
                user_id = None
        self._token_cache[digest] = (now, user_id)
        return user_id


store = SupabaseStore()


def resolve_user_id() -> Optional[str]:
    """Verified identity for the current request. Never from the request body."""
    token = current_identity().get("token")
    if not token:
        return None
    return store.verify_token(token)


def visitor_session_id() -> Optional[str]:
    session = current_identity().get("session_id")
    if not session:
        return None
    return session[:64]


def record_submission(
    product: str,
    input_data: Any,
    result_data: Any = None,
    *,
    status: str = STATUS_SUCCEEDED,
    error_category: Optional[str] = None,
    user_id: Optional[str] = None,
) -> Optional[str]:
    """Archive one product submission. Fail-open: never raises to the caller."""
    try:
        if not archiving_enabled() or not store.configured():
            return None

        clean_input = sanitise_input(product, input_data)
        if _encoded_size(clean_input) > MAX_INPUT_BYTES:
            raise RejectedInput("input too large")

        clean_result = sanitise_result(product, result_data)
        if clean_result is not None and _encoded_size(clean_result) > MAX_RESULT_BYTES:
            clean_result = None
            error_category = error_category or "result_too_large"

        if user_id is None:
            user_id = resolve_user_id()

        row = {
            "user_id": user_id,
            "visitor_session_id": visitor_session_id(),
            "product": product,
            "status": status if status in (STATUS_SUCCEEDED, STATUS_FAILED) else STATUS_SUCCEEDED,
            "input_data": clean_input,
            "result_data": clean_result,
            "error_category": (error_category or None) and str(error_category)[:120],
            "schema_version": SCHEMA_VERSION,
        }
        return store.insert(row)
    except RejectedInput as exc:
        logger.warning("Submission rejected: %s", exc)
        return None
    except Exception as exc:
        logger.warning("Submission not archived: %s", type(exc).__name__)
        return None


# ---------------------------------------------------------------------------
# Admin API
# ---------------------------------------------------------------------------
from fastapi import APIRouter, Header, HTTPException, Query  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402

router = APIRouter()

_LIST_SELECT = "id,created_at,completed_at,user_id,visitor_session_id,product,status,input_data,schema_version"
_RANGES = {"today": 1, "7d": 7, "30d": 30}


def _bearer(authorization: str) -> Optional[str]:
    value = (authorization or "").strip()
    if value.lower().startswith("bearer "):
        return value[7:].strip() or None
    return None


def _require_admin(authorization: str) -> str:
    if not store.configured():
        raise HTTPException(status_code=503, detail="Administration is not configured on this deployment.")
    token = _bearer(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Sign-in required.")
    user_id = store.verify_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Your session is no longer valid.")
    if not store.is_admin(user_id):
        raise HTTPException(status_code=403, detail="This account is not authorised for administration.")
    return user_id


def _filters(product: str, visitor: str, range_key: str, query: str) -> dict[str, str]:
    filters: dict[str, str] = {}
    if product and product != "all":
        if product not in PRODUCTS:
            raise HTTPException(status_code=400, detail="Unknown product filter.")
        filters["product"] = f"eq.{product}"
    if visitor == "guests":
        filters["user_id"] = "is.null"
    elif visitor == "accounts":
        filters["user_id"] = "not.is.null"
    if range_key in _RANGES:
        import datetime as _dt

        since = _dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(days=_RANGES[range_key])
        filters["created_at"] = f"gte.{since.isoformat()}"
    term = re.sub(r"[,()*%\\]", " ", (query or "").strip())[:80].strip()
    if term:
        like = f"*{term}*"
        filters["or"] = (
            f"(input_data->>name.ilike.{like},"
            f"input_data->>question.ilike.{like},"
            f"input_data->>place.ilike.{like},"
            f"product.ilike.{like},id.eq.{term})"
        )
    return filters


@router.get("/api/admin/stats")
async def admin_stats(authorization: str = Header(default="")):
    _require_admin(authorization)
    import datetime as _dt

    midnight = _dt.datetime.now(_dt.timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    return {
        "status": "ok",
        "stats": store.stats(midnight.isoformat()),
        # Documents the boundary used for "today" so the dashboard cannot mislead.
        "statsTimezone": STATS_TIMEZONE,
        "todayStartsAt": midnight.isoformat(),
    }


@router.get("/api/admin/submissions")
async def admin_list(
    authorization: str = Header(default=""),
    product: str = Query("all"),
    visitor: str = Query("all"),
    range: str = Query("all"),  # noqa: A002 - public API name
    q: str = Query(""),
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
):
    _require_admin(authorization)
    filters = _filters(product, visitor, range, q)
    offset = (page - 1) * page_size
    rows, total = store.query(filters, select=_LIST_SELECT, limit=page_size, offset=offset, count=True)

    account_ids = sorted({row["user_id"] for row in rows if row.get("user_id")})
    emails = {uid: store.email_for(uid) for uid in account_ids[:50]}
    for row in rows:
        row["account_email"] = emails.get(row.get("user_id")) if row.get("user_id") else None

    return {
        "status": "ok",
        "total": total,
        "page": page,
        "page_size": page_size,
        "submissions": rows,
    }


@router.get("/api/admin/submissions/{submission_id}")
async def admin_detail(submission_id: str, authorization: str = Header(default="")):
    _require_admin(authorization)
    if not re.fullmatch(r"[0-9a-fA-F-]{8,64}", submission_id):
        raise HTTPException(status_code=400, detail="Invalid submission id.")
    row = store.get(submission_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Submission not found.")
    row["account_email"] = store.email_for(row["user_id"]) if row.get("user_id") else None
    return {"status": "ok", "submission": row}


@router.delete("/api/admin/submissions/{submission_id}")
async def admin_delete(submission_id: str, authorization: str = Header(default="")):
    _require_admin(authorization)
    if not re.fullmatch(r"[0-9a-fA-F-]{8,64}", submission_id):
        raise HTTPException(status_code=400, detail="Invalid submission id.")
    if not store.delete(submission_id):
        return JSONResponse(status_code=502, content={"status": "error", "message": "Could not delete that submission."})
    return {"status": "ok", "deleted": submission_id}


# ---------------------------------------------------------------------------
# Installation
# ---------------------------------------------------------------------------
class IdentityMiddleware:
    """Capture verified-token and visitor-session headers for archive writes.

    Raw headers are read only to find these two values and are never persisted.
    """

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        token: Optional[str] = None
        session: Optional[str] = None
        for raw_key, raw_value in scope.get("headers", []):
            key = raw_key.decode("latin-1").lower()
            if key == "authorization":
                value = raw_value.decode("latin-1").strip()
                if value.lower().startswith("bearer "):
                    token = value[7:].strip() or None
            elif key == _SESSION_HEADER:
                candidate = raw_value.decode("latin-1").strip()
                # Anything outside the expected shape is dropped rather than stored.
                session = candidate if _SESSION_PATTERN.fullmatch(candidate) else None

        set_request_identity(token, session)
        await self.app(scope, receive, send)


def install_archive(app) -> None:
    """Attach the identity middleware and the protected admin API."""
    app.add_middleware(IdentityMiddleware)
    app.include_router(router)

