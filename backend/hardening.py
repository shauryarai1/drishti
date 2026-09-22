"""Production hardening: dev-tool gating, body-size cap, rate limiting, headers.

All four concerns live here so the policy is centralized and does not leak into
astrology or provider code. Nothing here inspects or alters astrology payloads.

Policies
--------
* Inspector/trace tooling (`/api/dev/*`) is FAIL-CLOSED and explicit: allowed
  only when a development environment sets KAVACH_DEV_TOOLS=1, and never when
  KAVACH_ENV=production. Ordinary production requests cannot reach private model
  context, routing metadata or hidden reading mechanics.
* Request bodies over MAX_BODY_BYTES are rejected with 413 before any handler runs.
* Expensive/public endpoints are rate limited. Anonymous callers are keyed by
  trusted client IP; authenticated callers additionally get a per-token bucket
  with a higher allowance. The IP bucket always applies, so inventing or rotating
  tokens cannot lift the limit.
* Security headers are attached to every response (HSTS only over HTTPS).

Rate limiting limitations (important)
-------------------------------------
The limiter is IN-MEMORY and PER PROCESS:
  * counters reset whenever the service restarts or redeploys;
  * counters are not shared across multiple workers or Render instances, so the
    effective limit is per instance;
  * it is basic abuse protection, not a distributed security boundary.
A shared limiter (Redis/Upstash or a CDN rule) would need new infrastructure and
has deliberately not been added.
"""

from __future__ import annotations

import hashlib
import ipaddress
import json
import logging
import os
import time
from collections import deque
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("kavach.security")

DEV_PREFIX = "/api/dev/"
MAX_BODY_BYTES = 64 * 1024
WINDOW_SECONDS = 60.0
MAX_TRACKED_KEYS = 20_000

# (path prefix, anonymous limit, authenticated limit) per window. Longest prefix wins.
# Anonymous budgets are deliberately tighter than authenticated ones because a
# guest identity cannot be verified.
RATE_LIMITS: Tuple[Tuple[str, int, int], ...] = (
    ("/api/ask", 8, 20),
    ("/api/interpretation", 6, 15),
    ("/api/chart", 6, 15),
    ("/api/kundli", 10, 25),
    ("/api/life-summary", 12, 30),
    ("/api/weekly", 12, 30),
    ("/api/current-dasha-reading", 12, 30),
    ("/api/daily", 20, 60),
    ("/api/panchang", 30, 90),
    ("/api/places/search", 12, 30),
    ("/api/admin", 60, 240),
)
DEFAULT_LIMITS = (60, 180)

# Only these headers are added; none of them can break the JSON API contract.
SECURITY_HEADERS: Tuple[Tuple[str, str], ...] = (
    ("X-Content-Type-Options", "nosniff"),
    ("Referrer-Policy", "strict-origin-when-cross-origin"),
    ("X-Frame-Options", "DENY"),
    ("Permissions-Policy", "camera=(), microphone=(), geolocation=(), payment=()"),
    ("Cross-Origin-Opener-Policy", "same-origin"),
)
HSTS_HEADER = ("Strict-Transport-Security", "max-age=31536000; includeSubDomains")


def rate_limiting_enabled() -> bool:
    if os.environ.get("KAVACH_RATELIMIT", "").strip() == "0":
        return False
    return os.environ.get("KAVACH_ENV", "").lower() != "test"


def dev_tools_allowed() -> bool:
    """Explicit, fail-closed development gate (mirrors chat.trace.dev_tools_enabled)."""
    if os.environ.get("KAVACH_ENV", "").lower() == "production":
        return False
    return (os.environ.get("KAVACH_DEV_TOOLS") or "").strip() == "1"


def client_ip(scope: dict, headers: Dict[str, str]) -> str:
    """Trusted client IP.

    Render terminates TLS and appends the real client address to
    X-Forwarded-For, so only the LAST entry is trustworthy; client-supplied
    leading values are ignored. Anything unparseable falls back to the socket
    peer address.
    """
    forwarded = headers.get("x-forwarded-for", "")
    if forwarded:
        candidates = [part.strip() for part in forwarded.split(",") if part.strip()]
        if candidates:
            try:
                ipaddress.ip_address(candidates[-1])
                return candidates[-1]
            except ValueError:
                pass
    peer = scope.get("client")
    return peer[0] if peer else "unknown"


def bearer_token(headers: Dict[str, str]) -> Optional[str]:
    authorization = headers.get("authorization", "")
    if authorization.lower().startswith("bearer "):
        return authorization[7:].strip() or None
    return None


def token_fingerprint(token: str) -> str:
    """Stable, non-reversible bucket id. Raw tokens are never stored or logged."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]


def limits_for(path: str) -> Tuple[int, int]:
    """Return (anonymous_limit, authenticated_limit) for this path."""
    best = ""
    chosen = DEFAULT_LIMITS
    for prefix, anonymous, authenticated in RATE_LIMITS:
        if path.startswith(prefix) and len(prefix) > len(best):
            best, chosen = prefix, (anonymous, authenticated)
    return chosen


def buckets_for(scope: dict, headers: Dict[str, str]) -> List[Tuple[str, int]]:
    """Buckets to charge for this request.

    The IP bucket always applies and becomes the abuse ceiling, so a fabricated
    or rotated token cannot raise the limit; a genuine bearer token additionally
    gets its own higher-allowance bucket. A client-supplied user id is never
    used, and X-Kavach-Session is explicitly not treated as authentication.
    """
    guest_limit, user_limit = limits_for(scope.get("path", ""))
    ip_bucket = (f"ip:{client_ip(scope, headers)}", user_limit if bearer_token(headers) else guest_limit)
    token = bearer_token(headers)
    if token:
        return [ip_bucket, (f"user:{token_fingerprint(token)}", user_limit)]
    return [ip_bucket]


class RateLimiter:
    """Sliding-window limiter with a bounded number of tracked keys."""

    def __init__(self) -> None:
        self._hits: Dict[str, deque] = {}

    def reset(self) -> None:
        self._hits.clear()

    def check(self, key: str, limit: int, now: Optional[float] = None) -> Tuple[bool, int]:
        now = time.monotonic() if now is None else now
        cutoff = now - WINDOW_SECONDS
        hits = self._hits.get(key)
        if hits is None:
            if len(self._hits) >= MAX_TRACKED_KEYS:
                self._hits.clear()  # bounded memory: drop the oldest window wholesale
            hits = self._hits[key] = deque()
        while hits and hits[0] < cutoff:
            hits.popleft()
        if len(hits) >= limit:
            retry_after = max(1, int(WINDOW_SECONDS - (now - hits[0])) + 1)
            return False, retry_after
        hits.append(now)
        return True, 0

    def charge(self, buckets: List[Tuple[str, int]]) -> Tuple[bool, int]:
        """Charge every bucket. Allowed only when each bucket still has room."""
        allowed = True
        retry_after = 0
        for key, limit in buckets:
            ok, retry = self.check(key, limit)
            if not ok:
                allowed = False
                retry_after = max(retry_after, retry)
        return allowed, retry_after


LIMITER = RateLimiter()


async def _json_response(send, status: int, payload: Dict[str, Any], extra: Optional[List[Tuple[str, str]]] = None) -> None:
    body = json.dumps(payload).encode("utf-8")
    headers: List[Tuple[bytes, bytes]] = [
        (b"content-type", b"application/json"),
        (b"content-length", str(len(body)).encode()),
    ]
    for name, value in SECURITY_HEADERS:
        headers.append((name.lower().encode(), value.encode()))
    for name, value in extra or []:
        headers.append((name.lower().encode(), str(value).encode()))
    await send({"type": "http.response.start", "status": status, "headers": headers})
    await send({"type": "http.response.body", "body": body})


class HardeningMiddleware:
    """Pure ASGI middleware so it cannot interfere with FastAPI routing."""

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        method = (scope.get("method") or "").upper()
        headers = {
            key.decode("latin-1").lower(): value.decode("latin-1")
            for key, value in scope.get("headers", [])
        }

        # 1. Inspector/trace tooling gate (fail-closed, explicit opt-in only).
        if path.startswith(DEV_PREFIX) and not dev_tools_allowed():
            await _json_response(send, 404, {"status": "error", "message": "Not found"})
            return

        # 2. Body size cap.
        try:
            declared = int(headers.get("content-length") or 0)
        except ValueError:
            declared = MAX_BODY_BYTES + 1
        if declared > MAX_BODY_BYTES:
            await _json_response(
                send, 413, {"status": "error", "message": "Request payload too large."}
            )
            return

        # 3. Rate limiting (preflights are exempt).
        if method != "OPTIONS" and rate_limiting_enabled():
            allowed, retry_after = LIMITER.charge(buckets_for(scope, headers))
            if not allowed:
                # Log only the path and the retry hint: no token, IP, or identity.
                logger.info(
                    "ask_kavach security=ratelimit path=%s status=429 retry_after=%s",
                    path, retry_after,
                )
                await _json_response(
                    send, 429,
                    {"status": "error", "message": "Too many requests. Please try again shortly."},
                    extra=[("Retry-After", str(retry_after))],
                )
                return

        # 4. Security headers on the way out.
        https = headers.get("x-forwarded-proto", "").lower() == "https"

        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                extra = list(message.get("headers") or [])
                for name, value in SECURITY_HEADERS:
                    extra.append((name.encode(), value.encode()))
                if https:
                    extra.append((HSTS_HEADER[0].encode(), HSTS_HEADER[1].encode()))
                message["headers"] = extra
            await send(message)

        await self.app(scope, receive, send_with_headers)


def install_hardening(app) -> None:
    app.add_middleware(HardeningMiddleware)
