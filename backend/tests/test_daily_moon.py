"""Tests for the Daily Moon day-quality signal (transit-based, no natal data)."""

from __future__ import annotations

import inspect
from datetime import date

import pytest

from panchang import PanchangRequest, compute_panchang
from prediction.panchang_natal import selectors
from prediction.panchang_natal.daily_moon import (
    CHART_REFERENCE_STATUS,
    DEFAULT_CHART_REFERENCE,
    EXTRA_CARE_HOUSES,
    SUPPORTIVE_HOUSES,
    classify_house,
    compute_daily_moon_signal,
)

DELHI = (28.6139, 77.2090, "Asia/Kolkata", "New Delhi")
TEST_DATE = date(2026, 9, 20)


@pytest.fixture(scope="module")
def signal():
    return compute_daily_moon_signal(TEST_DATE, *DELHI)


def test_birth_details_are_not_required():
    parameters = inspect.signature(compute_daily_moon_signal).parameters
    for forbidden in ("birth_date", "birth_time", "birth_place", "natal", "chart"):
        assert forbidden not in parameters, f"{forbidden} must not be a parameter"
    assert "on_date" in parameters and "latitude" in parameters


def test_moon_rashi_consumed_from_production_panchang(signal):
    produced = compute_panchang(
        PanchangRequest(on_date=TEST_DATE, latitude=DELHI[0], longitude=DELHI[1],
                        timezone_name=DELHI[2], label=DELHI[3])
    )
    assert signal["moon"]["rashi"] == produced["sun_moon_rashi"]["moon"]["name"]
    assert signal["moon"]["rashi"] == "Dhanu"


def test_moon_nakshatra_and_pada_consumed_from_production_panchang(signal):
    produced = compute_panchang(
        PanchangRequest(on_date=TEST_DATE, latitude=DELHI[0], longitude=DELHI[1],
                        timezone_name=DELHI[2], label=DELHI[3])
    )
    nakshatra = produced["panchanga"]["nakshatra"]
    assert signal["moon"]["nakshatra"] == nakshatra["name"]
    assert signal["moon"]["pada"] == nakshatra["pada"]


def test_nakshatra_lord_selected(signal):
    assert signal["moon"]["nakshatra"] == "Purva Ashadha"
    assert signal["moon"]["nakshatra_lord"] == "Venus"
    assert signal["daily_chart"]["nakshatra_lord"] == "Venus"


def test_lord_located_in_todays_chart_not_natal(signal):
    produced = compute_panchang(
        PanchangRequest(on_date=TEST_DATE, latitude=DELHI[0], longitude=DELHI[1],
                        timezone_name=DELHI[2], label=DELHI[3])
    )
    today_positions = {p["planet"]: p for p in produced["d1"]["positions"]}
    lord = signal["daily_chart"]["nakshatra_lord"]
    assert signal["daily_chart"]["lord_house"] == today_positions[lord]["house"]
    assert signal["daily_chart"]["lord_rashi"] == today_positions[lord]["sign"]


@pytest.mark.parametrize("house", [6, 8, 12])
def test_extra_care_houses(house):
    assert house in EXTRA_CARE_HOUSES
    assert classify_house(house) == "extra_care"


@pytest.mark.parametrize("house", [1, 2, 3, 4, 5, 7, 9, 10, 11])
def test_supportive_houses(house):
    assert house in SUPPORTIVE_HOUSES
    assert classify_house(house) == "supportive"


def test_same_planet_house_change_flips_classification():
    assert classify_house(2) == "supportive"
    assert classify_house(8) == "extra_care"


def test_all_27_nakshatras_resolve_via_shared_selector():
    canonical = [
        "Ashvini","Bharani","Krittika","Rohini","Mrigashira","Ardra","Punarvasu",
        "Pushya","Ashlesha","Magha","Purva Phalguni","Uttara Phalguni","Hasta",
        "Chitra","Swati","Vishakha","Anuradha","Jyeshtha","Mula","Purva Ashadha",
        "Uttara Ashadha","Shravana","Dhanishta","Shatabhisha","Purva Bhadrapada",
        "Uttara Bhadrapada","Revati",
    ]
    assert len(canonical) == 27
    for name in canonical:
        assert selectors.nakshatra_lord(name) is not None
    assert selectors.nakshatra_lord("Purva Ashadha") == "Venus"
    assert selectors.nakshatra_lord("Ashvini") == "Ketu"
    assert selectors.nakshatra_lord("Revati") == "Mercury"


def test_changing_location_or_date_recomputes():
    delhi = compute_daily_moon_signal(TEST_DATE, *DELHI)
    london = compute_daily_moon_signal(date(2026, 9, 20), 51.5074, -0.1278, "Europe/London", "London")
    assert delhi["date"] == london["date"]
    assert delhi["location"]["label"] != london["location"]["label"]
    assert delhi["daily_chart"]["reference_time"] != london["daily_chart"]["reference_time"]
    # Nakshatra is global, but the chart used for the house lookup is local.
    assert london["moon"]["nakshatra"] == delhi["moon"]["nakshatra"]


def test_chart_reference_is_explicit_and_flagged(signal):
    assert signal["daily_chart"]["reference"] == DEFAULT_CHART_REFERENCE
    assert "AWAITING ASTROLOGER CONFIRMATION" in signal["daily_chart"]["reference_status"]
    assert signal["daily_chart"]["reference_status"] == CHART_REFERENCE_STATUS
    assert signal["daily_chart"]["reference_time"]


def test_unsupported_chart_reference_rejected():
    with pytest.raises(ValueError):
        compute_daily_moon_signal(TEST_DATE, *DELHI, daily_chart_reference="noon")


def test_result_is_general_not_personalized(signal):
    assert signal["birth_details_required"] is False
    blob = str(signal).lower()
    for forbidden in ("exalted", "debilitated", "score", "probability", "will happen"):
        assert forbidden not in blob
