"""Provider adapter + breaker behaviour for the place-autocomplete backend.

HTTP is always mocked - no test consumes real provider quota.
"""

from __future__ import annotations

import json
import logging
import pathlib

import httpx
import pytest

import geocoding

REPO = pathlib.Path(__file__).resolve().parents[2]
DELHI_PAYLOAD = {
    "results": [
        {"formatted": "New Delhi, Delhi, India", "lat": 28.6139, "lon": 77.209},
        {"formatted": "Delhi, India", "lat": 28.7041, "lon": 77.1025},
    ]
}
FAKE_KEY = "geoapify-test-key-never-real"


class FakeResponse:
    def __init__(self, status_code: int = 200, payload=None, malformed: bool = False):
        self.status_code = status_code
        self._payload = payload
        self._malformed = malformed

    def json(self):
        if self._malformed:
            raise ValueError("not json")
        return self._payload


@pytest.fixture()
def http(monkeypatch):
    """Record every provider call and script the next response."""
    calls: list[dict] = []
    script = {"response": FakeResponse(200, DELHI_PAYLOAD)}

    def fake_get(url, params=None, timeout=None, **kwargs):
        calls.append({"url": url, "params": dict(params or {})})
        item = script["response"]
        if isinstance(item, Exception):
            raise item
        return item

    monkeypatch.setattr(geocoding.httpx, "get", fake_get)
    monkeypatch.setattr(geocoding, "GEOAPIFY_API_KEY", FAKE_KEY)
    monkeypatch.setattr(geocoding, "NOMINATIM_FALLBACK_ENABLED", False)
    geocoding.reset_state()
    yield {"calls": calls, "script": script}
    geocoding.reset_state()


# --- chain selection --------------------------------------------------------
def test_geoapify_is_the_only_production_provider(monkeypatch):
    monkeypatch.setattr(geocoding, "GEOAPIFY_API_KEY", FAKE_KEY)
    monkeypatch.setattr(geocoding, "NOMINATIM_FALLBACK_ENABLED", False)
    assert [name for name, _fn in geocoding.active_providers()] == ["geoapify"]


def test_nominatim_is_used_only_without_a_key_or_when_explicitly_enabled(monkeypatch):
    monkeypatch.setattr(geocoding, "GEOAPIFY_API_KEY", "")
    monkeypatch.setattr(geocoding, "NOMINATIM_FALLBACK_ENABLED", False)
    assert [name for name, _fn in geocoding.active_providers()] == ["nominatim"]

    monkeypatch.setattr(geocoding, "GEOAPIFY_API_KEY", FAKE_KEY)
    monkeypatch.setattr(geocoding, "NOMINATIM_FALLBACK_ENABLED", True)
    assert [name for name, _fn in geocoding.active_providers()] == ["geoapify", "nominatim"]


# --- success / no results ---------------------------------------------------
def test_provider_success_maps_to_display_lat_lon(http):
    outcome = geocoding.search("Delhi")

    assert outcome["status"] == "ok"
    assert [row["display"] for row in outcome["results"]] == [
        "New Delhi, Delhi, India", "Delhi, India"]
    assert outcome["results"][0]["lat"] == 28.6139
    assert set(outcome["results"][0]) == {"display", "lat", "lon"}

    call = http["calls"][0]
    assert call["url"] == geocoding.GEOAPIFY_ENDPOINT
    assert call["params"]["apiKey"] == FAKE_KEY, "the key must be sent as a request parameter"
    assert call["params"]["text"] == "delhi", "the query is normalized before the call"


def test_provider_no_results_is_a_valid_empty_answer(http):
    http["script"]["response"] = FakeResponse(200, {"results": []})
    outcome = geocoding.search("Nowhereville")

    assert outcome["status"] == "ok" and outcome["results"] == []
    assert len(http["calls"]) == 1


def test_short_queries_never_call_the_provider(http):
    assert geocoding.search("De")["results"] == []
    assert http["calls"] == []


# --- failure handling -------------------------------------------------------
def test_429_trips_the_breaker_and_never_retries(http):
    http["script"]["response"] = FakeResponse(429, {"error": "quota"})

    first = geocoding.search("Delhi")
    assert first["status"] == "unavailable"
    assert geocoding.cooldown_remaining() > 0
    assert geocoding.provider_state()["cooldown_reason"] == "rate_limited"

    for _ in range(5):
        assert geocoding.search("Delhi")["status"] == "unavailable"

    assert len(http["calls"]) == 1, "a 429 must not be retried in a loop"


def test_5xx_is_treated_as_unavailable_with_a_short_cooldown(http):
    http["script"]["response"] = FakeResponse(503, {"error": "down"})
    assert geocoding.search("Delhi")["status"] == "unavailable"
    assert geocoding.provider_state()["cooldown_reason"] == "unavailable"
    assert 0 < geocoding.cooldown_remaining() <= geocoding.ERROR_COOLDOWN_SECONDS


def test_timeout_is_handled_without_a_retry_storm(http):
    http["script"]["response"] = httpx.TimeoutException("slow")
    assert geocoding.search("Delhi")["status"] == "unavailable"
    assert geocoding.provider_state()["cooldown_reason"] == "timeout"
    assert len(http["calls"]) == 1


def test_malformed_provider_response_is_contained(http):
    http["script"]["response"] = FakeResponse(200, malformed=True)
    outcome = geocoding.search("Delhi")

    assert outcome["status"] == "unavailable"
    assert "not json" not in json.dumps(outcome)


def test_unexpected_payload_shape_is_contained(http):
    http["script"]["response"] = FakeResponse(200, {"unexpected": "shape"})
    assert geocoding.search("Delhi")["status"] == "unavailable"


def test_auth_failure_does_not_leak_the_body(http):
    http["script"]["response"] = FakeResponse(401, {"error": "invalid api key ABC123"})
    outcome = geocoding.search("Delhi")

    assert outcome["status"] == "unavailable"
    blob = json.dumps(outcome).lower()
    assert "invalid api key" not in blob and "abc123" not in blob


def test_partial_rows_are_skipped_rather_than_crashing(http):
    http["script"]["response"] = FakeResponse(200, {"results": [
        {"formatted": "Good, Place", "lat": 1.5, "lon": 2.5},
        {"formatted": "No coordinates"},
        {"lat": 3.0, "lon": 4.0},
        "not-an-object",
    ]})
    outcome = geocoding.search("Delhi")
    assert outcome["status"] == "ok"
    assert outcome["results"] == [{"display": "Good, Place", "lat": 1.5, "lon": 2.5}]


# --- optional emergency fallback --------------------------------------------
def test_fallback_provider_is_used_only_when_the_primary_fails(monkeypatch):
    monkeypatch.setattr(geocoding, "GEOAPIFY_API_KEY", FAKE_KEY)
    monkeypatch.setattr(geocoding, "NOMINATIM_FALLBACK_ENABLED", True)
    geocoding.reset_state()

    def failing_primary(_query, _limit):
        raise geocoding.ProviderRateLimited("rate limited")

    def fallback(_query, _limit):
        return [{"display": "Delhi, India", "lat": 28.6139, "lon": 77.209}]

    monkeypatch.setattr(geocoding, "active_providers",
                        lambda: [("geoapify", failing_primary), ("nominatim", fallback)])
    outcome = geocoding.search("Delhi")

    assert outcome["status"] == "ok"
    assert outcome["results"][0]["display"] == "Delhi, India"


# --- cache / concurrency / privacy -----------------------------------------
def test_cache_hit_does_not_call_the_provider_again(http):
    geocoding.search("Delhi")
    geocoding.search("delhi")
    assert len(http["calls"]) == 1


def test_concurrent_duplicate_queries_share_one_upstream_call(http):
    """Single-flight: parallel callers wait for the leader's result."""
    import threading

    results: list[dict] = []
    barrier = threading.Barrier(4)
    http["script"]["response"] = FakeResponse(200, DELHI_PAYLOAD)

    def worker():
        barrier.wait()
        results.append(geocoding.search("Delhi"))

    threads = [threading.Thread(target=worker) for _ in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert all(item["status"] == "ok" for item in results)
    assert len(http["calls"]) == 1, "concurrent identical lookups must share the provider call"


def test_stale_cache_is_served_when_the_provider_starts_failing(monkeypatch, http):
    geocoding.search("Delhi")
    monkeypatch.setattr(geocoding, "POSITIVE_TTL_SECONDS", -1.0)
    http["script"]["response"] = FakeResponse(429, {"error": "quota"})

    outcome = geocoding.search("Delhi")
    assert outcome["status"] == "ok" and outcome["stale"] is True


def test_provider_key_never_appears_in_logs_or_state(http, caplog):
    records: list[str] = []

    class Capture(logging.Handler):
        def emit(self, record):
            records.append(record.getMessage())

    logger = logging.getLogger("kavach.geocoding")
    handler = Capture()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    try:
        geocoding.search("Delhi")
        http["script"]["response"] = FakeResponse(429, {"error": "quota"})
        geocoding.search("Mumbai")
    finally:
        logger.removeHandler(handler)

    joined = "\n".join(records)
    assert "geocoder=geoapify" in joined
    assert FAKE_KEY not in joined
    assert FAKE_KEY not in json.dumps(geocoding.provider_state())
    # Logs carry categories, not query text or payloads.
    assert "quota" not in joined


def test_frontend_is_provider_agnostic():
    """No provider-specific code may appear in the frontend."""
    offenders = []
    for path in (REPO / "frontend-next").rglob("*.ts*"):
        if "node_modules" in path.parts or ".next" in path.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        for forbidden in ("geoapify", "nominatim", "geopy", "mapbox", "opencage"):
            if forbidden in text:
                offenders.append(f"{path.name}:{forbidden}")
    assert offenders == [], offenders
