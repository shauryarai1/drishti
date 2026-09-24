"""Owner-authorized Daily node rule: Rahu -> Aquarius, Ketu -> Scorpio (PRIMARY),
plus the node's actual mean-node transit Rashi as SECONDARY house.

Deterministic: production astronomy/ephemeris only, no network, no AI.
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import patch

import pytest

from calculator import _sign_from_longitude, calc_planet_longitudes
from daily.config import HOUSE_PATTERNS, status
from daily.engine import build_daily_prediction, get_daily_moon_rashi
from daily.rulership import (
    DAILY_NODE_RULERSHIP,
    active_houses_for_nakshatra,
    nakshatra_lord,
    ruled_rashis,
    whole_sign_house,
)
from jyotish.planets import RULERSHIP
from kundli.analysis.signs import RASHIS
from panchang import astronomy

DELHI = {"latitude": 28.6139, "longitude": 77.209, "timezone": "Asia/Kolkata"}

RAHU_NAKSHATRAS = ("Ardra", "Swati", "Shatabhisha")
KETU_NAKSHATRAS = ("Ashvini", "Magha", "Mula")


# --- 1. owner rule + isolation from the classical registry ----------------
def test_owner_node_rulership_registry():
    assert DAILY_NODE_RULERSHIP == {"Rahu": ("Aquarius",), "Ketu": ("Scorpio",)}
    assert ruled_rashis("Rahu") == ("Aquarius",)
    assert ruled_rashis("Ketu") == ("Scorpio",)


def test_node_rule_is_daily_only_not_classical_rulership():
    assert "Rahu" not in RULERSHIP
    assert "Ketu" not in RULERSHIP


@pytest.mark.parametrize("nakshatra,lord", [
    ("Ardra", "Rahu"), ("Swati", "Rahu"), ("Shatabhisha", "Rahu"),
    ("Ashvini", "Ketu"), ("Magha", "Ketu"), ("Mula", "Ketu"),
])
def test_node_nakshatras_map_to_their_lord(nakshatra, lord):
    assert nakshatra_lord(nakshatra) == lord


# --- 2. both 12-sign PRIMARY tables (computed, not hardcoded) --------------
@pytest.mark.parametrize("sign", RASHIS)
def test_rahu_primary_table_all_twelve_signs(sign):
    expected = whole_sign_house(sign, "Aquarius")
    for nakshatra in RAHU_NAKSHATRAS:
        assert active_houses_for_nakshatra(sign, nakshatra) == (expected,)


@pytest.mark.parametrize("sign", RASHIS)
def test_ketu_primary_table_all_twelve_signs(sign):
    expected = whole_sign_house(sign, "Scorpio")
    for nakshatra in KETU_NAKSHATRAS:
        assert active_houses_for_nakshatra(sign, nakshatra) == (expected,)


def test_primary_tables_boundary_values():
    # Rahu/Aquarius: Aries 11 ... Aquarius 1, Pisces 12.
    assert whole_sign_house("Aries", "Aquarius") == 11
    assert whole_sign_house("Aquarius", "Aquarius") == 1
    assert whole_sign_house("Pisces", "Aquarius") == 12
    # Ketu/Scorpio: Aries 8 ... Scorpio 1, Sagittarius 12.
    assert whole_sign_house("Aries", "Scorpio") == 8
    assert whole_sign_house("Scorpio", "Scorpio") == 1
    assert whole_sign_house("Sagittarius", "Scorpio") == 12


# --- helpers ---------------------------------------------------------------
def _build(date: str):
    return build_daily_prediction({**DELHI, "date": date})


def _independent_node_rashi(date: str, lord: str) -> str:
    """Same production ephemeris, computed independently of the engine."""
    sunrise = datetime.fromisoformat(get_daily_moon_rashi({**DELHI, "date": date})["sunrise"])
    longitude = calc_planet_longitudes(astronomy.to_jd(sunrise))[lord]
    sign, _i, _d = _sign_from_longitude(longitude)
    return sign


# --- 3/4/6. full engine on node days --------------------------------------
def test_node_days_build_all_twelve_cards_without_error():
    for date in ("2026-09-25", "2026-10-03", "2026-10-07", "2026-10-12", "2026-10-17"):
        result = _build(date)
        assert result["status"] == "ok"
        assert len(result["signs"]) == 12
        assert result["nakshatra"]["lord"] in ("Rahu", "Ketu")
        assert "nodeTransit" in result["nakshatra"]


def test_shatabhisha_day_is_rahu_in_aquarius():
    result = _build("2026-09-25")
    assert result["nakshatra"]["name"] == "Shatabhisha"
    assert result["nakshatra"]["lord"] == "Rahu"
    assert result["nakshatra"]["nodeTransit"] == {"lord": "Rahu", "rashi": "Aquarius"}
    for card in result["signs"]:
        primary = whole_sign_house(card["sign"], "Aquarius")
        assert card["primaryHouse"] == primary
        # Rahu transits Aquarius itself: secondary equals primary on this day.
        assert card["secondaryHouse"] == primary
        assert card["activeHouses"] == [primary]


def test_magha_day_ketu_transit_leo_is_secondary():
    result = _build("2026-10-07")
    assert result["nakshatra"]["name"] == "Magha"
    assert result["nakshatra"]["lord"] == "Ketu"
    assert result["nakshatra"]["nodeTransit"] == {"lord": "Ketu", "rashi": "Leo"}
    aries = next(c for c in result["signs"] if c["sign"] == "Aries")
    assert aries["primaryHouse"] == whole_sign_house("Aries", "Scorpio") == 8
    assert aries["secondaryHouse"] == whole_sign_house("Aries", "Leo") == 5
    assert aries["activeHouses"] == [8, 5]


def test_secondary_house_comes_from_actual_mean_node_transit():
    date, lord = "2026-12-06", "Rahu"
    independent = _independent_node_rashi(date, lord)
    assert independent == "Capricorn"  # verified ephemeris fixture
    result = _build(date)
    assert result["nakshatra"]["name"] == "Swati"
    assert result["nakshatra"]["nodeTransit"]["rashi"] == independent
    for card in result["signs"]:
        assert card["primaryHouse"] == whole_sign_house(card["sign"], "Aquarius")
        assert card["secondaryHouse"] == whole_sign_house(card["sign"], independent)
    aries = next(c for c in result["signs"] if c["sign"] == "Aries")
    assert aries["primaryHouse"] == 11
    assert aries["secondaryHouse"] == 10
    assert aries["primaryHouse"] != aries["secondaryHouse"]


def test_primary_leads_rendering_and_categories():
    result = _build("2026-12-06")  # Rahu: primary Aquarius, secondary Capricorn
    for card in result["signs"]:
        primary, secondary = card["primaryHouse"], card["secondaryHouse"]
        pattern = card["pattern"].lower()
        primary_theme = str(HOUSE_PATTERNS[primary]["theme"]).lower()
        secondary_theme = str(HOUSE_PATTERNS[secondary]["theme"]).lower()
        assert primary_theme in pattern
        assert pattern.index(primary_theme) <= pattern.index(secondary_theme)
        for category in ("love", "health", "career"):
            assert card["categories"][category]["status"] == status(primary, category)[0]
            assert card["categories"][category]["reason"]


def test_equal_secondary_renders_single_house_form():
    result = _build("2026-09-25")  # Rahu in Aquarius == primary sign
    for card in result["signs"]:
        assert card["secondaryHouse"] == card["primaryHouse"]
        assert card["activeHouses"] == [card["primaryHouse"]]
        assert "secondary" not in card["pattern"].lower()
        assert " + " not in card["pattern"]


def test_node_days_never_raise_unsupported_lord():
    from daily.rulership import UnsupportedNakshatraLordError

    for date in ("2026-09-25", "2026-10-07"):
        try:
            _build(date)
        except UnsupportedNakshatraLordError:  # pragma: no cover
            pytest.fail(f"node day {date} raised UnsupportedNakshatraLordError")


def test_node_day_basis_is_explicit():
    assert _build("2026-09-25")["basis"] == (
        "transit_moon_nakshatra_node_rulership_primary_with_mean_node_transit_secondary"
    )


# --- 5/9/12. classical path unchanged: no node transit consulted -----------
def test_classical_day_needs_no_node_transit():
    with patch(
        "daily.engine._node_transit_rashi",
        side_effect=AssertionError("node transit must not run on classical days"),
    ):
        result = _build("2026-09-24")  # Dhanishta / Mars
    assert result["nakshatra"]["lord"] == "Mars"
    assert "nodeTransit" not in result["nakshatra"]
    assert result["basis"] == "transit_moon_nakshatra_lord_ruled_rashis_whole_sign_from_native_moon"
    for card in result["signs"]:
        assert "primaryHouse" not in card
        assert "secondaryHouse" not in card
        assert card["activeHouses"] == list(active_houses_for_nakshatra(card["sign"], "Dhanishta"))


def test_classical_response_shape_is_untouched_on_classical_days():
    result = _build("2026-09-24")
    assert set(result["nakshatra"]) == {
        "name", "lord", "ruledRashis", "mode", "navtara", "navtaraTone",
    }
