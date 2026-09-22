"""Location autocomplete for KAVACH.

Provider: **Geoapify** (`/v1/geocode/autocomplete`), called server-side only with
the `GEOAPIFY_API_KEY` environment variable. The key is never logged, returned to
a client, archived, or exposed to the browser.

This replaces the previous public Nominatim/OpenStreetMap lookup, whose endpoint
returned HTTP 429 for this workload in production. Nominatim has been removed
from the production request path entirely; Geoapify is the single provider.

Simple protections kept from the earlier hardening:
* normalized query keys (trim, casefold, collapse whitespace)
* small in-memory cache: 24h for hits, 5 minutes for empty results
* stale-while-error: a previously successful place keeps working during an outage
* single-flight: concurrent identical lookups share one upstream call
* circuit breaker: a 429 is never retried in a loop (cooldown), and timeouts/5xx
  get a short cooldown
* one short timeout, one attempt per query, no aggressive retries
* provider detail never reaches a client: failures become the friendly
  "temporarily unavailable" response and logs carry a category only
"""

from __future__ import annotations

import logging
import os
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

import httpx

logger = logging.getLogger("kavach.geocoding")

# --- configuration ----------------------------------------------------------
GEOAPIFY_API_KEY = (os.environ.get("GEOAPIFY_API_KEY") or "").strip()
GEOAPIFY_ENDPOINT = "https://api.geoapify.com/v1/geocode/autocomplete"
GEOAPIFY_ATTRIBUTION = "Powered by Geoapify"
PROVIDER_NAME = "geoapify"

POSITIVE_TTL_SECONDS = 24 * 3600.0
NEGATIVE_TTL_SECONDS = 300.0
RATE_LIMIT_COOLDOWN_SECONDS = 60.0
ERROR_COOLDOWN_SECONDS = 15.0
TIMEOUT_SECONDS = 8.0

UNAVAILABLE_MESSAGE = "Location search is temporarily unavailable. Please try again shortly."


# --- provider errors (provider text never escapes) --------------------------
class ProviderError(Exception):
    """Base class: something went wrong talking to the provider."""


class ProviderRateLimited(ProviderError):
    """The provider told us we are over its limit (HTTP 429)."""


class ProviderTimeout(ProviderError):
    """The provider did not answer in time."""


class ProviderUnavailable(ProviderError):
    """The provider is reachable but not serving us (5xx / network / no key)."""


# Backwards-compatible name: calculator.py imports this to surface a friendly,
# non-technical message when a location had to be resolved by name.
GeocoderRateLimited = ProviderRateLimited


def _provider_search(normalized: str, limit: int) -> List[Dict[str, Any]]:
    """One Geoapify autocomplete call. Returns [] when there is no match.

    Raises a normalized ProviderError subclass so callers can trip the breaker
    without ever seeing provider detail.
    """
    if not GEOAPIFY_API_KEY:
        # Not configured: fail closed, and never pretend there are no cities.
        logger.warning("ask_kavach geocoder=%s outcome=no_api_key", PROVIDER_NAME)
        raise ProviderUnavailable("no api key")

    try:
        response = httpx.get(
            GEOAPIFY_ENDPOINT,
            params={
                "text": normalized,
                "format": "json",
                "limit": limit,
                "lang": "en",
                "apiKey": GEOAPIFY_API_KEY,
            },
            timeout=TIMEOUT_SECONDS,
        )
    except httpx.TimeoutException as exc:
        raise ProviderTimeout("timed out") from exc
    except httpx.HTTPError as exc:
        raise ProviderUnavailable("network") from exc

    if response.status_code == 429:
        raise ProviderRateLimited("rate limited")
    if response.status_code >= 500:
        raise ProviderUnavailable(f"http {response.status_code}")
    if response.status_code >= 400:
        # 401/403 = key problem, 400 = bad request. Never surface the body.
        raise ProviderError(f"http {response.status_code}")

    try:
        payload = response.json()
    except ValueError as exc:
        raise ProviderError("malformed payload") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
        raise ProviderError("malformed payload")

    results: List[Dict[str, Any]] = []
    for row in payload["results"]:
        if not isinstance(row, dict):
            continue
        label = row.get("formatted") or row.get("address_line1")
        lat, lon = row.get("lat"), row.get("lon")
        if not label or lat is None or lon is None:
            continue
        try:
            results.append({"display": str(label), "lat": round(float(lat), 6), "lon": round(float(lon), 6)})
        except (TypeError, ValueError):
            continue
    return results


# --- shared state -----------------------------------------------------------
_CACHE: Dict[str, Tuple[List[Dict[str, Any]], float]] = {}
_INFLIGHT: Dict[str, threading.Event] = {}
_LOCK = threading.Lock()
_COOLDOWN_UNTIL = 0.0
_COOLDOWN_REASON = ""
_UPSTREAM_CALLS = 0
_LOGGED_MISSING_KEY = False


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
    logger.info("ask_kavach geocoder=%s outcome=%s cooldown_s=%s", PROVIDER_NAME, reason, int(seconds))


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
    global _COOLDOWN_UNTIL, _COOLDOWN_REASON, _UPSTREAM_CALLS, _LOGGED_MISSING_KEY
    with _LOCK:
        _CACHE.clear()
        _INFLIGHT.clear()
    _COOLDOWN_UNTIL = 0.0
    _COOLDOWN_REASON = ""
    _UPSTREAM_CALLS = 0
    _LOGGED_MISSING_KEY = False


def provider_state() -> Dict[str, Any]:
    """Operational snapshot (no key, no query text, no upstream payload)."""
    with _LOCK:
        cached = len(_CACHE)
        inflight = len(_INFLIGHT)
    return {
        "provider": PROVIDER_NAME,
        "api_key_configured": bool(GEOAPIFY_API_KEY),
        "cached_queries": cached,
        "in_flight": inflight,
        "upstream_calls": _UPSTREAM_CALLS,
        "cooldown_remaining_s": cooldown_remaining(),
        "cooldown_reason": _COOLDOWN_REASON,
        "attribution": GEOAPIFY_ATTRIBUTION,
    }


def _classify(exc: Exception) -> str:
    if isinstance(exc, ProviderRateLimited):
        return "rate_limited"
    if isinstance(exc, ProviderTimeout):
        return "timeout"
    if isinstance(exc, ProviderUnavailable):
        return "unavailable"
    return "error"


def search(query: str, limit: int = 6) -> Dict[str, Any]:
    """Cached, single-flight place search (Geoapify only).

    Always returns: {"status": "ok", "results": [...], "stale": bool}
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

    global _UPSTREAM_CALLS, _LOGGED_MISSING_KEY
    if not GEOAPIFY_API_KEY and not _LOGGED_MISSING_KEY:
        _LOGGED_MISSING_KEY = True
        logger.warning("ask_kavach geocoder=%s outcome=no_api_key", PROVIDER_NAME)
    if not GEOAPIFY_API_KEY:
        return {"status": "unavailable", "results": [], "message": UNAVAILABLE_MESSAGE}

    # Single-flight: followers wait for the leader instead of calling upstream.
    with _LOCK:
        leader = normalized not in _INFLIGHT
        if leader:
            _INFLIGHT[normalized] = threading.Event()
        event = _INFLIGHT[normalized]

    if not leader:
        event.wait(timeout=TIMEOUT_SECONDS + 1.0)
        entry = _cached(normalized)
        if entry:
            return {"status": "ok", "results": list(entry[0]), "stale": False}
        return {"status": "unavailable", "results": [], "message": UNAVAILABLE_MESSAGE}

    try:
        started = time.monotonic()
        _UPSTREAM_CALLS += 1
        results = _provider_search(normalized, limit)
        _store(normalized, results)
        logger.info(
            "ask_kavach geocoder=%s outcome=ok results=%d elapsed_ms=%d",
            PROVIDER_NAME, len(results), int((time.monotonic() - started) * 1000),
        )
        return {"status": "ok", "results": list(results), "stale": False}
    except Exception as exc:  # noqa: BLE001 - classify, never surface detail
        category = _classify(exc)
        if category == "rate_limited":
            _trip_breaker("rate_limited", RATE_LIMIT_COOLDOWN_SECONDS)
        elif category in ("timeout", "unavailable"):
            _trip_breaker(category, ERROR_COOLDOWN_SECONDS)
        else:
            logger.info("ask_kavach geocoder=%s outcome=error", PROVIDER_NAME)

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
        raise ProviderRateLimited(UNAVAILABLE_MESSAGE)
    results = outcome["results"]
    if not results:
        return None
    return float(results[0]["lat"]), float(results[0]["lon"])
