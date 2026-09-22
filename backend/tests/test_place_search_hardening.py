"""Location-search hardening: caching, circuit breaker, and coordinate bypass.

The external geocoder is ALWAYS mocked here - no test touches Nominatim, and no
test touches production Supabase (the archive is isolated by conftest).
"""

from __future__ import annotations

import json
import pathlib

import pytest
from fastapi.testclient import TestClient
from geopy.exc import GeocoderRateLimited, GeocoderTimedOut

import geocoding
import main

REPO = pathlib.Path(__file__).resolve().parents[2]
FRONTEND = REPO / "frontend-next"

DELHI_RESULTS = [
    {"display": "New Delhi, Delhi, India", "lat": 28.6139, "lon": 77.209},
    {"display": "Delhi, India", "lat": 28.7041, "lon": 77.1025},
]
COORDS = {"latitude": 28.6139, "longitude": 77.209, "timezone": "Asia/Kolkata", "place": "New Delhi, India"}
BIRTH = {"date": "2010-01-21", "time": "08:19", **COORDS}


class FakeLocation:
    def __init__(self, address, latitude, longitude):
        self.address = address
        self.latitude = latitude
        self.longitude = longitude


class FakeGeocoder:
    """Scriptable stand-in for the real provider client."""

    def __init__(self):
        self.calls = 0
        self.mode = "ok"

    def geocode(self, query, **kwargs):
        self.calls += 1
        if self.mode == "rate_limited":
            raise GeocoderRateLimited("HTTP Error 429: Too many requests")
        if self.mode == "timeout":
            raise GeocoderTimedOut("timed out")
        if self.mode == "empty":
            return []
        if self.mode == "boom":
            raise RuntimeError("upstream exploded")
        return [FakeLocation(item["display"], item["lat"], item["lon"]) for item in DELHI_RESULTS]


@pytest.fixture()
def fake_geocoder(monkeypatch):
    fake = FakeGeocoder()
    monkeypatch.setattr(geocoding, "_GEOCODER", fake)
    geocoding.reset_state()
    yield fake
    geocoding.reset_state()


@pytest.fixture()
def client():
    return TestClient(main.app)


# --- normalization / caching -------------------------------------------------
def test_short_queries_never_reach_the_provider(fake_geocoder):
    assert geocoding.search("De")["results"] == []
    assert geocoding.search("D")["results"] == []
    assert fake_geocoder.calls == 0


def test_normalized_duplicates_share_one_upstream_call(fake_geocoder):
    first = geocoding.search("Delhi")
    second = geocoding.search("  delhi  ")
    third = geocoding.search("DELHI")

    assert first["results"] == second["results"] == third["results"]
    assert fake_geocoder.calls == 1, "normalized duplicates must reuse the cache"


def test_cached_lookup_does_not_call_upstream_again(fake_geocoder):
    geocoding.search("New Delhi")
    geocoding.search("New Delhi")
    assert fake_geocoder.calls == 1
    assert geocoding.provider_state()["cached_queries"] >= 1


def test_empty_results_are_cached_briefly(fake_geocoder):
    fake_geocoder.mode = "empty"
    assert geocoding.search("Nowhereville")["results"] == []
    assert geocoding.search("nowhereville")["results"] == []
    assert fake_geocoder.calls == 1, "a not-found result must be cached briefly too"


# --- 429 / breaker ----------------------------------------------------------
def test_upstream_429_trips_the_breaker_without_a_retry_storm(fake_geocoder):
    fake_geocoder.mode = "rate_limited"

    first = geocoding.search("Delhi")
    assert first["status"] == "unavailable"
    assert geocoding.cooldown_remaining() > 0

    for _ in range(6):
        outcome = geocoding.search("Delhi")
        assert outcome["status"] == "unavailable"

    assert fake_geocoder.calls == 1, "a 429 must not be retried in a loop"
    state = geocoding.provider_state()
    assert state["cooldown_reason"] == "rate_limited"


def test_stale_cache_is_served_during_a_rate_limit(fake_geocoder, monkeypatch):
    geocoding.search("Delhi")
    # Force the entry to be stale, then break the provider.
    monkeypatch.setattr(geocoding, "POSITIVE_TTL_SECONDS", -1.0)
    fake_geocoder.mode = "rate_limited"

    outcome = geocoding.search("Delhi")
    assert outcome["status"] == "ok", "a previously successful place must keep working"
    assert outcome["stale"] is True
    assert outcome["results"][0]["display"].startswith("New Delhi")


def test_timeout_also_trips_a_short_breaker(fake_geocoder):
    fake_geocoder.mode = "timeout"
    assert geocoding.search("Delhi")["status"] == "unavailable"
    assert geocoding.cooldown_remaining() > 0
    assert geocoding.provider_state()["cooldown_reason"] == "timeout"


def test_unexpected_upstream_error_is_not_leaked(fake_geocoder):
    fake_geocoder.mode = "boom"
    outcome = geocoding.search("Delhi")
    assert outcome["status"] == "unavailable"
    assert "exploded" not in json.dumps(outcome)


# --- HTTP contract ----------------------------------------------------------
def test_places_endpoint_returns_results(fake_geocoder, client):
    response = client.get("/api/places/search", params={"q": "Delhi"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert len(body["results"]) == 2
    assert set(body["results"][0]) == {"display", "lat", "lon"}


def test_places_endpoint_returns_a_clean_unavailable_response(fake_geocoder, client):
    fake_geocoder.mode = "rate_limited"
    response = client.get("/api/places/search", params={"q": "Delhi"})

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "unavailable"
    assert "temporarily unavailable" in body["message"]

    blob = json.dumps(body).lower()
    for forbidden in ("nominatim", "geopy", "traceback", "429", "openstreetmap", "user-agent"):
        assert forbidden not in blob, forbidden


def test_places_endpoint_rejects_short_queries(client):
    assert client.get("/api/places/search", params={"q": "De"}).status_code == 422


def test_places_endpoint_never_exposes_internals_on_success(fake_geocoder, client):
    blob = json.dumps(client.get("/api/places/search", params={"q": "Delhi"}).json()).lower()
    for forbidden in ("nominatim", "geopy", "user-agent", "api_key", "authorization"):
        assert forbidden not in blob


# --- selected coordinates bypass geocoding ----------------------------------
@pytest.mark.parametrize("product,request_spec", [
    ("kundli", ("POST", "/api/kundli", {**BIRTH, "name": "Test Native"})),
    ("reading", ("POST", "/api/interpretation", BIRTH)),
    ("life_summary", ("POST", "/api/life-summary", BIRTH)),
    ("weekly", ("POST", "/api/weekly", {"birth": BIRTH, "forecast": {
        "startDate": "2026-09-22", **COORDS}})),
])
def test_products_work_with_selected_coordinates_while_the_geocoder_is_down(fake_geocoder, client, product, request_spec):
    fake_geocoder.mode = "rate_limited"
    method, path, payload = request_spec
    response = client.post(path, json=payload)

    assert response.status_code == 200, f"{product}: {response.text[:200]}"
    assert fake_geocoder.calls == 0, f"{product} must not re-geocode supplied coordinates"


def test_panchang_uses_supplied_coordinates(fake_geocoder, client):
    fake_geocoder.mode = "rate_limited"
    response = client.get("/api/panchang", params={**COORDS, "date": "2026-09-22"})
    assert response.status_code == 200
    assert fake_geocoder.calls == 0


def test_coordinate_bypass_holds_while_the_breaker_is_open(fake_geocoder, client):
    fake_geocoder.mode = "rate_limited"
    geocoding.search("Delhi")  # open the breaker

    assert client.post("/api/kundli", json={**BIRTH, "name": "Test Native"}).status_code == 200
    assert fake_geocoder.calls == 1, "only the explicit place search hit the (mocked) provider"


# --- provider policy + frontend behaviour -----------------------------------
def test_geocoder_identifies_itself_per_provider_policy():
    assert geocoding.USER_AGENT.startswith("drishti-")
    assert "http" in geocoding.USER_AGENT or "contact" in geocoding.USER_AGENT.lower()
    assert geocoding.USER_AGENT.lower() not in ("geopy", "python-requests", "mozilla/5.0")


def test_frontend_autocomplete_is_debounced_and_guards_stale_results():
    source = (FRONTEND / "components" / "BirthDetails.tsx").read_text(encoding="utf-8")
    assert "}, 450);" in source, "autocomplete must be debounced around 400-500ms"
    assert "cancelled" in source, "stale responses must be ignored"
    assert "Location search is temporarily unavailable" in source


def test_frontend_shared_client_requires_three_chars_and_dedupes():
    source = (FRONTEND / "lib" / "api.ts").read_text(encoding="utf-8")
    assert "trimmed.length < 3" in source
    assert "placeInFlight" in source and "placeLookups" in source
    assert "searchPlacesDetailed" in source

    life_summary = (FRONTEND / "app" / "life-summary" / "page.tsx").read_text(encoding="utf-8")
    assert "searchPlacesDetailed" in life_summary
    assert "Location search is temporarily unavailable" in life_summary
