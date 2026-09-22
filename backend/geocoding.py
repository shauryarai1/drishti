"""Shared, hardened place geocoding for KAVACH.

Provider: **Nominatim / OpenStreetMap** through geopy, with a descriptive
user-agent so KAVACH identifies itself as the provider's usage policy requires.
We do not attempt to bypass the provider's rate limits, rotate identities or
proxy around restrictions - if the public endpoint is unsuitable for production
autocomplete traffic, that is reported rather than evaded.

Hardening (one shared implementation for every caller):

* normalized cache keys (casefold, collapsed whitespace)
* 24h TTL for successful lookups, a short TTL for empty/not-found results
* **stale-while-error**: a previously successful result keeps working during an
  upstream outage instead of breaking the product
* **single-flight**: concurrent identical lookups share one upstream call
* **circuit breaker**: on HTTP 429 / rate-limit responses the provider is not
  called again until the cooldown expires, so there is no retry storm
* upstream detail never reaches a client: callers get a clean "unavailable"
  state, and logs carry a category only (no queries, keys or stack traces)
"""

from __future__ import annotations

import logging
import os
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

from geopy.exc import GeocoderRateLimited, GeocoderTimedOut, GeocoderUnavailable
from geopy.geocoders import Nominatim

logger = logging.getLogger("kavach.geocoding")

USER_AGENT = "drishti-reading-platform-v1.0.0 (+https://drishti-5j3u.onrender.com)"
CONTACT_EMAIL = os.environ.get("NOMINATIM_CONTACT_EMAIL") or ""

POSITIVE_TTL_SECONDS = 24 * 3600.0
NEGATIVE_TTL_SECONDS = 300.0

# Circuit breaker windows.
RATE_LIMIT_COOLDOWN_SECONDS = 60.0
ERROR_COOLDOWN_SECONDS = 15.0

UPSTREAM_TIMEOUT_SECONDS = 8.0
UNRESOLVED_TIMEOUT_SECONDS = 2.0

UNAVAILABLE_MESSAGE = "Location search is temporarily unavailable. Please try again shortly."


def _make_geocoder() -> Nominatim:
    kwargs: Dict[str, Any] = {"user_agent": USER_AGENT, "timeout": UPSTREAM_TIMEOUT_SECONDS}
    if CONTACT_EMAIL:
        kwargs["user_agent"] = f"{USER_AGENT} (contact: {CONTACT_EMAIL})"
    return Nominatim(**kwargs)


_GEOCODER = _make_geocoder()

# normalized query -> (results, stored_at)
_CACHE: Dict[str, Tuple[List[Dict[str, Any]], float]] = {}
_INFLIGHT: Dict[str, threading.Event] = {}
_LOCK = threading.Lock()
_COOLDOWN_UNTIL = 0.0
_COOLDOWN_REASON = ""
_UPSTREAM_CALLS = 0


def normalize(query: str) -> str:
    """Trim, casefold and collapse internal whitespace (one cache key per query)."""
    return " ".join((query or "").split()).casefold()


def cooldown_remaining() -> float:
    return max(0.0, round(_COOLDOWN_UNTIL - time.monotonic(), 1))


def _in_cooldown() -> bool:
    return time.monotonic() < _COOLDOWN_UNTIL


def _trip_breaker(reason: str, seconds: float) -> None:
    global _COOLDOWN_UNTIL, _COOLDOWN_REASON
    _COOLDOWN_UNTIL = time.monotonic() + seconds
    _COOLDOWN_REASON = reason
    logger.info("ask_kavach geocoder=upstream outcome=%s cooldown_s=%s", reason, int(seconds))


def _cached(normalized: str) -> Optional[Tuple[List[Dict[str, Any]], float]]:
    with _LOCK:
        return _CACHE.get(normalized)


def _store(normalized: str, results: List[Dict[str, Any]]) -> None:
    with _LOCK:
        _CACHE[normalized] = (results, time.monotonic())


def _fresh(entry: Tuple[List[Dict[str, Any]], float]) -> bool:
    results, stored_at = entry
    ttl = POSITIVE_TTL_SECONDS if results else NEGATIVE_TTL_SECONDS
    return (time.monotonic() - stored_at) < ttl


def reset_state() -> None:
    """Test/diagnostic helper: clear cache, breaker and in-flight registry."""
    global _COOLDOWN_UNTIL, _COOLDOWN_REASON, _UPSTREAM_CALLS
    with _LOCK:
        _CACHE.clear()
        _INFLIGHT.clear()
    _COOLDOWN_UNTIL = 0.0
    _COOLDOWN_REASON = ""
    _UPSTREAM_CALLS = 0


def provider_state() -> Dict[str, Any]:
    """Operational snapshot (no secrets, no query text)."""
    with _LOCK:
        cached = len(_CACHE)
        inflight = len(_INFLIGHT)
    return {
        "provider": "nominatim",
        "user_agent_configured": bool(USER_AGENT),
        "cached_queries": cached,
        "in_flight": inflight,
        "upstream_calls": _UPSTREAM_CALLS,
        "cooldown_remaining_s": cooldown_remaining(),
        "cooldown_reason": _COOLDOWN_REASON,
    }


def _classify(exc: Exception) -> str:
    if isinstance(exc, GeocoderRateLimited):
        return "rate_limited"
    if isinstance(exc, GeocoderTimedOut):
        return "timeout"
    if isinstance(exc, GeocoderUnavailable):
        return "unavailable"
    text = str(exc).lower()
    if "429" in text or "too many requests" in text:
        return "rate_limited"
    return "error"


def _upstream_search(normalized: str, limit: int) -> List[Dict[str, Any]]:
    """One upstream call. Returns [] when the provider has no match."""
    global _UPSTREAM_CALLS
    started = time.monotonic()
    _UPSTREAM_CALLS += 1
    results = _GEOCODER.geocode(normalized, language="en", exactly_one=False, limit=limit)
    if results is None:
        results = []
    if not isinstance(results, list):
        results = [results]
    shaped = [
        {"display": item.address, "lat": round(float(item.latitude), 6), "lon": round(float(item.longitude), 6)}
        for item in results
    ]
    logger.info(
        "ask_kavach geocoder=upstream outcome=ok results=%d elapsed_ms=%d",
        len(shaped), int((time.monotonic() - started) * 1000),
    )
    return shaped


def search(query: str, limit: int = 6) -> Dict[str, Any]:
    """Cached, single-flight place search.

    Always returns a dict: {"status": "ok", "results": [...], "stale": bool}
    or {"status": "unavailable", "results": [], "message": ...}.
    """
    normalized = normalize(query)
    if len(normalized) < 3:
        return {"status": "ok", "results": [], "stale": False}

    entry = _cached(normalized)
    if entry and _fresh(entry):
        return {"status": "ok", "results": list(entry[0]), "stale": False}

    if _in_cooldown():
        # Provider is known to be rate-limiting us: serve last-known data if any.
        if entry:
            return {"status": "ok", "results": list(entry[0]), "stale": True}
        return {"status": "unavailable", "results": [], "message": UNAVAILABLE_MESSAGE}

    # Single-flight: followers wait for the leader instead of calling upstream.
    with _LOCK:
        leader = normalized not in _INFLIGHT
        if leader:
            _INFLIGHT[normalized] = threading.Event()
        event = _INFLIGHT[normalized]

    if not leader:
        event.wait(timeout=UPSTREAM_TIMEOUT_SECONDS + 1.0)
        entry = _cached(normalized)
        if entry:
            return {"status": "ok", "results": list(entry[0]), "stale": False}
        return {"status": "unavailable", "results": [], "message": UNAVAILABLE_MESSAGE}

    try:
        results = _upstream_search(normalized, limit)
        _store(normalized, results)
        return {"status": "ok", "results": list(results), "stale": False}
    except Exception as exc:  # noqa: BLE001 - classify, never surface detail
        category = _classify(exc)
        if category == "rate_limited":
            _trip_breaker("rate_limited", RATE_LIMIT_COOLDOWN_SECONDS)
        elif category in ("timeout", "unavailable"):
            _trip_breaker(category, ERROR_COOLDOWN_SECONDS)
        else:
            logger.info("ask_kavach geocoder=upstream outcome=error")

        if entry:
            # Stale-while-error: a previous successful place keeps working.
            return {"status": "ok", "results": list(entry[0]), "stale": True}
        return {"status": "unavailable", "results": [], "message": UNAVAILABLE_MESSAGE}
    finally:
        with _LOCK:
            _INFLIGHT.pop(normalized, None)
        event.set()


def resolve_coordinates(place: str) -> Optional[Tuple[float, float]]:
    """Coordinates for a place name, or None when the provider has no match.

    Raises GeocoderRateLimited only to signal "temporarily unavailable" so the
    caller can return a clean message; prefer supplying latitude/longitude.
    """
    outcome = search(place, limit=1)
    if outcome["status"] == "unavailable":
        raise GeocoderRateLimited(UNAVAILABLE_MESSAGE)
    results = outcome["results"]
    if not results:
        return None
    return float(results[0]["lat"]), float(results[0]["lon"])
