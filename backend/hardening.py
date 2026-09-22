"""Production hardening: dev-tool gating, body-size cap, rate limiting, headers.

All four concerns live here so the policy is centralized and does not leak into
astrology or provider code. Nothing here inspects or alters astrology payloads.

Policies
--------
* Dev tooling (`/api/dev/*`) is FAIL-CLOSED: only allowed when explicitly enabled
  with KAVACH_DEV_TOOLS=1, or (by default) when the caller is on loopback. It is
  never allowed when KAVACH_ENV=production.
* Request bodies over MAX_BODY_BYTES are rejected with 413 before any handler runs.
* Expensive/public endpoints are rate limited per client. Authenticated callers are
  keyed by a hash of their bearer token, guests by trusted client IP.
* Security headers are attached to every response (HSTS only over HTTPS).

Known limitation
----------------
The limiter is in-memory, per process. On a single Render instance that is
effective; it is not shared across instances, so it is abuse mitigation rather
than a hard guarantee. A distributed limiter would need shared infrastructure.
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
LOOPBACK_HOSTS = frozenset({"127.0.0.1", "::1", "localhost"})

# (path prefix, requests per window). Longest prefix wins.
RATE_LIMITS: Tuple[Tuple[str, int], ...] = (
    ("/api/ask", 12),
    ("/api/interpretation", 10),
    ("/api/chart", 10),
    ("/api/kundli", 15),
    ("/api/life-summary", 20),
    ("/api/weekly", 20),
    ("/api/current-dasha-reading", 20),
    ("/api/daily", 30),
    ("/api/panchang", 30),
    ("/api/places/search", 20),
    ("/api/admin", 120),
)
DEFAULT_LIMIT = 120

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


def dev_tools_allowed(client_host: str) -> bool:
    """Fail-closed dev policy: explicit opt-in, or loopback by default."""
    if os.environ.get("KAVACH_ENV", "").lower() == "production":
        return False
    explicit = (os.environ.get("KAVACH_DEV_TOOLS") or "").strip()
    if explicit == "0":
        return False
    if explicit == "1":
        return True
    return client_host in LOOPBACK_HOSTS


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


def client_key(scope: dict, headers: Dict[str, str]) -> str:
    """Authenticated callers are keyed by token hash, guests by client IP."""
    authorization = headers.get("authorization", "")
    if authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
        if token:
            digest = hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]
            return f"user:{digest}"
    return f"ip:{client_ip(scope, headers)}"


def limit_for(path: str) -> int:
    best = ""
    for prefix, limit in RATE_LIMITS:
        if path.startswith(prefix) and len(prefix) > len(best):
            best, chosen = prefix, limit
    return chosen if best else DEFAULT_LIMIT


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
        peer = scope.get("client")
        host = peer[0] if peer else ""

        # 1. Dev tooling gate (fail-closed).
        if path.startswith(DEV_PREFIX) and not dev_tools_allowed(host):
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
            allowed, retry_after = LIMITER.check(client_key(scope, headers), limit_for(path))
            if not allowed:
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
