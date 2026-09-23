"""CURRENT Daily product: TRANSIT-ONLY, ONE integrated prediction per field.

House theme (WHERE) x transit Nakshatra (HOW) x category must produce ONE
coherent interpretation. The old behaviour - a house sentence followed by an
appended generic Nakshatra sentence - is explicitly rejected here.
"""

from __future__ import annotations

import json
import pathlib

from daily.compose import compose_daily_category, compose_daily_pattern
from daily.config import HOUSE_PATTERNS
from daily.engine import build_daily_prediction

REPO = pathlib.Path(__file__).resolve().parents[2]
PAGE = REPO / "frontend-next" / "app" / "daily" / "page.tsx"
MODES = REPO / "backend" / "nakshatra_knowledge" / "modes.py"

DELHI = {"latitude": 28.6139, "longitude": 77.209, "timezone": "Asia/Kolkata", "place": "Delhi"}
DAY = {**DELHI, "date": "2026-09-23"}
CATEGORIES = ("love", "health", "career")


def _result():
    return build_daily_prediction(dict(DAY))


def test_daily_succeeds_without_any_natal_input():
    result = _result()
    assert result["status"] == "ok"
    assert len(result["signs"]) == 12


def test_no_personal_reading_failure_ever_appears():
    raw = json.dumps(_result()).lower()
    assert "personal reading" not in raw
    assert "could not calculate" not in raw


def test_aries_libra_pisces_patterns_differ_for_shravana():
    """Each sign falls in a different active house, so Shravana reads differently."""
    patterns = {
        sign: compose_daily_pattern(house, "Shravana")
        for sign, house in (("Aries", 4), ("Libra", 10), ("Pisces", 3))
    }
    assert len(set(patterns.values())) == 3


def test_the_raw_house_paragraph_is_not_rendered_before_the_composed_one():
    for card in _result()["signs"]:
        raw = str(HOUSE_PATTERNS[card["activeHouse"]]["pattern"])
        assert raw not in card["pattern"], card["sign"]


def test_each_sign_has_exactly_one_integrated_pattern_in_the_ui():
    page = PAGE.read_text(encoding="utf-8")
    assert page.count("card.pattern") == 1
    assert "nakshatraGuidance" not in page


def test_love_health_career_are_never_the_same_appended_suffix():
    for card in _result()["signs"]:
        reasons = [card["categories"][c]["reason"] for c in CATEGORIES]
        assert len(set(reasons)) == 3, card["sign"]


def test_aries_love_health_career_are_category_specific():
    love = compose_daily_category(4, "Shravana", "love")
    health = compose_daily_category(4, "Shravana", "health")
    career = compose_daily_category(4, "Shravana", "career")
    assert len({love, health, career}) == 3


def test_same_house_different_nakshatra_is_materially_different():
    for house in (4, 10, 3):
        assert compose_daily_pattern(house, "Shravana") != compose_daily_pattern(house, "Ashwini")
        for category in CATEGORIES:
            assert (compose_daily_category(house, "Shravana", category)
                    != compose_daily_category(house, "Ashwini", category)), (house, category)


def test_all_twelve_signs_are_integrated_house_x_nakshatra():
    result = _result()
    name = result["nakshatra"]["name"]
    assert name
    assert len(result["signs"]) == 12
    patterns = [card["pattern"] for card in result["signs"]]
    assert len(set(patterns)) == 12, "each sign must read differently"
    for card in result["signs"]:
        # The rendered pattern is exactly the composed house x Nakshatra text.
        assert card["pattern"] == compose_daily_pattern(card["activeHouse"], name), card["sign"]
        for category in CATEGORIES:
            assert (card["categories"][category]["reason"]
                    == compose_daily_category(card["activeHouse"], name, category)), (card["sign"], category)


def test_raw_nakshatra_keywords_are_never_printed():
    raw = json.dumps(_result())
    for leaked in ("this area expresses through", "listen, learn and communicate",
                   "Today's lunar pattern favours", "practical route forward", "help it land"):
        assert leaked not in raw, leaked


def test_the_generic_appended_construction_is_gone():
    source = MODES.read_text(encoding="utf-8")
    assert "Today's lunar pattern favours" not in source
    assert "compose_category" not in source
    assert "Today's lunar pattern favours" not in json.dumps(_result())


def test_navtara_personal_code_is_preserved_but_inactive():
    from navtara.engine import classify_transit_nakshatra

    assert callable(classify_transit_nakshatra), "the Navtara engine is preserved"
    result = _result()
    assert result["nakshatra"]["navtara"] == ""
    assert result["nakshatra"]["navtaraTone"] == {}
    assert result["natalMoon"] is None
    assert all(card["isPersonal"] is False for card in result["signs"])


def test_frontend_daily_is_transit_only():
    page = PAGE.read_text(encoding="utf-8")
    assert "deriveNatal" not in page
    assert "listProfiles" not in page
    assert "PersonSelector" not in page
    assert "natal_moon" not in page and "natal_nakshatra" not in page
    assert "date: localDate" in page
