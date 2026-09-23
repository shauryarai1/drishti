"""CURRENT Daily product: TRANSIT-ONLY.

The viewer's personal Janma-Nakshatra / Navtara layer is intentionally NOT part
of the current Daily prediction. The transit Moon Nakshatra is the HOW and it
must materially shape every Moon sign's Today's Pattern, Love, Health and
Career. The natal/Navtara code is preserved for possible future use, but a
request without natal input must succeed and must never surface a personal-
reading failure.
"""

from __future__ import annotations

import json
import pathlib

from daily.engine import build_daily_prediction
from nakshatra_knowledge.modes import (
    compose_category, compose_guidance, nakshatra_expression,
)

REPO = pathlib.Path(__file__).resolve().parents[2]
PAGE = REPO / "frontend-next" / "app" / "daily" / "page.tsx"

DELHI = {"latitude": 28.6139, "longitude": 77.209, "timezone": "Asia/Kolkata", "place": "Delhi"}
DAY = {**DELHI, "date": "2026-09-23"}


def test_daily_succeeds_without_any_natal_input():
    result = build_daily_prediction(dict(DAY))
    assert result["status"] == "ok"
    assert len(result["signs"]) == 12


def test_no_personal_reading_failure_ever_appears():
    raw = json.dumps(build_daily_prediction(dict(DAY))).lower()
    assert "personal reading" not in raw
    assert "could not calculate" not in raw


def test_the_same_house_pattern_changes_with_the_transit_nakshatra():
    theme = "Career and public role"
    reason = "steady progress is supported"
    assert compose_guidance(theme, "Shravana") != compose_guidance(theme, "Ashwini")
    assert compose_category(reason, "Shravana") != compose_category(reason, "Ashwini")
    # The house reading is modified, never replaced.
    assert reason in compose_category(reason, "Shravana")


def test_all_twelve_signs_receive_nakshatra_sensitive_output():
    result = build_daily_prediction(dict(DAY))
    name = result["nakshatra"]["name"]
    assert name
    expression = nakshatra_expression(name)
    assert len(result["signs"]) == 12
    for card in result["signs"]:
        assert card["nakshatraGuidance"], card["sign"]
        for category in ("love", "health", "career"):
            assert expression in card["categories"][category]["reason"], (card["sign"], category)


def test_navtara_personal_code_is_preserved_but_inactive():
    from navtara.engine import classify_transit_nakshatra

    assert callable(classify_transit_nakshatra), "the Navtara engine is preserved"
    result = build_daily_prediction(dict(DAY))
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
    # The transit Nakshatra is rendered per sign, and the city/date pipeline stays.
    assert "card.nakshatraGuidance" in page
    assert "date: localDate" in page
