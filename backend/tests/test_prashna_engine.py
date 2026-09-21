"""Tests for the Prashna / horary layer of Ask Kavach (System B)."""

from __future__ import annotations

import inspect
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

from main import app
from question_engine.engine import answer_question
from question_engine.evaluator import evaluate_prashna
from question_engine.knowledge.kavach_custom import EXTRA_CARE_HOUSES, EXTRA_CARE_TEMPLATE, SUPPORTIVE_TEMPLATE
from question_engine.moment import build_question_moment_context
from question_engine.topics import HOUSE_SIGNIFICATIONS, route_question

TZ = ZoneInfo("Asia/Kolkata")
WHEN = "2026-09-20T14:15:00+05:30"
DELHI = (28.6139, 77.2090, "Asia/Kolkata", "New Delhi")
BACKEND = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def evening():
    return answer_question("How will my evening go today?", WHEN, *DELHI)


# --- routing ---------------------------------------------------------------
@pytest.mark.parametrize(
    ("question", "house"),
    [
        ("What about my interview?", 10),
        ("Will this relationship work?", 7),
        ("How are my finances looking?", 2),
        ("How is the situation at home?", 4),
        ("How does my exam look?", 5),
        ("Will I gain from this?", 11),
        ("How will my evening go today?", 1),
    ],
)
def test_question_routes_to_expected_house(question, house):
    assert route_question(question)["primary_house"] == house


def test_all_twelve_houses_have_significations():
    assert set(HOUSE_SIGNIFICATIONS) == set(range(1, 13))


# --- KAVACH custom Moon rule ---------------------------------------------
@pytest.mark.parametrize("house", [6, 8, 12])
def test_moon_lord_extra_care_houses(house):
    assert house in EXTRA_CARE_HOUSES


@pytest.mark.parametrize("house", [1, 2, 3, 4, 5, 7, 9, 10, 11])
def test_moon_lord_supportive_houses(house):
    assert house not in EXTRA_CARE_HOUSES


def test_extra_care_tone_and_template_are_wired():
    moment = build_question_moment_context(
        datetime(2026, 9, 20, 14, 15, tzinfo=TZ), *DELHI
    )["moment"]
    evaluation = evaluate_prashna("How will my evening go today?", moment)
    assert evaluation["daily_moon_signal"] in ("supportive", "extra_care", "unclear")
    assert evaluation["overall_tone"] == evaluation["daily_moon_signal"]
    # only the KAVACH custom rule may set tone
    assert evaluation["kavach_rules_applied"] in ([], ["KC_DAILY_MOON_001"])
    assert "SP_CONTEXT_001" in evaluation["standard_rules_applied"]


def test_standard_rules_are_informational_only():
    from question_engine.knowledge.standard_prashna import STANDARD_RULES
    assert all(rule["kind"] == "informational" for rule in STANDARD_RULES)
    assert all(rule["provenance"]["source_type"] == "standard_prashna" for rule in STANDARD_RULES)


def test_kavach_rules_are_never_labelled_classical():
    from question_engine.knowledge.kavach_custom import KAVACH_RULES
    for rule in KAVACH_RULES.values():
        provenance = rule["provenance"]
        assert provenance["source_type"] == "kavach_custom"
        assert provenance["source"] == "kavach_astrologer_rule"


# --- core guarantees -------------------------------------------------------
def test_exact_question_timestamp_unchanged(evening):
    assert evening["used_timestamp"] == WHEN


def test_no_birth_details_and_no_natal_chart(evening):
    params = inspect.signature(answer_question).parameters
    for forbidden in ("birth_date", "birth_time", "birth_place", "natal", "chart"):
        assert forbidden not in params
    assert evening["uses_birth_details"] is False
    assert evening["uses_natal_chart"] is False


def test_question_engine_never_calls_panchang_natal():
    for path in (BACKEND / "question_engine").rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        assert "panchang_natal" not in source
        assert "generate_chart" not in source


def test_follow_up_retains_original_moment():
    result = answer_question(
        "What should I be careful about?", "2026-09-20T14:16:00+05:30", *DELHI,
        is_follow_up=True, original_timestamp=WHEN,
    )
    assert result["used_timestamp"] == WHEN


def test_new_topic_can_establish_new_moment():
    first = answer_question("How will my evening go today?", WHEN, *DELHI)
    second = answer_question("What about my exam tomorrow?", "2026-09-20T18:30:00+05:30", *DELHI)
    assert second["used_timestamp"] == "2026-09-20T18:30:00+05:30"
    assert second["used_timestamp"] != first["used_timestamp"]
    assert second["prashna"]["primary_house"] == 5


def test_evening_question_returns_a_real_answer(evening):
    assert evening["answered"] is True
    assert evening["status"] in ("supportive", "mixed", "extra_care", "unclear")
    assert evening["prashna"]["topic"] == "general_period"
    assert evening["prashna"]["primary_house"] == 1
    assert len(evening["answer"]) > 80
    assert "has not yet been added" not in evening["answer"]


# --- safety ----------------------------------------------------------------
@pytest.mark.parametrize("question", ["when will I die?", "how long will I live?"])
def test_lifespan_questions_refused(question):
    result = answer_question(question, WHEN, *DELHI)
    assert "does not answer questions about lifespan" in result["answer"]


def test_medical_diagnosis_refused():
    result = answer_question("can you diagnose what disease I have?", WHEN, *DELHI)
    assert "does not provide medical diagnoses" in result["answer"]


# --- API separation --------------------------------------------------------
def test_public_ask_api_leaks_no_calculation():
    client = TestClient(app)
    response = client.post("/api/ask", json={
        "question": "How will my evening go today?", "timestamp": WHEN,
        "latitude": 28.6139, "longitude": 77.209, "timezone": "Asia/Kolkata", "location_label": "New Delhi",
    })
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"status", "answered", "answer", "conversation_id"}
    blob = str(body).lower()
    for forbidden in ("house", "lagna", "nakshatra", "tithi", "moon", "rule", "prashna", "timestamp"):
        assert forbidden not in blob


def test_dev_chat_api_exposes_audit_information():
    client = TestClient(app)
    response = client.post("/api/dev/chat", json={
        "question": "How will my evening go today?", "timestamp": WHEN,
        "latitude": 28.6139, "longitude": 77.209, "timezone": "Asia/Kolkata", "location_label": "New Delhi",
    })
    assert response.status_code == 200
    body = response.json()
    assert body["prashna"]["primary_house"] == 1
    assert body["context"]["moment"]["chart"]["lagna"]["sign"]
    assert body["daily_moon_signal"] in ("supportive", "extra_care")


def test_no_scores_or_unsupported_claims(evening):
    blob = str(evening).lower()
    for forbidden in ("shadbala", "probability", "percent", "will definitely", "confidence score"):
        assert forbidden not in blob
