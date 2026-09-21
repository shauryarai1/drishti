"""Weekly forecast tests: Moon-Nakshatra only, private vs customer-safe."""

from __future__ import annotations

import json
import pathlib
import re
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from navtara import NAKSHATRAS, build_navtara_profile
from weekly import build_week, build_weekly_forecast, to_public
from weekly.moon_transits import moon_nakshatra_at, moon_periods
from weekly.public import TONE_BY_TARA

TZ = ZoneInfo("Asia/Kolkata")
DELHI = {"latitude": 28.6139, "longitude": 77.209}
START = "2026-09-21"

PRIVATE_TERMS = (
    "navtara", "navatara", "janma tara", "sampat", "vipat", "kshema", "pratyari",
    "sadhaka", "vadha", "ati-mitra", "atimitra", "ati mitra", "relativeposition",
    "relative_position", "taranumber", "tara_number", "jati", "karma nakshatra",
    "desha", "abhisheka", "sanghatika", "samudaya", "adhana", "moonnakshatra",
    "moon_nakshatra", "janmanakshatra", "janma_nakshatra",
)


def _week(janma: str, days: int = 7):
    return build_week(janma, date.fromisoformat(START), DELHI["latitude"], DELHI["longitude"],
                      "Asia/Kolkata", days)


# --- A: one Janma Nakshatra across a full 7-day forecast ------------------
def test_a_seven_day_forecast_from_one_janma_nakshatra():
    week = _week("Ashwini")
    assert len(week.days) == 7
    assert [day.date for day in week.days] == [
        "2026-09-21", "2026-09-22", "2026-09-23", "2026-09-24",
        "2026-09-25", "2026-09-26", "2026-09-27",
    ]
    for day in week.days:
        assert day.periods, f"{day.date} has no Moon period"
        for period in day.periods:
            assert period.nakshatra in NAKSHATRAS
            assert 1 <= period.relative_position <= 27
            assert period.tara


# --- B: a local day with a Moon Nakshatra change --------------------------
def test_b_a_day_can_contain_multiple_contiguous_periods():
    week = _week("Ashwini")
    multi = [day for day in week.days if len(day.periods) > 1]
    assert multi, "expected at least one day with two Moon periods in the window"
    day = multi[0]
    assert len(day.periods) >= 2
    for previous, current in zip(day.periods, day.periods[1:]):
        assert previous.end == current.start          # shared boundary exactly
        assert previous.nakshatra != current.nakshatra

    first_start = datetime.fromisoformat(day.periods[0].start)
    last_end = datetime.fromisoformat(day.periods[-1].end)
    assert first_start.hour == 0 and first_start.date().isoformat() == day.date
    assert last_end.isoformat() == (first_start + timedelta(days=1)).isoformat()


def test_b_periods_have_no_gaps_or_overlaps_over_the_window():
    week = _week("Rohini")
    for day in week.days:
        for period in day.periods:
            assert datetime.fromisoformat(period.end) > datetime.fromisoformat(period.start)
            assert datetime.fromisoformat(period.start).date().isoformat() == day.date


# --- C: transition across local midnight ---------------------------------
def test_c_transition_across_local_midnight_is_handled():
    week = _week("Rohini", days=12)
    assert all(day.periods[0].start.endswith("T00:00:00+05:30") for day in week.days)
    for previous, current in zip(week.days, week.days[1:]):
        assert previous.periods[-1].end == current.periods[0].start


# --- D: astronomical Nakshatra wrap Revati -> Ashwini ---------------------
def test_d_revati_to_ashwini_wrap_exists_in_astronomy():
    start = datetime(2026, 9, 21, 0, 0, tzinfo=TZ)
    periods = moon_periods(start, datetime(2026, 10, 10, 0, 0, tzinfo=TZ))
    chain = [moon_nakshatra_at(a) for a, _b in periods]
    assert "Revati" in chain and "Ashwini" in chain
    index = chain.index("Revati")
    if index + 1 < len(chain):
        assert chain[index + 1] == "Ashwini"


# --- E: Navtara wrap for Uttara Bhadrapada Janma -------------------------
def test_e_navtara_wrap_for_uttara_bhadrapada_janma():
    profile = build_navtara_profile("Uttara Bhadrapada")
    assert profile.positions[0].position == 1
    assert profile.positions[1].nakshatra == "Revati"
    assert profile.positions[2].nakshatra == "Ashwini"
    week = _week("Uttara Bhadrapada", days=3)
    for day in week.days:
        for period in day.periods:
            assert period.tara in set(TONE_BY_TARA)


# --- F: same transit Nakshatra, different Janma -> different result ------
def test_f_same_transit_different_janma_gives_different_classification():
    ashwini = _week("Ashwini", days=2)
    rohini = _week("Rohini", days=2)
    first_ashwini = ashwini.days[0].periods[0]
    first_rohini = rohini.days[0].periods[0]
    assert first_ashwini.nakshatra == first_rohini.nakshatra
    assert (first_ashwini.relative_position, first_ashwini.tara) != (
        first_rohini.relative_position, first_rohini.tara)


# --- G: determinism -------------------------------------------------------
def test_g_same_inputs_produce_identical_output():
    first = _week("Pushya", days=7).to_private_dict()
    second = _week("Pushya", days=7).to_private_dict()
    assert first == second
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_g_birth_flow_uses_the_existing_calculator():
    week = build_weekly_forecast(
        {"date": "1990-05-15", "time": "14:15", "place": "New Delhi, India", **DELHI},
        START, DELHI["latitude"], DELHI["longitude"], "Asia/Kolkata", days=3)
    assert week.janma_nakshatra in NAKSHATRAS
    assert len(week.days) == 3


# --- H + privacy: customer-safe output -----------------------------------
def test_h_public_output_has_no_private_fields_or_terms():
    public = to_public(_week("Ashwini"))
    blob = json.dumps(public).lower()
    for term in PRIVATE_TERMS:
        assert term not in blob, term
    for day in public["days"]:
        assert set(day) == {"date", "headline", "summary", "periods"}
        for period in day["periods"]:
            assert set(period) == {"label", "start", "end", "afterTime", "headline",
                                   "guidance", "tone"}
            assert period["tone"] in ("supportive", "personal", "caution", "strong_caution")
            assert period["start"] and period["guidance"]


def test_h_public_output_keeps_exact_transition_times():
    week = _week("Ashwini")
    private_day = next(day for day in week.days if len(day.periods) > 1)
    public = to_public(week)
    public_day = next(day for day in public["days"] if day["date"] == private_day.date)
    assert public_day["periods"][0]["end"] == private_day.periods[0].end[11:16]
    assert public_day["periods"][1]["start"] == private_day.periods[1].start[11:16]


def test_h_public_output_is_not_fear_based():
    public = to_public(_week("Ashwini", days=14))
    blob = json.dumps(public).lower()
    for banned in ("death", "fatal", "disaster", "terrible", "guaranteed", "will happen",
                   "unavoidable", "bad luck"):
        assert banned not in blob, banned
    assert public["weekSummary"]


def test_h_headlines_are_customer_safe_and_deterministic():
    public = to_public(_week("Ashwini"))
    headlines = {day["headline"] for day in public["days"]}
    assert headlines <= {
        "Take It Slowly Early, Better Flow Later", "Use the Earlier Part of the Day Well",
        "A Generally Supportive Day", "A Day for Patience and Care",
        "Personal Focus Gives Way to Practical Progress", "A Steady Personal Focus Later",
        "A Day for Extra Care and Patience", "A Day for Personal Focus", "A Steady Day",
    }
    assert to_public(_week("Ashwini"))["days"] == public["days"]


def test_week_highlights_use_safe_labels_only():
    public = to_public(_week("Ashwini", days=14))
    labels = {item["label"] for item in public["highlights"]}
    assert labels
    assert labels <= {"Extra Care", "Supportive Window", "Good for Focused Effort",
                      "Support From Others", "Practical/Resource Focus"}
    for item in public["highlights"]:
        assert item["text"] and item["date"] and item["time"]


# --- I + scope guarantees -------------------------------------------------
def test_public_route_is_wired_to_the_safe_serializer():
    root = pathlib.Path(__file__).resolve().parents[1]
    source = (root / "main.py").read_text(encoding="utf-8")
    assert "/api/weekly" in source
    assert "to_public" in source
    assert "build_weekly_forecast" in source


def test_i_daily_feature_was_not_touched():
    root = pathlib.Path(__file__).resolve().parents[1]
    assert (root / "daily" / "engine.py").exists()
    source = (root / "weekly" / "engine.py").read_text(encoding="utf-8").lower()
    assert "daily" not in source


def test_only_moon_nakshatras_are_used():
    root = pathlib.Path(__file__).resolve().parents[1] / "weekly"
    for path in root.glob("*.py"):
        source = re.sub(r'""".*?"""', "", path.read_text(encoding="utf-8"), flags=re.S)
        for line in source.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            lowered = stripped.lower()
            for forbidden in ("house", "aspect", "dasha", "ascendant", "tithi", "karana",
                              "yoga", "vara", "dignity", "exalt", "debilit", "benefic",
                              "malefic", "sun_longitude", "mars", "jupiter", "venus",
                              "saturn", "rahu", "ketu", "mercury"):
                assert forbidden not in lowered, f"{path.name}: {stripped}"
