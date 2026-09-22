"""Life Summary must use the SELECTED location's timezone, never a hardcoded one.

The geocoder is mocked; the timezone derivation is offline (timezonefinder).
"""

from __future__ import annotations

import pathlib

import pytest
from fastapi.testclient import TestClient

import main
from calculator import timezone_for

REPO = pathlib.Path(__file__).resolve().parents[2]
PAGE = REPO / "frontend-next" / "app" / "life-summary" / "page.tsx"

CITIES = {
    "Delhi": (28.6139, 77.209, "Asia/Kolkata"),
    "London": (51.5074, -0.1278, "Europe/London"),
    "New York": (40.7128, -74.006, "America/New_York"),
    "Dubai": (25.2048, 55.2708, "Asia/Dubai"),
    "Sydney": (-33.8688, 151.2093, "Australia/Sydney"),
}

PAYLOAD_BASE = {"date": "2010-01-21", "time": "08:19", "place": "Some Place"}


@pytest.fixture()
def captured(monkeypatch):
    """Capture the kwargs the endpoint hands to the summary builder."""
    seen: dict = {}

    def fake_build_life_summary(**kwargs):
        seen.update(kwargs)
        return {"status": "ok", "sections": []}

    monkeypatch.setattr(main, "build_life_summary", fake_build_life_summary)
    return seen


@pytest.fixture()
def client():
    return TestClient(main.app)


# --- the derivation helper --------------------------------------------------
@pytest.mark.parametrize("city,coords,expected", [(city, c[:2], c[2]) for city, c in CITIES.items()])
def test_timezone_is_derived_from_coordinates(city, coords, expected):
    assert timezone_for(*coords) == expected, city


def test_derivation_never_defaults_to_kolkata_for_other_coordinates():
    for city, (_lat, _lon, expected) in CITIES.items():
        if city != "Delhi":
            assert timezone_for(_lat, _lon) != "Asia/Kolkata"


# --- the endpoint -----------------------------------------------------------
@pytest.mark.parametrize("city,coords,expected", [(city, c[:2], c[2]) for city, c in CITIES.items()])
def test_life_summary_receives_the_selected_locations_timezone(client, captured, city, coords, expected):
    latitude, longitude = coords
    response = client.post("/api/life-summary", json={**PAYLOAD_BASE, "latitude": latitude,
                                                      "longitude": longitude})

    assert response.status_code == 200, response.text
    assert captured["timezone_name"] == expected, city


def test_explicit_timezone_is_not_needed_and_a_stale_one_is_corrected(client, captured):
    """A cached client sending the old hardcoded zone must still be corrected."""
    response = client.post("/api/life-summary", json={
        **PAYLOAD_BASE, "latitude": 51.5074, "longitude": -0.1278,
        "timezone": "Asia/Kolkata",  # stale value from the old frontend
    })

    assert response.status_code == 200
    assert captured["timezone_name"] == "Europe/London"


def test_ocean_coordinates_still_resolve_to_a_real_zone_never_kolkata(client, captured):
    """Even open-ocean coordinates resolve to a real IANA zone - no blanket default."""
    response = client.post("/api/life-summary", json={**PAYLOAD_BASE, "latitude": 0.0,
                                                      "longitude": -140.0})
    assert response.status_code == 200
    assert captured["timezone_name"] != "Asia/Kolkata"


def test_supplied_timezone_is_used_only_when_derivation_is_impossible(monkeypatch, client, captured):
    """If (and only if) no zone can be derived, the supplied value wins."""
    import calculator

    monkeypatch.setattr(calculator, "timezone_for", lambda lat, lon: None)
    ocean = {**PAYLOAD_BASE, "latitude": 0.0, "longitude": -140.0}

    assert client.post("/api/life-summary", json={**ocean, "timezone": "Pacific/Honolulu"}).status_code == 200
    assert captured["timezone_name"] == "Pacific/Honolulu"

    # No coordinates resolvable and nothing supplied: the app default is the last resort.
    assert client.post("/api/life-summary", json=ocean).status_code == 200
    assert captured["timezone_name"] == "Asia/Kolkata"


def test_coordinates_are_forwarded_unchanged(client, captured):
    response = client.post("/api/life-summary", json={**PAYLOAD_BASE, "latitude": 51.5074,
                                                      "longitude": -0.1278})
    assert response.status_code == 200
    assert captured["latitude"] == 51.5074 and captured["longitude"] == -0.1278


# --- place search now carries the zone --------------------------------------
def test_places_search_results_include_the_derived_timezone(monkeypatch, client):
    import geocoding

    def fake_provider(_query, _limit):
        return [{"display": "London, UK", "lat": 51.5074, "lon": -0.1278}]

    monkeypatch.setattr(geocoding, "active_providers", lambda: [("fake", fake_provider)])
    geocoding.reset_state()

    body = client.get("/api/places/search", params={"q": "London"}).json()
    assert body["status"] == "ok"
    assert body["results"][0]["timezone"] == "Europe/London"
    # Existing fields are untouched (display/lat/lon contract preserved).
    assert set(body["results"][0]) >= {"display", "lat", "lon", "timezone"}


# --- frontend ---------------------------------------------------------------
def test_frontend_no_longer_hardcodes_the_timezone():
    source = PAGE.read_text(encoding="utf-8")
    assert "timezone: 'Asia/Kolkata'" not in source, "the hardcoded zone must be gone"
    assert "selectedTimezone" in source, "the selected place's timezone must be carried"
    assert "(selectedTimezone ? { timezone: selectedTimezone } : {})" in source
    assert "setSelectedTimezone(h.timezone)" in source
