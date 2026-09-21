"""Public /api/weekly tests: customer-safe boundary and privacy regression."""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

import main

CLIENT = TestClient(main.app)

PAYLOAD = {
    "birth": {"date": "1990-05-15", "time": "14:15", "place": "New Delhi, India",
              "latitude": 28.6139, "longitude": 77.209, "timezone": "Asia/Kolkata"},
    "forecast": {"startDate": "2026-09-21", "place": "New Delhi, India",
                 "latitude": 28.6139, "longitude": 77.209, "timezone": "Asia/Kolkata"},
}

FORBIDDEN = (
    "navtara", "navatara", "janma tara", "sampat", "vipat", "kshema", "pratyari",
    "sadhaka", "vadha", "mitra", "atimitra", "ati-mitra", "taranumber", "tara_number",
    "relativeposition", "relative_position", "janmanakshatra", "janma_nakshatra",
    "moonnakshatra", "moon_nakshatra", "specialroles", "special_roles", "jatinakshatra",
    "karmanakshatra", "deshanakshatra", "abhishekanakshatra", "sanghatikanakshatra",
    "samudayanakshatra", "adhananakshatra", "tara", "nakshatra",
)


def _post(payload=None):
    return CLIENT.post("/api/weekly", json=payload or PAYLOAD)


# --- endpoint works -------------------------------------------------------
def test_weekly_endpoint_returns_a_seven_day_safe_forecast():
    response = _post()
    assert response.status_code == 200
    body = response.json()
    assert body["startDate"] == "2026-09-21"
    assert body["endDate"] == "2026-09-27"
    assert len(body["days"]) == 7
    assert body["weekSummary"]
    assert body["timezone"] == "Asia/Kolkata"

    for day in body["days"]:
        assert set(day) == {"date", "headline", "summary", "periods"}
        assert day["periods"]
        for period in day["periods"]:
            assert set(period) == {"label", "start", "end", "afterTime", "headline",
                                   "guidance", "tone"}
            assert period["guidance"]


def test_weekly_highlights_are_safe_and_labelled():
    body = _post().json()
    for item in body["highlights"]:
        assert set(item) == {"label", "date", "time", "text"}
        assert item["label"] in ("Extra Care", "Supportive Window", "Good for Focused Effort",
                                 "Support From Others", "Practical/Resource Focus")
        assert item["text"]


# --- privacy regression on the REAL endpoint ------------------------------
def test_public_endpoint_contains_no_private_methodology():
    blob = json.dumps(_post().json()).lower()
    for term in FORBIDDEN:
        assert term not in blob, term


def test_no_private_keys_appear_even_as_absent_field_names():
    def keys(node):
        found = set()
        if isinstance(node, dict):
            for key, value in node.items():
                found.add(str(key).lower())
                found |= keys(value)
        elif isinstance(node, list):
            for item in node:
                found |= keys(item)
        return found

    present = keys(_post().json())
    for banned in ("tara", "relativeposition", "janmanakshatra", "moonnakshatra",
                   "specialroles", "nakshatra", "navtara"):
        assert banned not in present, banned


# --- invalid input --------------------------------------------------------
def test_invalid_birth_time_is_a_clean_error():
    payload = json.loads(json.dumps(PAYLOAD))
    payload["birth"]["time"] = "99:99"
    response = _post(payload)
    assert response.status_code == 400
    assert "couldn't prepare your week" in response.json()["message"]
    assert "traceback" not in json.dumps(response.json()).lower()


def test_missing_required_birth_field_is_rejected_by_validation():
    payload = json.loads(json.dumps(PAYLOAD))
    del payload["birth"]["date"]
    assert _post(payload).status_code == 422


# --- timezone handling ----------------------------------------------------
def test_forecast_timezone_is_respected_and_separate_from_birth():
    payload = json.loads(json.dumps(PAYLOAD))
    payload["forecast"].update({"timezone": "Europe/London", "latitude": 51.5074,
                                "longitude": -0.1278, "place": "London, United Kingdom"})
    body = _post(payload).json()
    assert body["timezone"] == "Europe/London"
    # transition times are local to the FORECAST location
    assert any("+" in day["periods"][0]["start"] or day["periods"][0]["start"] for day in body["days"])
    assert body["days"][0]["date"] == "2026-09-21"


def test_daily_methodology_untouched_and_no_other_inputs():
    body = _post().json()
    blob = json.dumps(body).lower()
    for banned in ("tithi", "karana", "yoga", "vara", "dasha", "ascendant", "house",
                   "aspect", "tarot", "gemini", "jupiter", "saturn"):
        assert banned not in blob, banned
