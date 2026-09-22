"""KAVACH YES / NO: the engine runs on the user's exact LOCAL time.

The same UTC instant must produce different planetary numbers in different
timezones, and India must never be assumed.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from yesno import evaluate_yes_no, resolve_local_datetime, resolve_timezone
from yesno.timezone import local_datetime_for

# 2026-09-22: Kolkata is UTC+5:30, London is BST (UTC+1), New York is EDT (UTC-4).
INSTANT = datetime(2026, 9, 22, 10, 23, tzinfo=timezone.utc)

DELHI = (28.6139, 77.209)
LONDON = (51.5074, -0.1278)
NEW_YORK = (40.7128, -74.006)


def test_same_instant_different_local_times():
    kolkata = resolve_local_datetime(INSTANT, timezone_name="Asia/Kolkata")
    london = resolve_local_datetime(INSTANT, timezone_name="Europe/London")
    new_york = resolve_local_datetime(INSTANT, timezone_name="America/New_York")

    assert (kolkata.hour, kolkata.minute) == (15, 53)
    assert (london.hour, london.minute) == (11, 23)
    assert (new_york.hour, new_york.minute) == (6, 23)


def test_same_instant_produces_different_numbers_and_planets():
    kolkata = evaluate_yes_no("Will it work?", resolve_local_datetime(INSTANT, timezone_name="Asia/Kolkata"))
    london = evaluate_yes_no("Will it work?", resolve_local_datetime(INSTANT, timezone_name="Europe/London"))
    new_york = evaluate_yes_no("Will it work?", resolve_local_datetime(INSTANT, timezone_name="America/New_York"))

    assert kolkata.local_time == "15:53"
    assert london.local_time == "11:23"
    assert new_york.local_time == "06:23"

    assert (kolkata.hour_number, kolkata.minute_number) == (6, 8)   # Venus + Saturn
    assert (london.hour_number, london.minute_number) == (2, 5)     # Moon + Mercury
    assert (new_york.hour_number, new_york.minute_number) == (6, 5)  # Venus + Mercury
    assert kolkata.hour_number != london.hour_number


@pytest.mark.parametrize("coordinates,zone", [
    (DELHI, "Asia/Kolkata"),
    (LONDON, "Europe/London"),
    (NEW_YORK, "America/New_York"),
])
def test_coordinates_resolve_through_the_authoritative_source(coordinates, zone):
    assert resolve_timezone(*coordinates) == zone


def test_coordinates_are_used_for_the_calculation():
    kolkata = evaluate_yes_no("Will it work?", resolve_local_datetime(INSTANT, *DELHI))
    new_york = evaluate_yes_no("Will it work?", resolve_local_datetime(INSTANT, *NEW_YORK))

    assert kolkata.local_time == "15:53"
    assert new_york.local_time == "06:23"


def test_india_is_never_assumed():
    assert resolve_timezone(*NEW_YORK) != "Asia/Kolkata"
    new_york = resolve_local_datetime(INSTANT, *NEW_YORK)
    assert new_york.hour == 6, "New York must not be treated as Indian time"


def test_explicit_timezone_is_only_a_fallback():
    # Coordinates win over the supplied timezone when both are present.
    resolved = resolve_local_datetime(INSTANT, latitude=NEW_YORK[0], longitude=NEW_YORK[1],
                                      timezone_name="Asia/Kolkata")
    assert resolved.hour == 6


def test_naive_local_time_is_attached_without_shifting():
    naive = datetime(2026, 9, 22, 15, 53)
    resolved = resolve_local_datetime(naive, timezone_name="Asia/Kolkata")

    assert (resolved.hour, resolved.minute) == (15, 53)
    assert resolved.tzinfo is not None
    assert evaluate_yes_no("Will it work?", resolved).local_time == "15:53"


def test_missing_timezone_is_an_error_not_a_default():
    with pytest.raises(ValueError):
        resolve_local_datetime(INSTANT)
    assert resolve_timezone() is None, "no zone is available, and none is assumed"


def test_aware_instant_requires_a_zone_for_direct_conversion():
    with pytest.raises(ValueError):
        local_datetime_for(datetime(2026, 9, 22, 10, 23), "Asia/Kolkata")
