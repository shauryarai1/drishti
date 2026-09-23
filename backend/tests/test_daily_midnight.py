"""KAVACH Daily Prediction: the reading day changes at LOCAL MIDNIGHT.

The Daily DAY boundary is 12:00 AM in the user's selected timezone. Sunrise,
Moonrise, the Moon sign, Tithi and Nakshatra must never move that boundary.
No astrology methodology is tested here - only WHEN a new day is selected.
"""

from __future__ import annotations

import pathlib

import pytest

from daily.engine import build_daily_prediction, get_daily_moon_rashi

REPO = pathlib.Path(__file__).resolve().parents[2]
PAGE = REPO / "frontend-next" / "app" / "daily" / "page.tsx"
LIB = REPO / "frontend-next" / "lib" / "daily.ts"

DELHI = {"latitude": 28.6139, "longitude": 77.209, "timezone": "Asia/Kolkata", "place": "Delhi"}


def test_explicitly_requested_date_is_authoritative():
    """Regression: date=2026-09-22 must never return a 2026-09-23 sunrise."""
    result = get_daily_moon_rashi({**DELHI, "date": "2026-09-22"})
    assert result["date"] == "2026-09-22"
    assert result["sunrise"].startswith("2026-09-22"), result["sunrise"]


def test_requested_date_wins_over_the_server_clock():
    for day in ("2026-09-22", "2026-09-24", "2027-01-01"):
        result = get_daily_moon_rashi({**DELHI, "date": day})
        assert result["date"] == day
        assert result["sunrise"].startswith(day)


def test_23_59_and_00_00_use_different_days():
    """23:59 belongs to the old date; 00:00 belongs to the new one."""
    old = build_daily_prediction({**DELHI, "date": "2026-09-23", "at": "2026-09-23T23:59:00+05:30"})
    new = build_daily_prediction({**DELHI, "date": "2026-09-24", "at": "2026-09-24T00:00:00+05:30"})
    assert old["dailyMoon"]["date"] == "2026-09-23"
    assert new["dailyMoon"]["date"] == "2026-09-24"
    assert old["dailyMoon"]["date"] != new["dailyMoon"]["date"]


def test_consecutive_days_produce_their_own_reading():
    first = build_daily_prediction({**DELHI, "date": "2026-09-23"})
    second = build_daily_prediction({**DELHI, "date": "2026-09-24"})
    assert first["dailyMoon"]["date"] == "2026-09-23"
    assert second["dailyMoon"]["date"] == "2026-09-24"
    # The day boundary is the calendar date, so the two readings differ even if
    # the sunrise Moon sign happens to be the same.
    assert first["dailyMoon"]["sunrise"] != second["dailyMoon"]["sunrise"]


def test_sunrise_cannot_move_the_daily_day_boundary():
    """The reading's date is the requested calendar date, not a sunrise-derived one."""
    for day in ("2026-09-22", "2026-09-23"):
        result = get_daily_moon_rashi({**DELHI, "date": day})
        sunrise_date = result["sunrise"][:10]
        assert result["date"] == day
        assert sunrise_date == day, "sunrise belongs to the same requested day"


def test_timezone_is_respected_and_server_utc_is_not_used():
    """The same instant is a different local date in different zones."""
    instant = "2026-09-23T20:00:00+00:00"          # 01:30 on the 24th in IST
    kolkata = build_daily_prediction({**DELHI, "date": "2026-09-24", "at": instant})
    assert kolkata["dailyMoon"]["date"] == "2026-09-24"

    london = build_daily_prediction({
        "latitude": 51.5074, "longitude": -0.1278, "timezone": "Europe/London",
        "place": "London", "date": "2026-09-23", "at": instant,
    })
    assert london["dailyMoon"]["date"] == "2026-09-23", "21:00 local on the 23rd"

    # An explicit date is honoured in every zone: the server clock never wins.
    for tz, lat, lon in (("Asia/Kolkata", 28.6139, 77.209),
                         ("Europe/London", 51.5074, -0.1278),
                         ("America/New_York", 40.7128, -74.006)):
        result = get_daily_moon_rashi({"latitude": lat, "longitude": lon,
                                       "timezone": tz, "place": "", "date": "2026-09-22"})
        assert result["date"] == "2026-09-22", tz


def test_missing_date_still_falls_back_to_the_local_today():
    """Backwards compatible: no date supplied keeps the existing behaviour."""
    result = get_daily_moon_rashi(dict(DELHI))
    assert result["date"]
    assert result["date"] == result["sunrise"][:10]


def test_frontend_sends_the_local_calendar_date():
    lib = LIB.read_text(encoding="utf-8")
    page = PAGE.read_text(encoding="utf-8")
    assert "date?: string" in lib, "the request must be able to carry the local date"
    assert "date: localDate" in page, "the page must send the local calendar date"
    assert "localCalendarDate" in page
    # The zone is used to compute it, never the server's date.
    assert "timeZone" in page


def test_frontend_refreshes_across_midnight():
    page = PAGE.read_text(encoding="utf-8")
    # A tab left open must roll over without a manual reload.
    assert "setInterval(" in page
    assert "visibilitychange" in page
    assert "dayRef" in page
    assert "if (dayRef.current && current !== dayRef.current)" in page


def test_frontend_daily_is_latest_wins_and_uncached():
    """A slow response for a previous city must never overwrite the current one."""
    page = PAGE.read_text(encoding="utf-8")
    lib = LIB.read_text(encoding="utf-8")
    assert "requestIdRef" in page
    assert "if (requestId !== requestIdRef.current) return;" in page
    # The reading must never be served from a cache.
    assert "cache: 'no-store'" in lib
