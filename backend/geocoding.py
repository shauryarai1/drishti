"""Location autocomplete for KAVACH, with a pluggable production provider.

Primary provider: **Geoapify** (`/v1/geocode/autocomplete`), a commercial
geocoding service whose free plan fits a small production app. The API key is
server-side only (Render env var `GEOAPIFY_API_KEY`); it is never logged, never
returned to a client and never exposed to the browser.

Provider history: KAVACH originally called **Nominatim / OpenStreetMap**
directly, which returned HTTP 429 for this workload from Render. Nominatim's
public endpoint is not intended for production autocomplete, so it has been
removed from the production request path. It remains available as an optional
emergency fallback (`GEOCODER_NOMINATIM_FALLBACK=1`) or automatically when no
Geoapify key is configured, which keeps local development working. We never
rotate identities, proxy around restrictions or retry aggressively.

Preserved architecture (unchanged in behaviour):
* normalized cache keys, 24h TTL for hits, short TTL for empty results
* stale-while-error: previously successful places keep working during an outage
* single-flight: concurrent identical lookups share one upstream call
* circuit breaker: on rate-limit/timeout the provider is not called again until
  the cooldown expires, so there is no retry storm
* provider internals and stack traces never reach a client
"""

from __future__ import annotations

import logging
import os
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

import httpx

logger = logging.getLogger("kavach.geocoding")

# --- configuration ----------------------------------------------------------
GEOAPIFY_API_KEY = (os.environ.get("GEOAPIFY_API_KEY") or "").strip()
GEOAPIFY_ENDPOINT = "https://api.geoapify.com/v1/geocode/autocomplete"
GEOAPIFY_ATTRIBUTION = "Powered by Geoapify"

NOMINATIM_USER_AGENT = "drishti-reading-platform-v1.0.0 (+https://drishti-5j3u.onrender.com)"
NOMINATIM_CONTACT_EMAIL = (os.environ.get("NOMINATIM_CONTACT_EMAIL") or "").strip()
NOMINATIM_FALLBACK_ENABLED = (os.environ.get("GEOCODER_NOMINATIM_FALLBACK") or "").strip() == "1"

POSITIVE_TTL_SECONDS = 24 * 3600.0
NEGATIVE_TTL_SECONDS = 300.0
RATE_LIMIT_COOLDOWN_SECONDS = 60.0
ERROR_COOLDOWN_SECONDS = 15.0
UPSTREAM_TIMEOUT_SECONDS = 8.0
UNRESOLVED_TIMEOUT_SECONDS = 2.0

UNAVAILABLE_MESSAGE = "Location search is temporarily unavailable. Please try again shortly."


# --- provider errors (no provider text ever escapes) ------------------------
class ProviderError(Exception):
    """Base class: something went wrong talking to a provider."""


class ProviderRateLimited(ProviderError):
    """The provider told us we are over its limit (HTTP 429)."""


class ProviderTimeout(ProviderError):
    """The provider did not answer in time."""


class ProviderUnavailable(ProviderError):
    """The provider is reachable but not serving us (5xx / network)."""


# Backwards-compatible name: calculator.py imports this to surface a friendly,
# non-technical message when no coordinates were supplied.
GeocoderRateLimited = ProviderRateLimited


# --- Geoapify (primary) -----------------------------------------------------
def _geoapify_search(normalized: str, limit: int) -> List[Dict[str, Any]]:
    """Auto-complete lookup. Returns [] when the provider has no match."""
    response = httpx.get(
        GEOAPIFY_ENDPOINT,
        params={
            "text": normalized,
            "format": "json",
            "limit": limit,
            "lang": "en",
            "apiKey": GEOAPIFY_API_KEY,
        },
        timeout=UPSTREAM_TIMEOUT_SECONDS,
    )
    if response.status_code == 429:
        raise ProviderRateLimited("rate limited")
    if response.status_code >= 500:
        raise ProviderUnavailable(f"http {response.status_code}")
    if response.status_code >= 400:
        # 401/403 = key problem, 400 = bad request: never surface the body.
        raise ProviderError(f"http {response.status_code}")

    payload = response.json()  # ValueError -> malformed
    if not isinstance(payload, dict):
        raise ProviderError("malformed payload")
    rows = payload.get("results")
    if rows is None:
        raise ProviderError("malformed payload")
    if not isinstance(rows, list):
        raise ProviderError("malformed payload")

    shaped: List[Dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        label = row.get("formatted") or row.get("address_line1")
        lat, lon = row.get("lat"), row.get("lon")
        if not label or lat is None or lon is None:
            continue
        try:
            shaped.append({"display": str(label), "lat": round(float(lat), 6), "lon": round(float(lon), 6)})
        except (TypeError, ValueError):
            continue
    return shaped


# --- Nominatim (optional fallback / local development) ----------------------
def _nominatim_search(normalized: str, limit: int) -> List[Dict[str, Any]]:
    from geopy.exc import GeocoderRateLimited as _GeoRateLimited
    from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
    from geopy.geocoders import Nominatim

    user_agent = NOMINATIM_USER_AGENT
    if NOMINATIM_CONTACT_EMAIL:
        user_agent = f"{user_agent} (contact: {NOMINATIM_CONTACT_EMAIL})"
    geocoder = Nominatim(user_agent=user_agent, timeout=UPSTREAM_TIMEOUT_SECONDS)

    try:
        results = geocoder.geocode(normalized, language="en", exactly_one=False, limit=limit)
    except _GeoRateLimited as exc:
        raise ProviderRateLimited("rate limited") from exc
    except GeocoderTimedOut as exc:
        raise ProviderTimeout("timed out") from exc
    except GeocoderUnavailable as exc:
        raise ProviderUnavailable("unavailable") from exc

    if results is None:
        return []
    if not isinstance(results, list):
        results = [results]
    return [
        {"display": item.address, "lat": round(float(item.latitude), 6), "lon": round(float(item.longitude), 6)}
        for item in results
    ]


def active_providers() -> List[Tuple[str, Callable[[str, int], List[Dict[str, Any]]]]]:
    """Provider chain, in order. Production uses Geoapify only."""
    chain: List[Tuple[str, Callable[[str, int], List[Dict[str, Any]]]]] = []
    if GEOAPIFY_API_KEY:
        chain.append(("geoapify", _geoapify_search))
    # Nominatim is a fallback of last resort (or the only provider locally).
    if NOMINATIM_FALLBACK_ENABLED or not GEOAPIFY_API_KEY:
        chain.append(("nominatim", _nominatim_search))
    return chain


def _provider_search(normalized: str, limit: int) -> List[Dict[str, Any]]:
    """Try each configured provider at most once, in order.

    A provider that answers with "no matches" is a valid result and stops the
    chain; only failures fall through. Errors are normalized so callers can
    trip the breaker without ever seeing provider detail.
    """
    global _UPSTREAM_CALLS
    errors: List[Exception] = []
    for name, provider in active_providers():
        started = time.monotonic()
        _UPSTREAM_CALLS += 1
        try:
            results = provider(normalized, limit)
        except ProviderError as exc:
            errors.append(exc)
            logger.info("ask_kavach geocoder=%s outcome=%s", name, _classify(exc))
            continue
        except (httpx.TimeoutException,) as exc:
            errors.append(ProviderTimeout("timed out"))
            logger.info("ask_kavach geocoder=%s outcome=timeout", name)
            continue
        except httpx.HTTPError as exc:
            errors.append(ProviderUnavailable("network"))
            logger.info("ask_kavach geocoder=%s outcome=unavailable", name)
            continue
        except ValueError:
            # Malformed JSON body.
            errors.append(ProviderError("malformed"))
            logger.info("ask_kavach geocoder=%s outcome=malformed", name)
            continue
        logger.info(
            "ask_kavach geocoder=%s outcome=ok results=%d elapsed_ms=%d",
            name, len(results), int((time.monotonic() - started) * 1000),
        )
        return results

    if errors:
        raise errors[0]
    return []


# --- shared state -----------------------------------------------------------
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
    logger.info("ask_kavach geocoder=provider outcome=%s cooldown_s=%s", reason, int(seconds))


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
        "providers": [name for name, _fn in active_providers()],
        "primary": (active_providers() or [("none", None)])[0][0],
        "api_key_configured": bool(GEOAPIFY_API_KEY),
        "cached_queries": cached,
        "in_flight": inflight,
        "upstream_calls": _UPSTREAM_CALLS,
        "cooldown_remaining_s": cooldown_remaining(),
        "cooldown_reason": _COOLDOWN_REASON,
        "attribution": GEOAPIFY_ATTRIBUTION if GEOAPIFY_API_KEY else "",
    }


def _classify(exc: Exception) -> str:
    if isinstance(exc, ProviderRateLimited):
        return "rate_limited"
    if isinstance(exc, ProviderTimeout):
        return "timeout"
    if isinstance(exc, ProviderUnavailable):
        return "unavailable"
    try:  # geopy fallback exceptions
        from geopy.exc import GeocoderRateLimited as _GeoRateLimited
        from geopy.exc import GeocoderTimedOut, GeocoderUnavailable

        if isinstance(exc, _GeoRateLimited):
            return "rate_limited"
        if isinstance(exc, GeocoderTimedOut):
            return "timeout"
        if isinstance(exc, GeocoderUnavailable):
            return "unavailable"
    except Exception:  # pragma: no cover - geopy always present
        pass
    text = str(exc).lower()
    if "429" in text or "too many requests" in text:
        return "rate_limited"
    return "error"


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
        results = _provider_search(normalized, limit)
        _store(normalized, results)
        return {"status": "ok", "results": list(results), "stale": False}
    except Exception as exc:  # noqa: BLE001 - classify, never surface detail
        category = _classify(exc)
        if category == "rate_limited":
            _trip_breaker("rate_limited", RATE_LIMIT_COOLDOWN_SECONDS)
        elif category in ("timeout", "unavailable"):
            _trip_breaker(category, ERROR_COOLDOWN_SECONDS)
        else:
            logger.info("ask_kavach geocoder=provider outcome=error")

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
