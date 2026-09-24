"""Active Daily path uses rulership only; historical semantics stay inactive."""

from __future__ import annotations

import pathlib

from daily.engine import build_daily_prediction

REPO = pathlib.Path(__file__).resolve().parents[2]
PAGE = REPO / "frontend-next" / "app" / "daily" / "page.tsx"

DELHI = {"latitude": 28.6139, "longitude": 77.209, "timezone": "Asia/Kolkata", "place": "Delhi"}
DAY = {**DELHI, "date": "2026-09-24"}  # Dhanishtha at local sunrise


def test_daily_succeeds_without_any_natal_input():
    result = build_daily_prediction(dict(DAY))
    assert result["status"] == "ok"
    assert len(result["signs"]) == 12
    assert result["natalMoon"] is None
    assert all(card["isPersonal"] is False for card in result["signs"])


def test_active_path_never_calls_previous_semantic_composer(monkeypatch):
    import daily.compose as old_composer

    def forbidden(*_args, **_kwargs):
        raise AssertionError("old House x Nakshatra semantic composer was called")

    monkeypatch.setattr(old_composer, "compose_daily_pattern", forbidden)
    monkeypatch.setattr(old_composer, "compose_daily_category", forbidden)
    result = build_daily_prediction(dict(DAY))
    assert result["nakshatra"]["lord"] == "Mars"


def test_no_nakshatra_behaviour_or_navtara_in_active_result():
    result = build_daily_prediction({
        **DAY,
        "natal_moon": "Aries",
        "natal_nakshatra": "Ashvini",
    })
    assert result["nakshatra"]["mode"] == ""
    assert result["nakshatra"]["navtara"] == ""
    assert result["nakshatra"]["navtaraTone"] == {}
    assert result["natalMoon"] is None
    assert all(card["isPersonal"] is False for card in result["signs"])


def test_each_card_has_one_integrated_prediction_in_the_ui():
    page = PAGE.read_text(encoding="utf-8")
    assert page.count("card.pattern") == 1
    assert "nakshatraGuidance" not in page


def test_frontend_daily_remains_public_and_non_natal():
    page = PAGE.read_text(encoding="utf-8")
    assert "deriveNatal" not in page
    assert "listProfiles" not in page
    assert "PersonSelector" not in page
    assert "natal_moon" not in page and "natal_nakshatra" not in page
    assert "date: localDate" in page
    assert "Nakshatra Lord:" in page
