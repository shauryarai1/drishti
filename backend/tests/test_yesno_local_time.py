"""KAVACH YES / NO: local-time reliability.

The engine, number reduction, planet mapping, the directional registry and the
verdict mapping are unchanged. These tests cover the TIME INPUT only: the
browser's IANA zone cross-checked against its reported UTC offset, the
deterministic fallback when they disagree, backwards compatibility, and the
privacy-safe diagnostics.
"""

from __future__ import annotations

import logging
import pathlib

import pytest
from fastapi.testclient import TestClient

import main
from yesno.timezone import resolve_local_time, zone_offset_minutes

REPO = pathlib.Path(__file__).resolve().parents[2]
FRONTEND = REPO / "frontend-next"

INSTANT = "2026-09-22T12:56:00+00:00"   # 18:26 in Asia/Kolkata
IST_OFFSET = 330                        # minutes east of UTC


def _ask(payload):
    return TestClient(main.app).post("/api/yes-no", json=payload)


# --- 15. the exact regression fixture ---------------------------------------
def test_1826_asia_kolkata_resolves_to_1826_and_no():
    body = _ask({"question": "Will it work?", "timestamp": INSTANT,
                 "timezone": "Asia/Kolkata", "utc_offset_minutes": IST_OFFSET}).json()

    assert body["status"] == "ok"
    assert body["local_time"] == "18:26"
    assert body["verdict"] == "NO", "Mars -> Saturn is ENEMY"


# --- 1/2. correct zone, and an incorrect zone with a correct offset ---------
def test_correct_zone_with_matching_offset_uses_the_zone():
    body = _ask({"question": "q", "timestamp": INSTANT,
                 "timezone": "Asia/Kolkata", "utc_offset_minutes": IST_OFFSET}).json()
    assert body["local_time"] == "18:26"
    assert body["verdict"] == "NO"


def test_incorrect_zone_with_correct_offset_falls_back_to_the_device_clock():
    """A UTC zone with a +330 device offset must still evaluate 18:26."""
    body = _ask({"question": "q", "timestamp": INSTANT,
                 "timezone": "UTC", "utc_offset_minutes": IST_OFFSET}).json()
    assert body["status"] == "ok"
    assert body["local_time"] == "18:26", "the device clock wins on mismatch"
    assert body["verdict"] == "NO"


def test_mismatch_resolution_reports_the_fallback_source():
    from datetime import datetime

    instant = datetime.fromisoformat(INSTANT)
    local, resolution = resolve_local_time(instant, "UTC", IST_OFFSET)
    assert local.strftime("%H:%M") == "18:26"
    assert resolution["source"] == "offset_fallback"
    assert resolution["matched"] is False

    _, ok = resolve_local_time(instant, "Asia/Kolkata", IST_OFFSET)
    assert ok["source"] == "iana+offset" and ok["matched"] is True


# --- 3. DST ------------------------------------------------------------------
@pytest.mark.parametrize("instant,zone,offset,expected", [
    # London: BST (+60) in September, GMT (0) in January.
    ("2026-09-22T12:56:00+00:00", "Europe/London", 60, "13:56"),
    ("2026-01-15T12:56:00+00:00", "Europe/London", 0, "12:56"),
    # New York: EDT (-240) in September, EST (-300) in January.
    ("2026-09-22T12:56:00+00:00", "America/New_York", -240, "08:56"),
    ("2026-01-15T12:56:00+00:00", "America/New_York", -300, "07:56"),
])
def test_dst_offsets_are_validated_per_instant(instant, zone, offset, expected):
    body = _ask({"question": "q", "timestamp": instant, "timezone": zone,
                 "utc_offset_minutes": offset}).json()
    assert body["status"] == "ok"
    assert body["local_time"] == expected


def test_stale_dst_offset_is_treated_as_a_mismatch():
    """A January instant sent with a summer offset must not use the wrong clock."""
    body = _ask({"question": "q", "timestamp": "2026-01-15T12:56:00+00:00",
                 "timezone": "Europe/London", "utc_offset_minutes": 60}).json()
    assert body["local_time"] == "13:56", "the submitted device offset is used"
    assert body["verdict"] in {"YES", "NO", "50/50"}


# --- 4/5. half-hour and quarter-hour offsets --------------------------------
def test_half_hour_zone():
    body = _ask({"question": "q", "timestamp": INSTANT, "timezone": "Asia/Kolkata",
                 "utc_offset_minutes": 330}).json()
    assert body["local_time"] == "18:26"


def test_quarter_hour_offset_is_supported():
    """+05:45 (Kathmandu) has no whole-hour equivalent."""
    body = _ask({"question": "q", "timestamp": INSTANT, "timezone": "Asia/Kathmandu",
                 "utc_offset_minutes": 345}).json()
    assert body["status"] == "ok"
    assert body["local_time"] == "18:41"


# --- 6/7. malformed inputs ---------------------------------------------------
@pytest.mark.parametrize("zone", ["", "Not/AZone", "Mars/Olympus", "12345"])
def test_malformed_timezone_with_a_valid_offset_uses_the_offset(zone):
    body = _ask({"question": "q", "timestamp": INSTANT, "timezone": zone,
                 "utc_offset_minutes": IST_OFFSET}).json()
    assert body["status"] == "ok"
    assert body["local_time"] == "18:26"


@pytest.mark.parametrize("offset", [99999, -99999])
def test_out_of_range_offset_falls_back_to_the_zone(offset):
    body = _ask({"question": "q", "timestamp": INSTANT, "timezone": "Asia/Kolkata",
                 "utc_offset_minutes": offset}).json()
    assert body["status"] == "ok"
    assert body["local_time"] == "18:26", "an unusable offset must be ignored"


@pytest.mark.parametrize("offset", ["abc", 1.5])
def test_wrong_offset_type_is_rejected_or_ignored(offset):
    """A non-integer offset is refused by validation; it is never used as a clock."""
    response = _ask({"question": "q", "timestamp": INSTANT, "timezone": "Asia/Kolkata",
                     "utc_offset_minutes": offset})
    assert response.status_code in (200, 422)
    if response.status_code == 200:
        assert response.json()["local_time"] == "18:26"


def test_malformed_zone_and_no_offset_is_invalid():
    body = _ask({"question": "q", "timestamp": INSTANT, "timezone": "Not/AZone"}).json()
    assert body["status"] == "invalid"


# --- 8. backwards compatibility ---------------------------------------------
def test_missing_offset_keeps_the_existing_behaviour():
    body = _ask({"question": "q", "timestamp": INSTANT, "timezone": "Asia/Kolkata"}).json()
    assert body["status"] == "ok"
    assert body["local_time"] == "18:26"
    assert body["verdict"] == "NO"


def test_missing_offset_and_missing_zone_is_still_invalid():
    assert _ask({"question": "q", "timestamp": INSTANT}).json()["status"] == "invalid"
    assert _ask({"question": "q", "timestamp": "nope", "timezone": "UTC"}).json()["status"] == "invalid"


# --- 9. minute boundary ------------------------------------------------------
def test_minute_boundary_uses_the_exact_minute():
    """12:56:59Z in IST is still 18:26, not 18:27."""
    body = _ask({"question": "q", "timestamp": "2026-09-22T12:56:59+00:00",
                 "timezone": "Asia/Kolkata", "utc_offset_minutes": IST_OFFSET}).json()
    assert body["local_time"] == "18:26"
    assert body["verdict"] == "NO"


# --- 10. a genuine UTC user --------------------------------------------------
def test_a_utc_user_is_evaluated_in_utc():
    body = _ask({"question": "q", "timestamp": INSTANT, "timezone": "UTC",
                 "utc_offset_minutes": 0}).json()
    assert body["status"] == "ok"
    assert body["local_time"] == "12:56", "a real UTC user is not a mismatch"


# --- 11. public response exposes the wall clock only ------------------------
def test_public_response_exposes_local_time_but_no_mechanics():
    body = _ask({"question": "q", "timestamp": INSTANT, "timezone": "Asia/Kolkata",
                 "utc_offset_minutes": IST_OFFSET}).json()

    assert set(body) == {"status", "verdict", "interpretation", "local_time"}
    blob = str(body)
    for banned in ("FRIEND", "ENEMY", "NEUTRAL", "hour_number", "minute_number",
                   "hour_planet", "minute_planet", "relationship", "planet",
                   "Mars", "Saturn", "Jupiter", "Moon"):
        assert banned not in blob, banned


# --- 12/13. diagnostics ------------------------------------------------------
def test_diagnostics_log_the_time_resolution_without_the_question(caplog):
    question = "will my secret business deal work out"
    with caplog.at_level(logging.INFO, logger="kavach.yesno"):
        _ask({"question": question, "timestamp": INSTANT, "timezone": "UTC",
              "utc_offset_minutes": IST_OFFSET})

    log = caplog.text
    assert "yesno_time_resolution" in log
    assert "resolved_local=18:26" in log
    assert "source=offset_fallback" in log
    assert "2026-09-22T12:56:00+00:00" in log, "the submitted instant"
    assert "Asia/Kolkata" not in log and "UTC" in log

    # Never the question, identity, tokens, planets or the interpretation.
    for banned in (question, "secret", "business", "FRIEND", "ENEMY", "NEUTRAL",
                   "Mars", "Saturn", "hour_number", "planet", "Bearer", "token"):
        assert banned not in log, banned


def test_diagnostics_never_leak_the_relationship_or_planets():
    """The logging call carries time fields only."""
    source = (REPO / "backend" / "yesno" / "api.py").read_text(encoding="utf-8")
    call = source.split("logger.info(", 1)[1].split(")\n", 1)[0]
    assert "instant" in call and "resolved_local" in call
    for banned in ("question", "hour_planet", "minute_planet", "relationship",
                   "verdict", "interpretation", "token"):
        assert banned not in call, banned


# --- frontend contract -------------------------------------------------------
def test_frontend_sends_the_offset_with_the_correct_sign():
    ui = (FRONTEND / "components" / "YesNoExperience.tsx").read_text(encoding="utf-8")
    assert "utc_offset_minutes" in ui
    assert "-new Date().getTimezoneOffset()" in ui, "JS sign convention must be inverted"
    assert "Evaluated at {localTime} local time" in ui
    assert "body.local_time" in ui, "the wall clock comes from the backend"


# --- 14. the engine itself is untouched -------------------------------------
def test_engine_and_registry_are_unchanged():
    registry = (REPO / "backend" / "kundli" / "analysis" / "relationships.py").read_text(encoding="utf-8")
    assert '"Mars": (("Moon", "Jupiter", "Venus", "Sun", "Ketu"), ("Mercury", "Rahu", "Saturn"))' in registry
    numbers = (REPO / "backend" / "yesno" / "numbers.py").read_text(encoding="utf-8")
    assert "while number > 9" in numbers and "ZERO_HANDLING = 9" in numbers
    relationships = (REPO / "backend" / "yesno" / "relationships.py").read_text(encoding="utf-8")
    assert "FRIEND: YES" in relationships and "ENEMY: NO" in relationships
    # The offset is a time source only: it never reaches the engine's inputs.
    api = (REPO / "backend" / "yesno" / "api.py").read_text(encoding="utf-8")
    assert "evaluate_yes_no(payload.question, local" in api
    engine = (REPO / "backend" / "yesno" / "engine.py").read_text(encoding="utf-8")
    assert "utc_offset" not in engine


def test_zone_offset_helper_matches_the_zone():
    from datetime import datetime

    instant = datetime.fromisoformat(INSTANT)
    assert zone_offset_minutes(instant, "Asia/Kolkata") == 330
    assert zone_offset_minutes(instant, "Europe/London") == 60
    assert zone_offset_minutes(instant, "America/New_York") == -240
    assert zone_offset_minutes(instant, "Not/AZone") is None
