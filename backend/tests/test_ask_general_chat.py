"""Ask KAVACH behaviour: general conversation, astrology routing, provider failure.

Providers are mocked - no live quota. The archive is isolated by conftest.
"""

from __future__ import annotations

import json
import logging
import pathlib

import pytest
from fastapi.testclient import TestClient

import archive
import chat.gemini as gemini
import chat.nvidia as nvidia
import main

REPO = pathlib.Path(__file__).resolve().parents[2]
ASK = {"timestamp": "2026-09-22T11:45:00+05:30", "latitude": 28.6139, "longitude": 77.209,
       "timezone": "Asia/Kolkata"}
GENERAL_QUESTIONS = ["hi", "how are you?", "what is gravity?", "explain photosynthesis",
                     "write an email to my teacher", "give me study tips", "will my project work?"]
ASTROLOGY_QUESTIONS = ["read my kundli", "what does Saturn mean in my chart?",
                       "how is my week astrologically?",
                       "what should I be cautious about according to my chart?"]


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
    seen: dict = {"nvidia": [], "gemini": [], "geocoder": 0, "inserts": 0}

    monkeypatch.setattr(archive, "store", FakeStore())
    monkeypatch.setattr("chat.reading.sensitive_response", lambda _q: None)
    monkeypatch.setattr("chat.reading.build_reading", lambda _q: {"draw_id": "d1", "interpretations": [
        {"reading": "context"}]})
    monkeypatch.setattr("chat.reading.private_context", lambda _r: "PRIVATE CONTEXT")

    def fake_nvidia(_q, _h, private_context=""):
        seen["nvidia"].append(bool(private_context))
        return {"text": "NVIDIA answer.", "model": nvidia.primary_model(), "preferred": nvidia.primary_model(),
                "provider": "nvidia", "attempts": [{"model": nvidia.primary_model(), "reason": "ok"}],
                "fallback": False, "reasoning_content": "HIDDEN"}

    def fake_gemini(_q, _h, private_context=""):
        seen["gemini"].append(bool(private_context))
        return {"text": "Gemini answer.", "model": "gemini-3.5-flash-lite", "preferred": "gemini-3.5-flash-lite",
                "provider": "gemini", "attempts": []}

    monkeypatch.setattr("chat.nvidia.generate_reply_detailed", fake_nvidia)
    monkeypatch.setattr("chat.gemini.generate_reply_detailed", fake_gemini)

    import geocoding

    def geocoder_guard(_query, _limit):
        seen["geocoder"] += 1
        raise AssertionError("Ask KAVACH must never call the geocoder")

    monkeypatch.setattr(geocoding, "_provider_search", geocoder_guard)
    gemini.reset_health()
    yield seen


def ask(client, question, conversation_id="general"):
    return client.post("/api/ask", json={**ASK, "question": question, "conversation_id": conversation_id})


@pytest.fixture()
def client():
    return TestClient(main.app)


# --- general chat -----------------------------------------------------------
@pytest.mark.parametrize("question", GENERAL_QUESTIONS)
def test_general_questions_get_a_normal_answer(env, client, question):
    body = ask(client, question).json()

    assert body["answered"] is True
    assert body["answer"] == "NVIDIA answer."
    assert set(body) == {"status", "answered", "answer", "conversation_id"}


def test_general_chat_uses_no_astrology_context_and_no_geocoder(env, client):
    for index, question in enumerate(GENERAL_QUESTIONS):
        ask(client, question, conversation_id=f"general-{index}")

    assert env["geocoder"] == 0, "ordinary conversation must never geocode"
    assert env["nvidia"], "the primary provider should have been used"
    assert all(private is False for private in env["nvidia"]), "no private astrology context for general chat"


def test_general_chat_needs_no_birth_details(env, client):
    """No birth date/time/place/coordinates may be required."""
    response = client.post("/api/ask", json={"question": "what is gravity?",
                                             "timestamp": "2026-09-22T11:45:00+05:30",
                                             "conversation_id": "no-birth-details"})
    assert response.status_code == 200
    assert response.json()["answer"] == "NVIDIA answer."


# --- astrology chat ---------------------------------------------------------
@pytest.mark.parametrize("question", ASTROLOGY_QUESTIONS)
def test_astrology_questions_use_the_kavach_context(env, client, question):
    body = ask(client, question, conversation_id=f"astro-{question[:12]}").json()

    assert body["answered"] is True
    assert env["nvidia"][-1] is True, "astrology questions must carry the private context"


def test_astrology_follow_up_stays_in_context_then_general_returns(env, client):
    ask(client, "read my kundli", conversation_id="switch")
    assert env["nvidia"][-1] is True

    ask(client, "what about Jupiter?", conversation_id="switch")
    assert env["nvidia"][-1] is True, "an astrology follow-up keeps the context"

    ask(client, "thanks. Now explain gravity.", conversation_id="switch")
    assert env["nvidia"][-1] is False, "an unrelated question returns to general chat"


# --- provider failure -------------------------------------------------------
def test_primary_success_is_used(env, client):
    ask(client, "what is gravity?")
    assert env["gemini"] == [], "the fallback must not run when the primary answers"


def test_primary_timeout_reaches_the_fallback(env, client, monkeypatch):
    monkeypatch.setattr("chat.nvidia.generate_reply_detailed",
                        lambda *a, **k: {"text": None, "provider": "nvidia", "preferred": nvidia.primary_model(),
                                         "attempts": [{"model": nvidia.primary_model(), "reason": "timeout"}],
                                         "fallback": True})
    body = ask(client, "what is gravity?").json()
    assert body["answer"] == "Gemini answer."
    assert env["gemini"], "the fallback must answer when the primary times out"


@pytest.mark.parametrize("reason", ["transient_429", "transient_503", "unavailable"])
def test_primary_429_or_503_reaches_the_fallback(env, client, monkeypatch, reason):
    monkeypatch.setattr("chat.nvidia.generate_reply_detailed",
                        lambda *a, **k: {"text": None, "provider": "nvidia", "preferred": nvidia.primary_model(),
                                         "attempts": [{"model": nvidia.primary_model(), "reason": reason}],
                                         "fallback": True})
    body = ask(client, "explain photosynthesis").json()
    assert body["answered"] is True and body["answer"] == "Gemini answer."


def test_both_providers_unavailable_gives_the_friendly_message(env, client, monkeypatch):
    monkeypatch.setattr("chat.nvidia.generate_reply_detailed",
                        lambda *a, **k: {"text": None, "provider": "nvidia",
                                         "preferred": nvidia.primary_model(), "attempts": [], "fallback": True})
    monkeypatch.setattr("chat.gemini.generate_reply_detailed",
                        lambda *a, **k: {"text": None, "provider": "gemini",
                                         "preferred": gemini.MODEL_PRIORITY[0], "attempts": []})
    body = ask(client, "what is gravity?").json()

    assert body["answered"] is False
    assert body["answer"] == gemini.UNAVAILABLE_MESSAGE
    assert body["status"] == "ok"


def test_provider_chain_is_one_primary_and_one_fallback():
    assert len(nvidia.MODEL_REGISTRY) == 1, "one NVIDIA primary only"
    assert nvidia.MAX_ATTEMPTS == 1
    assert len(gemini.MODEL_PRIORITY) == 2, "one Gemini fallback provider, two viable models"
    assert nvidia.TOTAL_BUDGET_SECONDS <= 15.0
    assert gemini.PER_ATTEMPT_TIMEOUT <= 15.0


# --- privacy ----------------------------------------------------------------
def test_internal_metadata_and_prompts_are_never_returned(env, client):
    body = json.dumps(ask(client, "what is gravity?").json())

    for forbidden in ("HIDDEN", "reasoning", "PRIVATE CONTEXT", "system_instruction",
                      "You are Ask KAVACH", "nvidia/nemotron", "gemini-3.5", "attempts", "provider"):
        assert forbidden not in body, forbidden


def test_api_keys_are_never_returned_or_logged(env, client, monkeypatch, caplog):
    monkeypatch.setenv("NVIDIA_API_KEY", "nvidia-sentinel-key")
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
        body = ask(client, "what is gravity?").text
    finally:
        logger.removeHandler(handler)

    joined = "\n".join(records)
    for secret in ("nvidia-sentinel-key", "gemini-sentinel-key"):
        assert secret not in body and secret not in joined
    # Logs carry categories only - never the question or the answer text.
    assert "gravity" not in joined.lower()
    assert "NVIDIA answer." not in joined
