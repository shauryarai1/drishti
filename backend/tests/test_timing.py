from datetime import date, datetime, timezone
import json

from interpretation import RASHI_GUIDANCE
from timing import calculate_caution_windows


BASE = date(2026, 1, 1)


def fake_position(body: str, moment: datetime) -> int:
    day = (moment.date() - BASE).days
    if body == "Saturn":
        if 10 <= day < 20 or 40 <= day < 50:
            return 0
        if 60 <= day < 70:
            return 1
    if body == "Rahu" and 15 <= day < 25:
        return 0
    if body == "Ketu" and 30 <= day < 40:
        return 2
    return 5


def test_all_bodies_have_refined_ingress_and_egress_windows():
    result = calculate_caution_windows(
        ["Aries", "Taurus", "Gemini"],
        RASHI_GUIDANCE,
        start_date=BASE,
        horizon_years=1,
        position_fn=fake_position,
    )

    windows = result["upcoming"]
    assert windows
    assert any(item["start_date"] == "2026-01-11" and item["end_date"] == "2026-01-26" for item in windows)
    assert any(item["start_date"] == "2026-01-31" and item["end_date"] == "2026-02-20" for item in windows)
    assert all("triggers" not in item for item in windows)


def test_current_period_and_retrograde_reentry_are_preserved():
    result = calculate_caution_windows(
        ["Aries"],
        RASHI_GUIDANCE,
        start_date=date(2026, 1, 18),
        horizon_years=1,
        position_fn=fake_position,
    )

    assert result["current"] is not None
    assert result["current"]["start_date"] == "2026-01-11"
    assert result["current"]["end_date"] == "2026-01-26"

    later = calculate_caution_windows(
        ["Aries"],
        RASHI_GUIDANCE,
        start_date=BASE,
        horizon_years=1,
        position_fn=fake_position,
    )
    assert any(item["start_date"] == "2026-02-10" for item in later["upcoming"])


def test_overlapping_windows_are_merged_and_chronological():
    result = calculate_caution_windows(
        ["Aries"],
        RASHI_GUIDANCE,
        start_date=BASE,
        horizon_years=1,
        position_fn=fake_position,
    )

    windows = result["upcoming"]
    assert windows[0]["start_date"] == "2026-01-11"
    assert windows[0]["end_date"] == "2026-01-26"
    assert windows == sorted(windows, key=lambda item: item["start_date"])


def test_ten_year_horizon_and_public_copy_are_safe():
    result = calculate_caution_windows(
        ["Aries"],
        RASHI_GUIDANCE,
        start_date=BASE,
        horizon_years=10,
        position_fn=lambda _body, _moment: 5,
    )

    assert result["current"] is None
    assert result["upcoming"] == []


def test_public_timing_payload_contains_no_internal_theory():
    result = calculate_caution_windows(
        ["Aries"],
        RASHI_GUIDANCE,
        start_date=BASE,
        horizon_years=1,
        position_fn=fake_position,
    )
    public_text = json.dumps(result).lower()
    for forbidden in ("mars", "mangal", "saturn", "shani", "rahu", "ketu", "aspect", "malefic", "transit"):
        assert forbidden not in public_text
