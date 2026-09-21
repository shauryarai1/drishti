"""Tests proving System A (birth summary) and System B (question chat) are separate."""

from __future__ import annotations

import inspect
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

from main import app
from panchang import PanchangRequest, compute_panchang
from panchang.moment import calculate_panchang_moment
from prediction.panchang_natal.engine import compute_panchang_natal_significators
from question_engine.engine import answer_question
from question_engine.rules import KAVACH_QUESTION_RULES, NO_RULE_MESSAGE

TZ = ZoneInfo("Asia/Kolkata")
DELHI = (28.6139, 77.2090, "Asia/Kolkata", "New Delhi")
BACKEND = Path(__file__).resolve().parents[1]


def test_birth_summary_still_requires_birth_details():
    parameters = inspect.signature(compute_panchang_natal_significators).parameters
    for required in ("birth_date", "birth_time", "latitude", "longitude"):
        assert required in parameters, f"{required} must remain required"


def test_chatbot_requires_no_birth_details():
    parameters = inspect.signature(answer_question).parameters
    for forbidden in ("birth_date", "birth_time", "birth_place", "natal", "chart"):
        assert forbidden not in parameters
    result = answer_question("How will my interview go?", "2026-09-20T14:15:00+05:30", *DELHI)
    assert result["uses_birth_details"] is False
    assert result["uses_natal_chart"] is False


def test_question_at_1415_uses_1415_calculations():
    result = answer_question("How does this look?", "2026-09-20T14:15:37+05:30", *DELHI)
    direct = calculate_panchang_moment(
        datetime(2026, 9, 20, 14, 15, 37, tzinfo=TZ), *DELHI
    )
    assert result["used_timestamp"] == "2026-09-20T14:15:37+05:30"
    assert result["context"]["moment"]["tithi"]["name"] == direct["tithi"]["name"]
    assert result["context"]["moment"]["nakshatra"]["pada"] == direct["nakshatra"]["pada"]
    assert result["context"]["moment"]["chart"]["lagna"]["sign"] == direct["chart"]["lagna"]["sign"]


def test_question_moment_is_not_sunrise_d1():
    """The question chart must differ from the production Sunrise D1."""
    sunrise_panchang = compute_panchang(
        PanchangRequest(on_date=datetime(2026, 9, 20).date(), latitude=DELHI[0],
                        longitude=DELHI[1], timezone_name=DELHI[2], label=DELHI[3])
    )
    moment = calculate_panchang_moment(datetime(2026, 9, 20, 14, 15, tzinfo=TZ), *DELHI)
    assert moment["timestamp"] != sunrise_panchang["sun_moon"]["sunrise"]
    assert moment["chart"]["lagna"]["sign"] != sunrise_panchang["d1"]["lagna"]["sign"]
    assert moment["nakshatra"]["pada"] != sunrise_panchang["panchanga"]["nakshatra"]["pada"]


def test_new_question_at_1416_produces_new_moment():
    first = answer_question("How will my evening look?", "2026-09-20T14:15:00+05:30", *DELHI)
    second = answer_question("What about my work matters?", "2026-09-20T14:16:00+05:30", *DELHI)
    assert first["used_timestamp"] != second["used_timestamp"]
    assert second["used_timestamp"] == "2026-09-20T14:16:00+05:30"


def test_follow_up_retains_original_question_moment():
    result = answer_question(
        "What should I be careful about?",
        "2026-09-20T14:16:00+05:30",
        *DELHI,
        is_follow_up=True,
        original_timestamp="2026-09-20T14:15:00+05:30",
    )
    assert result["used_timestamp"] == "2026-09-20T14:15:00+05:30"
    assert result["requested_timestamp"] == "2026-09-20T14:16:00+05:30"
    assert result["is_follow_up"] is True


def test_changing_location_changes_moment_context():
    delhi = calculate_panchang_moment(datetime(2026, 9, 20, 14, 15, tzinfo=TZ), *DELHI)
    london = calculate_panchang_moment(
        datetime(2026, 9, 20, 14, 15, tzinfo=TZ), 51.5074, -0.1278, "Europe/London", "London"
    )
    assert delhi["tithi"]["name"] == london["tithi"]["name"]  # global instant
    assert delhi["chart"]["lagna"]["sign"] != london["chart"]["lagna"]["sign"]


def test_chatbot_does_not_touch_panchang_natal():
    for path in (BACKEND / "question_engine").glob("*.py"):
        source = path.read_text(encoding="utf-8")
        assert "panchang_natal" not in source, f"{path.name} must not use System A"
        assert "generate_chart" not in source, f"{path.name} must not use the natal calculator"


def test_birth_summary_does_not_touch_question_engine():
    for path in (BACKEND / "prediction" / "panchang_natal").glob("*.py"):
        source = path.read_text(encoding="utf-8")
        assert "question_engine" not in source, f"{path.name} must not use System B"


def test_existing_panchang_endpoint_still_works():
    client = TestClient(app)
    response = client.get(
        "/api/panchang",
        params={"date": "2026-09-20", "latitude": 28.6139, "longitude": 77.2090,
                "timezone": "Asia/Kolkata", "label": "New Delhi"},
    )
    assert response.status_code == 200
    assert response.json()["d1"]["instant"]


def test_sunrise_d1_behaviour_unchanged():
    """The production Panchang still builds its D1 at sunrise."""
    produced = compute_panchang(
        PanchangRequest(on_date=datetime(2026, 9, 20).date(), latitude=DELHI[0],
                        longitude=DELHI[1], timezone_name=DELHI[2], label=DELHI[3])
    )
    assert produced["d1"]["instant"] == produced["sun_moon"]["sunrise"]


def test_no_unsupported_interpretation_added():
    """Only approved templates may be returned: no scores, no fabricated claims."""
    from question_engine.knowledge.kavach_custom import EXTRA_CARE_TEMPLATE, SUPPORTIVE_TEMPLATE

    assert KAVACH_QUESTION_RULES == []
    result = answer_question("Should I be careful?", "2026-09-20T18:30:00+05:30", *DELHI)
    assert result["answered"] is True
    answer = result["answer"].lower()
    assert "not prepared a reading" not in answer
    for forbidden in ("exalted", "debilitated", "score", "probability", "shadbala", "percent"):
        assert forbidden not in answer


def test_timestamp_must_be_timezone_aware():
    with pytest.raises(ValueError):
        answer_question("How will my evening go?", "2026-09-20T14:15:00", *DELHI)
