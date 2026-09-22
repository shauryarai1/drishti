"""Ask KAVACH: scope behaviour, provider chain and privacy.

Ask KAVACH is an astrology / KAVACH advisory assistant. Casual conversation is
answered briefly; unrelated requests get the short scope message with no
provider call at all; astrology questions carry the chart context; personal
questions carry the hidden reading. Providers are mocked - no live quota.
"""

from __future__ import annotations

import json
import logging

import pytest
from fastapi.testclient import TestClient

import archive
import chat.gemini as gemini
import chat.groq as groq
import chat.router as router
import main

ASK = {"timestamp": "2026-09-22T11:45:00+05:30", "latitude": 28.6139, "longitude": 77.209,
       "timezone": "Asia/Kolkata"}

CASUAL_QUESTIONS = ["hi", "how are you?", "thanks", "hello"]
OUT_OF_SCOPE_QUESTIONS = ["what is gravity?", "explain photosynthesis", "write an email",
                          "write a Python script", "will it rain tomorrow?",
                          "solve this equation", "give me a recipe"]
ASTROLOGY_QUESTIONS = ["read my kundli", "what does Saturn mean in my chart?", "how is my dasha?"]


class FakeStore:
    def __init__(self):
        self.rows: list[dict] = []

    def configured(self):
        return True

    def insert(self, row):
        stored = dict(row)
        stored["id"] = f"row-{len(self.rows) + 1}"
        self.rows.append(stored)
        return stored["id"]

    def verify_token(self, token):
        return None


@pytest.fixture()
def env(monkeypatch):
    """Mock both providers and the geocoder; record what each one saw."""
    seen: dict = {"groq": [], "gemini": [], "geocoder": 0, "readings": [], "astrology": []}

    monkeypatch.setattr(archive, "store", FakeStore())
    monkeypatch.setattr("chat.reading.sensitive_response", lambda _q: None)

    def fake_reading(question):
        seen["readings"].append(question)
        return {"draw_id": "d1", "interpretations": [{"reading": "context"}]}

    monkeypatch.setattr("chat.reading.build_reading", fake_reading)
    monkeypatch.setattr("chat.reading.private_context", lambda _r: "PRIVATE READING CONTEXT")

    def fake_groq(_q, _h, private_context="", astrology_context=""):
        seen["groq"].append(private_context)
        seen["astrology"].append(astrology_context)
        return {"text": "Groq answer.", "model": groq.MODEL, "preferred": groq.MODEL,
                "provider": "groq", "attempts": [{"model": groq.MODEL, "reason": "ok"}],
                "fallback": False, "reasoning_content": "HIDDEN"}

    def fake_gemini(_q, _h, private_context="", astrology_context=""):
        seen["gemini"].append(private_context)
        return {"text": "Gemini answer.", "model": "gemini-3.5-flash-lite",
                "preferred": "gemini-3.5-flash-lite", "provider": "gemini", "attempts": []}

    monkeypatch.setattr("chat.groq.generate_reply_detailed", fake_groq)
    monkeypatch.setattr("chat.gemini.generate_reply_detailed", fake_gemini)

    import geocoding

    def geocoder_guard(_query, _limit):
        seen["geocoder"] += 1
        raise AssertionError("Ask KAVACH must never call the geocoder")

    monkeypatch.setattr(geocoding, "_provider_search", geocoder_guard)
    gemini.reset_health()
    yield seen


@pytest.fixture()
def client():
    return TestClient(main.app)


def ask(client, question, conversation_id="scope"):
    return client.post("/api/ask", json={**ASK, "question": question, "conversation_id": conversation_id})


# --- casual conversation ----------------------------------------------------
@pytest.mark.parametrize("question", CASUAL_QUESTIONS)
def test_casual_messages_get_a_brief_answer(env, client, question):
    body = ask(client, question).json()

    assert body["answered"] is True
    assert body["answer"] == "Groq answer."
    assert set(body) == {"status", "answered", "answer", "conversation_id"}


def test_casual_chat_uses_no_reading_or_chart_context(env, client):
    for index, question in enumerate(CASUAL_QUESTIONS):
        ask(client, question, conversation_id=f"casual-{index}")

    assert env["readings"] == [], "casual chat must not draw a reading"
    assert env["geocoder"] == 0
    assert all(private == "" for private in env["groq"])
    assert all(astrology == "" for astrology in env["astrology"])


# --- out of scope -----------------------------------------------------------
@pytest.mark.parametrize("question", OUT_OF_SCOPE_QUESTIONS)
def test_out_of_scope_gets_the_scope_message(env, client, question):
    body = ask(client, question, conversation_id=f"oos-{question[:10]}").json()

    assert body["answered"] is True
    assert body["answer"] == router.SCOPE_MESSAGE, question
    assert set(body) == {"status", "answered", "answer", "conversation_id"}


def test_out_of_scope_never_reaches_a_provider_or_the_reading(env, client):
    for index, question in enumerate(OUT_OF_SCOPE_QUESTIONS):
        ask(client, question, conversation_id=f"scope-{index}")

    assert env["groq"] == [], "no paid provider call for an unrelated request"
    assert env["gemini"] == []
    assert env["readings"] == []
    assert env["geocoder"] == 0


def test_out_of_scope_never_returns_code(env, client):
    body = ask(client, "write a basic python script to generate a menu", "code-1").json()
    answer = body["answer"]
    assert "def " not in answer and "print(" not in answer and "import " not in answer
    assert "```" not in answer
    assert answer == router.SCOPE_MESSAGE


# --- astrology --------------------------------------------------------------
@pytest.mark.parametrize("question", ASTROLOGY_QUESTIONS)
def test_astrology_questions_use_the_chart_context(env, client, question):
    body = ask(client, question, conversation_id=f"astro-{abs(hash(question))}").json()

    assert body["answered"] is True
    assert body["answer"] == "Groq answer."
    assert env["groq"][-1] == "", "astrology must not carry the Tarot reading"
    assert env["astrology"][-1], "astrology must carry the chart context"
    assert env["readings"] == [], "astrology must not draw a Tarot reading"


def test_astrology_then_astrology_follow_up_stays_astrology(env, client):
    ask(client, "read my kundli", conversation_id="astro-switch")
    assert env["astrology"][-1]

    ask(client, "why?", conversation_id="astro-switch")
    assert env["astrology"][-1], "a follow-up keeps the chart context"
    assert env["groq"][-1] == ""


# --- provider failure -------------------------------------------------------
def test_primary_success_is_used(env, client):
    ask(client, "hi")
    assert env["gemini"] == [], "the fallback must not run when the primary answers"


def test_primary_timeout_reaches_the_fallback(env, client, monkeypatch):
    monkeypatch.setattr("chat.groq.generate_reply_detailed",
                        lambda *a, **k: {"text": None, "provider": "groq", "preferred": groq.MODEL,
                                         "attempts": [{"model": groq.MODEL, "reason": "timeout"}],
                                         "fallback": True})
    body = ask(client, "hi").json()
    assert body["answer"] == "Gemini answer."
    assert env["gemini"], "the fallback must answer when the primary times out"


@pytest.mark.parametrize("reason", ["transient_429", "transient_503", "unavailable"])
def test_primary_429_or_503_reaches_the_fallback(env, client, monkeypatch, reason):
    monkeypatch.setattr("chat.groq.generate_reply_detailed",
                        lambda *a, **k: {"text": None, "provider": "groq", "preferred": groq.MODEL,
                                         "attempts": [{"model": groq.MODEL, "reason": reason}],
                                         "fallback": True})
    body = ask(client, "will my project work?").json()
    assert body["answered"] is True and body["answer"] == "Gemini answer."


def test_both_providers_unavailable_gives_the_friendly_message(env, client, monkeypatch):
    monkeypatch.setattr("chat.groq.generate_reply_detailed",
                        lambda *a, **k: {"text": None, "provider": "groq",
                                         "preferred": groq.MODEL, "attempts": [], "fallback": True})
    monkeypatch.setattr("chat.gemini.generate_reply_detailed",
                        lambda *a, **k: {"text": None, "provider": "gemini",
                                         "preferred": gemini.MODEL_PRIORITY[0], "attempts": []})
    body = ask(client, "hi").json()

    assert body["answered"] is False
    assert body["answer"] == gemini.UNAVAILABLE_MESSAGE
    assert body["status"] == "ok"


def test_provider_chain_is_one_primary_and_one_fallback():
    assert groq.MODEL == "openai/gpt-oss-120b", "one Groq primary"
    assert groq.TIMEOUT_SECONDS <= 20.0
    assert len(gemini.MODEL_PRIORITY) == 2, "one Gemini fallback provider, two viable models"
    assert gemini.PER_ATTEMPT_TIMEOUT <= 15.0
    assert not list((__import__("pathlib").Path(__file__).resolve().parents[1] / "chat").glob("nvidia.py"))


# --- privacy ----------------------------------------------------------------
def test_internal_metadata_and_prompts_are_never_returned(env, client):
    body = json.dumps(ask(client, "what does Saturn mean in my chart?", "private-1").json())

    for forbidden in ("HIDDEN", "reasoning", "PRIVATE READING CONTEXT", "CHART CONTEXT",
                      "system_instruction", "You are Ask KAVACH", "openai/gpt-oss",
                      "gemini-3.5", "attempts", "provider"):
        assert forbidden not in body, forbidden


def test_api_keys_are_never_returned_or_logged(env, client, monkeypatch, caplog):
    monkeypatch.setenv("GROQ_API_KEY", "groq-sentinel-key")
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-sentinel-key")

    records: list[str] = []

    class Capture(logging.Handler):
        def emit(self, record):
            records.append(record.getMessage())

    logger = logging.getLogger("kavach.chat")
    handler = Capture()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    try:
        body = ask(client, "will my startup succeed?", "log-1").text
    finally:
        logger.removeHandler(handler)

    joined = "\n".join(records)
    for secret in ("groq-sentinel-key", "gemini-sentinel-key"):
        assert secret not in body and secret not in joined
    # Logs carry categories only - never the question or the answer text.
    assert "startup" not in joined.lower()
