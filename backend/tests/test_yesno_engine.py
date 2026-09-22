"""KAVACH YES / NO: the deterministic engine, interpretation, safety and API."""

from __future__ import annotations

import json
import pathlib
from datetime import datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from yesno import CERTAINTY_DISCLAIMER, SAFE_MESSAGE, evaluate_yes_no, verdict_for_time
from yesno.safety import sensitive_refusal, unsafe_category
from yesno.types import SafetyRefusal, YesNoResult

REPO = pathlib.Path(__file__).resolve().parents[2]


def at(hour: int, minute: int) -> datetime:
    return datetime(2026, 9, 22, hour, minute)


def result(hour: int, minute: int, question: str = "Will my business deal work?"):
    outcome = evaluate_yes_no(question, at(hour, minute))
    assert isinstance(outcome, YesNoResult)
    return outcome


# --- the required example ----------------------------------------------------
def test_1553_venus_saturn_is_yes():
    outcome = result(15, 53)

    assert (outcome.hour_number, outcome.minute_number) == (6, 8)
    assert (outcome.hour_planet, outcome.minute_planet) == ("Venus", "Saturn")
    assert outcome.relationship == "FRIEND"
    assert outcome.verdict == "YES"


def test_yes_still_reports_delay_for_saturn():
    """YES with Saturn stays YES: delay is described, not converted into a NO."""
    outcome = result(15, 53)
    text = outcome.interpretation.lower()

    assert outcome.verdict == "YES"
    assert "delay" in text or "patience" in text
    assert "established" in text or "gradual" in text or "longer" in text


@pytest.mark.parametrize("hour,minute,expected", [
    (15, 53, "YES"), (15, 49, "YES"), (12, 38, "YES"), (10, 5, "YES"),
    (23, 59, "50/50"), (9, 27, "50/50"),
    (9, 5, "NO"),
])
def test_verdicts_for_known_times(hour, minute, expected):
    assert verdict_for_time(hour, minute) == expected
    assert result(hour, minute).verdict == expected


# --- interpretation per verdict ---------------------------------------------
def test_yes_explanation_is_supportive():
    text = result(15, 53).interpretation.lower()
    assert "support" in text or "favourable" in text or "positive" in text


def test_no_explanation_reflects_resistance_without_absolutes():
    outcome = result(9, 5)  # Mars -> Mercury is an enemy pair
    text = outcome.interpretation.lower()

    assert outcome.verdict == "NO"
    assert "resistance" in text or "working against" in text
    for absolute in ("definitely", "100%", "certainly", "will happen", "never"):
        assert absolute not in text, absolute


def test_even_explanation_reflects_a_mixed_result():
    outcome = result(23, 59)  # Mercury with Mercury
    text = outcome.interpretation.lower()

    assert outcome.verdict == "50/50"
    assert "mixed" in text or "not strongly tilted" in text or "balanced" in text
    assert "mercury" in text


def test_every_interpretation_carries_the_disclaimer():
    for hour, minute in ((15, 53), (9, 5), (23, 59), (9, 27), (10, 5)):
        assert CERTAINTY_DISCLAIMER in result(hour, minute).interpretation


# --- planets do not decide on their own -------------------------------------
def test_mars_speed_does_not_create_a_yes():
    outcome = result(9, 5)  # Mars is the hour planet, verdict is NO
    text = outcome.interpretation.lower()
    assert outcome.hour_planet == "Mars"
    assert outcome.verdict == "NO"
    assert "urgency" in text or "friction" in text


def test_rahu_does_not_automatically_mean_no():
    outcome = result(4, 5)  # Rahu -> Mercury is a friend pair
    assert outcome.hour_planet == "Rahu"
    assert outcome.verdict == "YES"
    assert "rahu" in outcome.interpretation.lower()


def test_ketu_does_not_automatically_mean_no():
    outcome = result(7, 9)  # Ketu -> Mars is a friend pair
    assert outcome.hour_planet == "Ketu"
    assert outcome.verdict == "YES"
    assert "ketu" in outcome.interpretation.lower()


# --- the question can never change the verdict ------------------------------
def test_question_wording_cannot_override_the_verdict():
    questions = (
        "Will my business deal work?",
        "Will I fail completely?",
        "Is this a terrible idea?",
        "Will everything go wrong?",
        "",
    )
    verdicts = {evaluate_yes_no(q, at(15, 53)).verdict for q in questions}
    assert verdicts == {"YES"}


def test_question_only_shapes_the_wording():
    a = result(15, 53, "Will my business deal work?")
    b = result(15, 53, "Will my relationship last?")
    assert a.verdict == b.verdict
    assert a.relationship == b.relationship
    assert a.interpretation != b.interpretation


def test_interpretation_is_deterministic():
    first = result(15, 53).interpretation
    second = result(15, 53).interpretation
    assert first == second


# --- no language model participates -----------------------------------------
def test_no_llm_is_used(monkeypatch):
    def exploding(*_args, **_kwargs):
        raise AssertionError("YES / NO must never call a language model")

    monkeypatch.setattr("chat.groq.generate_reply_detailed", exploding)
    monkeypatch.setattr("chat.gemini.generate_reply_detailed", exploding)

    assert result(15, 53).verdict == "YES"


def test_engine_has_no_provider_imports():
    for name in ("engine.py", "interpretation.py", "numbers.py", "planets.py", "relationships.py"):
        source = (REPO / "backend" / "yesno" / name).read_text(encoding="utf-8").lower()
        for banned in ("groq", "gemini", "httpx", "openai", "anthropic"):
            assert banned not in source, f"{name} references {banned}"


# --- safety ------------------------------------------------------------------
@pytest.mark.parametrize("question", [
    "Will I die soon?",
    "What is my lifespan?",
    "Do I have a terminal illness?",
    "Should I end my life?",
    "Will I have a medical emergency this year?",
    "Should I commit a crime?",
])
def test_unsafe_topics_get_the_safe_message_not_a_verdict(question):
    outcome = evaluate_yes_no(question, at(15, 53))

    assert isinstance(outcome, SafetyRefusal)
    assert outcome.message == SAFE_MESSAGE
    assert outcome.to_public()["verdict"] is None
    assert "yes" not in outcome.message.lower().split()[0:2]


@pytest.mark.parametrize("question", [
    "Will my business grow?",
    "Will things improve for my Cancer moon?",
    "Will my emergency fund be enough?",
    "Will I meet my deadline?",
    "Is my diet going to change my energy?",
])
def test_ordinary_questions_are_not_refused(question):
    assert sensitive_refusal(question) is None
    assert unsafe_category(question) is None
    assert isinstance(evaluate_yes_no(question, at(15, 53)), YesNoResult)


# --- invariants --------------------------------------------------------------
def test_numbers_stay_within_one_to_nine_all_day():
    for hour in range(24):
        for minute in range(60):
            outcome = evaluate_yes_no("Will it work?", at(hour, minute))
            assert 1 <= outcome.hour_number <= 9
            assert 1 <= outcome.minute_number <= 9
            assert outcome.verdict in {"YES", "NO", "50/50"}
            assert 0 not in (outcome.hour_number, outcome.minute_number)


def test_no_placeholders_leak_into_the_text_all_day():
    """Every minute of the day must produce finished prose, with no {placeholder}."""
    for hour in range(24):
        for minute in range(60):
            text = evaluate_yes_no("Will it work?", at(hour, minute)).interpretation
            assert "{" not in text and "}" not in text, f"{hour:02d}:{minute:02d}: {text}"


def test_public_payload_hides_the_mechanics():
    outcome = result(15, 53, "Will my business deal work?")
    payload = outcome.to_public()

    assert set(payload) == {"verdict", "interpretation"}
    blob = json.dumps(payload)
    for banned in ("FRIEND", "ENEMY", "NEUTRAL", "hour_number", "minute_number",
                   "hour_planet", "relationship", "15:53"):
        assert banned not in blob, banned


def test_invalid_input_is_rejected():
    with pytest.raises(ValueError):
        evaluate_yes_no("q", "15:53")  # type: ignore[arg-type]


# --- the mounted API surface -------------------------------------------------
def test_router_is_mounted_on_the_app():
    """Owner-approved integration: /api/yes-no is reachable on the existing app."""
    import main
    from yesno.api import router as yes_no_router

    included = [getattr(route, "original_router", None) for route in main.app.routes
                if type(route).__name__ == "_IncludedRouter"]
    assert yes_no_router in included, "the YES / NO router must be the mounted sub-router"

    response = TestClient(main.app).post("/api/yes-no", json={
        "question": "Will my business deal work?",
        "timestamp": "2026-09-22T10:23:00+00:00",
        "timezone": "Asia/Kolkata",
    })
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_mounted_endpoint_returns_the_1553_verdict():
    """15:53 local -> 6/8 -> Venus -> Saturn -> FRIEND -> YES."""
    import main

    body = TestClient(main.app).post("/api/yes-no", json={
        "question": "Will my business deal work?",
        "timestamp": "2026-09-22T10:23:00+00:00",
        "timezone": "Asia/Kolkata",
    }).json()

    assert body["status"] == "ok"
    assert body["verdict"] == "YES"
    assert isinstance(body["interpretation"], str) and body["interpretation"]


def test_mounted_endpoint_handles_midnight_zero():
    """00 -> 9 is owner-approved: 00:00 is Mars with Mars, i.e. 50/50."""
    import main

    body = TestClient(main.app).post("/api/yes-no", json={
        "question": "Will it work?",
        "timestamp": "2026-09-22T00:00:00+00:00",
        "timezone": "UTC",
    }).json()

    assert body["status"] == "ok"
    assert body["verdict"] == "50/50"


def test_mounted_endpoint_hides_the_mechanics():
    import main

    body = TestClient(main.app).post("/api/yes-no", json={
        "question": "Will my business deal work?",
        "timestamp": "2026-09-22T10:23:00+00:00",
        "timezone": "Asia/Kolkata",
    }).json()

    assert set(body) == {"status", "verdict", "interpretation"}
    blob = json.dumps(body)
    for banned in ("FRIEND", "NEUTRAL", "hour_number", "minute_number", "relationship", "15:53"):
        assert banned not in blob, banned


def test_mounted_endpoint_preserves_safety_behaviour():
    import main

    body = TestClient(main.app).post("/api/yes-no", json={
        "question": "Will I die soon?",
        "timestamp": "2026-09-22T10:23:00+00:00",
        "timezone": "Asia/Kolkata",
    }).json()

    assert body["status"] == "ok"
    assert body["verdict"] is None
    assert body["interpretation"] == SAFE_MESSAGE


def test_mounted_endpoint_rejects_bad_input():
    import main

    client = TestClient(main.app)
    assert client.post("/api/yes-no", json={"question": "q", "timestamp": "not-a-time"}).json()["status"] == "invalid"
    assert client.post("/api/yes-no", json={"question": "q"}).json()["status"] == "invalid"


def test_standalone_router_still_works():
    from yesno.api import router

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    body = client.post("/api/yes-no", json={
        "question": "Will my business deal work?",
        "timestamp": "2026-09-22T10:23:00+00:00",
        "timezone": "Asia/Kolkata",
    }).json()

    assert body["status"] == "ok"
    assert body["verdict"] == "YES"
    assert set(body) == {"status", "verdict", "interpretation"}


# --- the public page ---------------------------------------------------------
FRONTEND = REPO / "frontend-next"
YES_NO_PAGE = FRONTEND / "app" / "yes-no" / "page.tsx"
YES_NO_UI = FRONTEND / "components" / "YesNoExperience.tsx"


def test_yes_no_page_and_experience_exist():
    assert YES_NO_PAGE.exists(), "the /yes-no page must exist"
    assert YES_NO_UI.exists(), "the YES / NO experience component must exist"
    assert "metadata" in YES_NO_PAGE.read_text(encoding="utf-8")


def test_yes_no_ui_calls_the_deterministic_endpoint_with_local_time():
    ui = YES_NO_UI.read_text(encoding="utf-8")

    assert "/yes-no" in ui and "API_BASE" in ui
    assert "new Date().toISOString()" in ui, "the exact moment of the question"
    assert "resolvedOptions().timeZone" in ui, "the user's own timezone"
    assert "POST" not in ui or "method: 'POST'" in ui


def test_yes_no_ui_shows_loading_error_and_prevents_double_submit():
    ui = YES_NO_UI.read_text(encoding="utf-8")

    for state in ("idle", "loading", "done", "error"):
        assert f"'{state}'" in ui, state
    assert "submitting" in ui, "a double submission guard is required"
    assert "disabled=" in ui
    assert "aria-live" in ui, "the result region must be announced"


def test_yes_no_ui_hides_the_mechanics():
    ui = YES_NO_UI.read_text(encoding="utf-8")

    for banned in ("hour_number", "minute_number", "hour_planet", "minute_planet",
                   "relationship", "FRIEND", "NEUTRAL", "ENEMY", "matrix"):
        assert banned not in ui, f"the page must not expose {banned}"


def test_yes_no_ui_has_no_monetization_or_provider_calls():
    ui = YES_NO_UI.read_text(encoding="utf-8").lower()

    for banned in ("servicescta", "wa.me", "whatsapp", "razorpay", "stripe", "groq", "gemini"):
        assert banned not in ui, banned
