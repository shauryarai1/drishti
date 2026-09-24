"""Deterministic tests for the Nakshatra-lord Daily rulership engine."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from daily.config import HOUSE_PATTERNS
from daily.engine import RASHIS, build_daily_prediction
from daily.rulership import (
    active_houses,
    active_houses_for_nakshatra,
    nakshatra_lord,
    ruled_rashis,
    whole_sign_house,
)


@pytest.mark.parametrize("native,ruled,house", [
    ("Aries", "Aries", 1),
    ("Aries", "Scorpio", 8),
    ("Taurus", "Aries", 12),
    ("Pisces", "Aquarius", 12),
    ("Pisces", "Aries", 2),
])
def test_whole_sign_house_distance(native, ruled, house):
    assert whole_sign_house(native, ruled) == house


@pytest.mark.parametrize("nakshatra,lord", [
    ("Krittika", "Sun"),
    ("Rohini", "Moon"),
    ("Dhanishta", "Mars"),
    ("Revati", "Mercury"),
    ("Punarvasu", "Jupiter"),
    ("Bharani", "Venus"),
    ("Pushya", "Saturn"),
])
def test_repository_nakshatra_to_lord_mapping(nakshatra, lord):
    assert nakshatra_lord(nakshatra) == lord


def test_owner_supplied_dhanishtha_spelling_uses_repository_mapping():
    assert nakshatra_lord("Dhanishtha") == "Mars"


def test_lord_to_ruled_rashis_uses_approved_registry():
    assert ruled_rashis("Sun") == ("Leo",)
    assert ruled_rashis("Moon") == ("Cancer",)
    assert ruled_rashis("Mars") == ("Aries", "Scorpio")
    assert ruled_rashis("Mercury") == ("Gemini", "Virgo")
    assert ruled_rashis("Jupiter") == ("Sagittarius", "Pisces")
    assert ruled_rashis("Venus") == ("Taurus", "Libra")
    assert ruled_rashis("Saturn") == ("Capricorn", "Aquarius")


def test_single_ruler_produces_exactly_one_active_house():
    assert active_houses_for_nakshatra("Aries", "Krittika") == (5,)
    assert active_houses_for_nakshatra("Aries", "Rohini") == (4,)


def test_dual_ruler_produces_exactly_two_active_houses():
    assert active_houses_for_nakshatra("Aries", "Dhanishta") == (1, 8)
    assert active_houses("Libra", ruled_rashis("Venus")) == (8, 1)


DHANISHTHA = {
    "Aries": (1, 8),
    "Taurus": (12, 7),
    "Gemini": (11, 6),
    "Cancer": (10, 5),
    "Leo": (9, 4),
    "Virgo": (8, 3),
    "Libra": (7, 2),
    "Scorpio": (6, 1),
    "Sagittarius": (5, 12),
    "Capricorn": (4, 11),
    "Aquarius": (3, 10),
    "Pisces": (2, 9),
}


def test_dhanishtha_all_twelve_signs():
    assert set(DHANISHTHA) == set(RASHIS)
    for sign, expected in DHANISHTHA.items():
        assert active_houses_for_nakshatra(sign, "Dhanishtha") == expected


def test_nodes_use_owner_daily_rulership():
    # Owner Daily rule (authorized): Rahu -> Aquarius, Ketu -> Scorpio.
    # The nodes remain absent from jyotish.planets.RULERSHIP (see
    # test_jyotish_channels); this registry lives only in daily.rulership.
    assert ruled_rashis("Rahu") == ("Aquarius",)
    assert ruled_rashis("Ketu") == ("Scorpio",)
    assert active_houses_for_nakshatra("Aries", "Shatabhisha") == (11,)
    assert active_houses_for_nakshatra("Aries", "Mula") == (8,)


def test_final_daily_response_uses_new_active_house_engine():
    fake_daily = {
        "date": "2026-09-24",
        "sunrise": "2026-09-24T06:12:00+05:30",
        "sunriseLocal": "06:12",
        "longitude": 300.0,  # Dhanishtha
        "rashi": "Aquarius",
    }
    fake_current = {"rashi": "Aquarius", "longitude": 300.0,
                    "asOf": "2026-09-24T12:00:00+05:30"}
    with patch("daily.engine.get_daily_moon_rashi", return_value=fake_daily), patch(
        "daily.engine.get_current_moon_rashi", return_value=fake_current
    ):
        result = build_daily_prediction({"latitude": 0, "longitude": 0, "date": "2026-09-24"})

    assert result["basis"] == "transit_moon_nakshatra_lord_ruled_rashis_whole_sign_from_native_moon"
    assert result["nakshatra"] == {
        "name": "Dhanishta",
        "lord": "Mars",
        "ruledRashis": ["Aries", "Scorpio"],
        "mode": "",
        "navtara": "",
        "navtaraTone": {},
    }
    for card in result["signs"]:
        expected = DHANISHTHA[card["sign"]]
        assert tuple(card["activeHouses"]) == expected
        assert card["pattern"]
        assert " + " not in card["pattern"]
        for house in expected:
            assert str(HOUSE_PATTERNS[house]["theme"]).lower() in card["pattern"].lower()
