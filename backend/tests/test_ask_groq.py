"""Ask KAVACH primary provider: Groq `openai/gpt-oss-120b`, Gemini as fallback.

Groq HTTP is always mocked - no automated test consumes real Groq quota.
"""

from __future__ import annotations

import json
import logging
import pathlib

import httpx
import pytest
from fastapi.testclient import TestClient

import archive
import chat.gemini as gemini
import chat.groq as groq
import main

REPO = pathlib.Path(__file__).resolve().parents[2]
ASK = {"timestamp": "2026-09-22T11:45:00+05:30", "latitude": 28.6139, "longitude": 77.209,
       "timezone": "Asia/Kolkata"}
FAKE_KEY = "groq-test-key-never-real"
REASONING = "HIDDEN MODEL REASONING that must never surface"


class FakeResponse:
    def __init__(self, status_code: int = 200, payload=None, malformed: bool = False, headers=None):
        self.status_code = status_code
        self._payload = payload
        self._malformed = malformed
        self.headers = headers or {}

    def json(self):
        if self._malformed:
            raise ValueError("not json")
        return self._payload


def groq_payload(content: str = "Here is a helpful answer.", reasoning: str | None = None) -> dict:
    message = {"role": "assistant", "content": content}
    if reasoning is not None:
        message["reasoning_content"] = reasoning
    return {"choices": [{"index": 0, "message": message, "finish_reason": "stop"}]}


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
    """Record every Groq request; mock Gemini; guard the geocoder."""
    seen: dict = {"groq": [], "gemini": [], "geocoder": 0}
    script = {"response": FakeResponse(200, groq_payload())}

    def fake_groq_post(url, headers=None, json=None, timeout=None):  # noqa: A002
        seen["groq"].append({"url": url, "messages": (json or {}).get("messages"),
                             "model": (json or {}).get("model"), "timeout": timeout,
                             "auth": (headers or {}).get("Authorization")})
        item = script["response"]
        if isinstance(item, Exception):
            raise item
        return item

    monkeypatch.setattr(groq.httpx, "post", fake_groq_post)
    monkeypatch.setenv("GROQ_API_KEY", FAKE_KEY)

    def fake_gemini(*_a, **_k):
        seen["gemini"].append(1)
        return {"text": "Gemini emergency answer.", "model": "gemini-3.5-flash-lite",
                "preferred": "gemini-3.5-flash-lite", "provider": "gemini", "attempts": []}

    monkeypatch.setattr("chat.gemini.generate_reply_detailed", fake_gemini)
    monkeypatch.setattr(archive, "store", FakeStore())
    monkeypatch.setattr("chat.reading.sensitive_response", lambda _q: None)
    monkeypatch.setattr("chat.reading.build_reading",
                        lambda _q: {"draw_id": "d1", "interpretations": [{"reading": "ctx"}]})
    monkeypatch.setattr("chat.reading.private_context", lambda _r: "PRIVATE READING CONTEXT")

    import geocoding

    def geocoder_guard(_query, _limit):
        seen["geocoder"] += 1
        raise AssertionError("Ask KAVACH must never call the geocoder")

    monkeypatch.setattr(geocoding, "_provider_search", geocoder_guard)
    return {"seen": seen, "script": script}


@pytest.fixture()
def client():
    return TestClient(main.app)


def ask(client, question, conversation_id="groq-1"):
    return client.post("/api/ask", json={**ASK, "question": question, "conversation_id": conversation_id})


# --- 1/2/3/4/5: behaviour ----------------------------------------------------
def test_general_question_answered_by_groq(env, client):
    body = ask(client, "what is gravity?").json()

    assert body["answered"] is True
    assert body["answer"] == "Here is a helpful answer."
    assert len(env["seen"]["groq"]) == 1
    assert env["seen"]["groq"][0]["model"] == "openai/gpt-oss-120b"
    assert env["seen"]["groq"][0]["url"] == groq.ENDPOINT
    assert env["seen"]["groq"][0]["auth"] == f"Bearer {FAKE_KEY}"


def test_general_question_carries_no_astrology_context(env, client):
    from chat.gemini import READING_INSTRUCTION, SYSTEM_INSTRUCTION

    ask(client, "explain photosynthesis")
    request = env["seen"]["groq"][0]

    assert SYSTEM_INSTRUCTION in request["messages"][0]["content"]
    assert READING_INSTRUCTION not in request["messages"][0]["content"]
    assert "PRIVATE READING CONTEXT" not in json.dumps(request["messages"])


def test_astrology_question_carries_the_kavach_context(env, client):
    from chat.gemini import READING_INSTRUCTION

    ask(client, "what does Saturn mean in my chart?")
    request = env["seen"]["groq"][0]

    assert READING_INSTRUCTION in request["messages"][0]["content"]
    assert "PRIVATE READING CONTEXT" in request["messages"][-1]["content"]


def test_astrology_follow_up_keeps_context_then_general_returns(env, client):
    ask(client, "read my kundli", conversation_id="switch")
    assert "PRIVATE READING CONTEXT" in env["seen"]["groq"][-1]["messages"][-1]["content"]

    ask(client, "what about Jupiter?", conversation_id="switch")
    assert "PRIVATE READING CONTEXT" in env["seen"]["groq"][-1]["messages"][-1]["content"]

    ask(client, "thanks. Now explain gravity.", conversation_id="switch")
    assert "PRIVATE READING CONTEXT" not in env["seen"]["groq"][-1]["messages"][-1]["content"]


def test_general_chat_never_touches_astrology_or_the_geocoder(env, client):
    for index, question in enumerate(("hi", "how are you?", "what is gravity?",
                                      "write an email", "help me study", "will my project work?")):
        ask(client, question, conversation_id=f"general-{index}")

    assert env["seen"]["geocoder"] == 0
    assert all("PRIVATE READING CONTEXT" not in json.dumps(item["messages"])
               for item in env["seen"]["groq"])


# --- 6/7/8/9/10/11: provider failure ----------------------------------------
def test_groq_success_does_not_call_gemini(env, client):
    ask(client, "what is gravity?")
    assert env["seen"]["gemini"] == [], "the fallback must not run when Groq answers"


def test_groq_timeout_falls_back_to_gemini_once(env, client):
    env["script"]["response"] = httpx.TimeoutException("slow")
    body = ask(client, "what is gravity?").json()

    assert body["answer"] == "Gemini emergency answer."
    assert env["seen"]["gemini"] == [1], "the fallback runs exactly once"
    assert len(env["seen"]["groq"]) == 1, "a failed Groq request is never retried"


def test_groq_429_falls_back_to_gemini_once(env, client):
    env["script"]["response"] = FakeResponse(429, {"error": "rate limited"},
                                             headers={"retry-after": "7"})
    body = ask(client, "what is gravity?").json()

    assert body["answer"] == "Gemini emergency answer."
    assert env["seen"]["gemini"] == [1]
    assert len(env["seen"]["groq"]) == 1


def test_groq_5xx_falls_back_to_gemini_once(env, client):
    env["script"]["response"] = FakeResponse(503, {"error": "overloaded"})
    body = ask(client, "what is gravity?").json()

    assert body["answer"] == "Gemini emergency answer."
    assert env["seen"]["gemini"] == [1]


def test_groq_malformed_response_falls_back_safely(env, client):
    env["script"]["response"] = FakeResponse(200, malformed=True)
    body = ask(client, "what is gravity?").json()

    assert body["answer"] == "Gemini emergency answer."
    assert env["seen"]["gemini"] == [1]


def test_both_providers_unavailable_gives_the_friendly_error(env, client, monkeypatch):
    env["script"]["response"] = FakeResponse(500, {"error": "down"})
    monkeypatch.setattr("chat.gemini.generate_reply_detailed",
                        lambda *a, **k: {"text": None, "provider": "gemini",
                                         "preferred": gemini.MODEL_PRIORITY[0], "attempts": []})

    body = ask(client, "what is gravity?").json()

    assert body["answered"] is False
    assert body["answer"] == gemini.UNAVAILABLE_MESSAGE
    assert body["status"] == "ok"


def test_missing_groq_key_falls_back_without_calling_out(env, client, monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    body = ask(client, "what is gravity?").json()

    assert body["answer"] == "Gemini emergency answer."
    assert env["seen"]["groq"] == [], "no request may be attempted without a key"


# --- 12/13: no other providers ----------------------------------------------
def test_nvidia_is_removed_from_the_active_path():
    assert not (REPO / "backend" / "chat" / "nvidia.py").exists(), "the NVIDIA provider was removed"
    assert not (REPO / "backend" / "tests" / "test_nvidia_router.py").exists()
    text = (REPO / "backend" / "main.py").read_text(encoding="utf-8")
    assert "chat.nvidia" not in text and "chat.groq" in text


def test_no_geocoder_request_for_any_ask_traffic(env, client):
    ask(client, "read my kundli")
    ask(client, "what is gravity?")
    assert env["seen"]["geocoder"] == 0


# --- 14/15/16/17: privacy ---------------------------------------------------
def test_api_key_never_returned_or_logged(env, client):
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
    assert FAKE_KEY not in body and FAKE_KEY not in joined
    assert "gravity" not in joined.lower(), "questions are never logged"
    assert "Here is a helpful answer." not in joined, "answer text is never logged"


def test_system_prompt_and_reasoning_are_never_exposed(env, client):
    env["script"]["response"] = FakeResponse(200, groq_payload("Public answer.", reasoning=REASONING))
    body = json.dumps(ask(client, "what is gravity?").json())

    assert "Public answer." in body
    assert REASONING not in body
    for forbidden in ("reasoning", "You are Ask KAVACH", "system", "gpt-oss", "provider", "attempts"):
        assert forbidden not in body.lower(), forbidden


def test_reasoning_is_never_archived(env, client):
    env["script"]["response"] = FakeResponse(200, groq_payload("Archived answer.", reasoning=REASONING))
    ask(client, "read my kundli")

    row = archive.store.rows[0]
    assert row["product"] == "ask"
    assert row["result_data"] == {"answered": True, "answer": "Archived answer."}
    assert REASONING not in json.dumps(row)
    assert FAKE_KEY not in json.dumps(row)
    assert "PRIVATE READING CONTEXT" not in json.dumps(row)


def test_observability_logs_are_safe_and_useful(env, client):
    records: list[str] = []

    class Capture(logging.Handler):
        def emit(self, record):
            records.append(record.getMessage())

    logger = logging.getLogger("kavach.chat")
    handler = Capture()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    try:
        ask(client, "what is gravity?")
    finally:
        logger.removeHandler(handler)

    joined = "\n".join(records)
    assert "provider=groq" in joined
    assert "model=openai/gpt-oss-120b" in joined
    assert "outcome=success" in joined and "elapsed_ms=" in joined
    assert "fallback_used=false" in joined


# --- configuration ----------------------------------------------------------
def test_provider_chain_is_exactly_one_primary_and_one_fallback():
    assert groq.MODEL == "openai/gpt-oss-120b"
    assert groq.ENDPOINT == "https://api.groq.com/openai/v1/chat/completions"
    assert groq.TIMEOUT_SECONDS <= 20.0, "users must not wait 30-60s"
    assert len(gemini.MODEL_PRIORITY) == 2
    assert gemini.PER_ATTEMPT_TIMEOUT <= 15.0
