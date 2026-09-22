"""KAVACH Daily Prediction — deterministic tests (no network, no AI)."""

from __future__ import annotations

import inspect
import pathlib
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from daily.config import CAUTION, GOOD, HOUSE_PATTERNS, NEUTRAL, status
from daily.engine import (
    RASHIS,
    build_daily_prediction,
    calculate_active_house,
    get_best_colour,
    get_daily_category_status,
    get_daily_house_pattern,
    rashi_number,
)

TZ = ZoneInfo("Asia/Kolkata")


# --- the specified reference cases ---------------------------------------
@pytest.mark.parametrize("natal,transit,house", [
    # Forward through the zodiac from the transit Moon (transit Moon = H1).
    ("Pisces", "Sagittarius", 4),
    ("Aries", "Sagittarius", 5),
    ("Taurus", "Sagittarius", 6),
    ("Sagittarius", "Sagittarius", 1),
    ("Capricorn", "Sagittarius", 2),
    ("Aries", "Aries", 1),
    ("Pisces", "Aries", 12),
    ("Sagittarius", "Capricorn", 12),
])
def test_reference_cases(natal, transit, house):
    assert calculate_active_house(natal, transit) == house


def test_rashi_numbers():
    assert rashi_number("Aries") == 1
    assert rashi_number("Pisces") == 12


# --- complete coverage: all 144 combinations -----------------------------
def test_all_144_combinations_map_to_a_valid_house():
    seen = 0
    for natal in RASHIS:
        for transit in RASHIS:
            house = calculate_active_house(natal, transit)
            assert 1 <= house <= 12
            assert house in HOUSE_PATTERNS
            seen += 1
    assert seen == 144


@pytest.mark.parametrize("natal", RASHIS)
def test_each_natal_sign_uses_every_house_exactly_once(natal):
    houses = [calculate_active_house(natal, transit) for transit in RASHIS]
    assert sorted(houses) == list(range(1, 13))


def test_transit_change_rotates_all_signs():
    first = {sign: calculate_active_house(sign, "Sagittarius") for sign in RASHIS}
    second = {sign: calculate_active_house(sign, "Capricorn") for sign in RASHIS}
    assert all(first[sign] != second[sign] for sign in RASHIS)


# --- content configuration ------------------------------------------------
def test_all_twelve_houses_have_content():
    assert sorted(HOUSE_PATTERNS) == list(range(1, 13))
    for house, entry in HOUSE_PATTERNS.items():
        assert entry["theme"] and entry["pattern"]
        assert len(str(entry["pattern"])) > 80
        for category in ("love", "health", "career"):
            level, reason = entry[category]
            assert level in (GOOD, NEUTRAL, CAUTION)
            assert reason


def test_status_helper_returns_reason_from_the_same_house():
    level, reason = status(10, "career")
    assert level == GOOD
    work, health = status(6, "career"), status(6, "health")
    assert work[0] == GOOD and health[0] == CAUTION


def test_no_bad_label_is_used():
    for entry in HOUSE_PATTERNS.values():
        for category in ("love", "health", "career"):
            assert entry[category][0] in (GOOD, NEUTRAL, CAUTION)


# --- colour ---------------------------------------------------------------
def test_no_personalised_colour_rule_is_invented():
    # Awaiting the approved methodology: no fabricated per-sign colour.
    assert get_best_colour("Pisces", "Capricorn") is None
    payload = build_daily_prediction({"latitude": 28.6139, "longitude": 77.209})
    assert "colour" not in payload
    assert all(card["bestColour"] is None for card in payload["signs"])


# --- engine behaviour -----------------------------------------------------
def test_daily_payload_shape():
    payload = build_daily_prediction({"latitude": 28.6139, "longitude": 77.209,
                                      "timezone": "Asia/Kolkata"})
    assert payload["status"] == "ok"
    assert payload["dailyMoon"]["rashi"] in RASHIS
    assert payload["asOf"]["timezone"] == "Asia/Kolkata"
    assert len(payload["signs"]) == 12
    assert {card["sign"] for card in payload["signs"]} == set(RASHIS)
    for card in payload["signs"]:
        assert 1 <= card["activeHouse"] <= 12
        assert card["pattern"] and card["title"]
        assert set(card["categories"]) == {"love", "health", "career"}
        for category in card["categories"].values():
            assert category["status"] in (GOOD, NEUTRAL, CAUTION)
            assert category["reason"]


DAILY_FIXTURE = {"latitude": 28.6139, "longitude": 77.209, "timezone": "Asia/Kolkata",
                 "date": "2026-09-21", "place": "New Delhi, India"}


def _daily(at: str):
    return build_daily_prediction({**DAILY_FIXTURE, "at": at})


def test_daily_moon_is_the_sunrise_rashi_not_the_live_moon():
    # On 2026-09-21 in New Delhi the Moon is in Sagittarius at sunrise and
    # enters Capricorn later in the day. The Daily Prediction must keep using
    # the sunrise rashi for the whole Panchang day.
    early = _daily("2026-09-21T10:00:00+05:30")
    late = _daily("2026-09-21T14:00:00+05:30")

    assert early["dailyMoon"]["rashi"] == late["dailyMoon"]["rashi"] == "Sagittarius"
    assert late["currentMoon"]["rashi"] == "Capricorn"   # live moon moved on
    assert early["dailyMoon"]["sunrise"] and early["dailyMoon"]["longitude"]

    for early_card, late_card in zip(early["signs"], late["signs"]):
        assert early_card["activeHouse"] == late_card["activeHouse"]


SAGITTARIUS_MAPPING = {
    "Aries": 5, "Taurus": 6, "Gemini": 7, "Cancer": 8, "Leo": 9, "Virgo": 10,
    "Libra": 11, "Scorpio": 12, "Sagittarius": 1, "Capricorn": 2, "Aquarius": 3,
    "Pisces": 4,
}


def test_full_sagittarius_daily_mapping():
    payload = _daily("2026-09-21T10:00:00+05:30")
    actual = {card["sign"]: card["activeHouse"] for card in payload["signs"]}
    assert actual == SAGITTARIUS_MAPPING


def test_pisces_counts_forward_from_the_daily_moon():
    payload = _daily("2026-09-21T14:00:00+05:30")   # daily moon is Sagittarius
    pisces = next(card for card in payload["signs"] if card["sign"] == "Pisces")
    anchor = payload["dailyMoon"]["rashi"]
    assert anchor == "Sagittarius"

    # Forward direction: Sagittarius H1, Capricorn H2, Aquarius H3, Pisces H4.
    assert pisces["activeHouse"] == 4
    assert pisces["title"] == get_daily_house_pattern(4)["theme"]
    assert pisces["title"] != get_daily_house_pattern(10)["theme"]


def test_no_transition_history_is_returned_at_all():
    payload = _daily("2026-09-21T14:00:00+05:30")
    blob = str(payload).lower()
    for banned in ("earlier", "transition", "previous pattern", "\u00b7 now"):
        assert banned not in blob, banned
    for card in payload["signs"]:
        assert "earlierTitle" not in card


def test_colour_resolver_accepts_both_dimensions_and_is_pending():
    assert list(inspect.signature(get_best_colour).parameters) == ["natal_moon_sign", "daily_moon_rashi"]
    assert get_best_colour("Aries", "Sagittarius") is None
    assert get_best_colour("Aries", "Capricorn") is None
    payload = _daily("2026-09-21T10:00:00+05:30")
    assert "colour" not in payload
    assert all(card["bestColour"] is None for card in payload["signs"])


def test_daily_moon_uses_the_selected_date_and_location():
    other = build_daily_prediction({**DAILY_FIXTURE, "date": "2026-09-25"})
    assert other["dailyMoon"]["date"] == "2026-09-25"
    assert other["dailyMoon"]["rashi"] in RASHIS
    assert other["dailyMoon"]["sunrise"].startswith("2026-09-25")


def test_personal_highlight_when_natal_moon_is_supplied():
    payload = build_daily_prediction({"latitude": 28.6139, "longitude": 77.209,
                                      "natal_moon": "Pisces"})
    personal = [card for card in payload["signs"] if card["isPersonal"]]
    assert len(personal) == 1 and personal[0]["sign"] == "Pisces"
    assert personal[0]["activeHouse"] == calculate_active_house("Pisces", payload["dailyMoon"]["rashi"])


def test_transit_moon_is_sidereal_and_not_tropical():
    # A tropical Moon would sit in the next sign roughly 24 degrees later; the
    # sidereal value must match the production astronomy helper.
    from calculator import _sign_from_longitude
    from panchang import astronomy

    now = datetime.now(TZ)
    longitude = astronomy.moon_longitude(astronomy.to_jd(now))
    sign, _i, _d = _sign_from_longitude(longitude)
    payload = build_daily_prediction({"latitude": 28.6139, "longitude": 77.209})
    assert payload["currentMoon"]["rashi"] == sign


# --- structural guarantees ------------------------------------------------
def _import_lines(path: pathlib.Path):
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith(("import ", "from ")):
            yield stripped.lower()


def test_no_ascendant_can_affect_the_result():
    # The calculation takes only the two Moon signs, so an Ascendant cannot
    # influence it, and no module imports Ascendant/Lagna data.
    assert list(inspect.signature(calculate_active_house).parameters) == ["natal_moon", "daily_moon"]
    assert list(inspect.signature(get_daily_house_pattern).parameters) == ["active_house"]
    assert list(inspect.signature(get_daily_category_status).parameters) == ["active_house"]

    root = pathlib.Path(__file__).resolve().parents[1] / "daily"
    for path in root.glob("*.py"):
        for line in _import_lines(path):
            assert "ascendant" not in line and "lagna" not in line, f"{path.name}: {line}"


def test_calculation_needs_no_ai_or_network():
    root = pathlib.Path(__file__).resolve().parents[1] / "daily"
    for path in root.glob("*.py"):
        for line in _import_lines(path):
            for forbidden in ("gemini", "httpx", "requests", "openai", "urllib", "socket"):
                assert forbidden not in line, f"{path.name}: {line}"
