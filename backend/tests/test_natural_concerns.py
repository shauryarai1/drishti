"""Naturally phrased concerns must work, and dev tracing must never break /ask."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

import chat.gemini as gemini
import chat.session as session
import chat.trace as trace


@pytest.fixture(autouse=True)
def _pin_primary_provider_off(monkeypatch):
    """These tests assert the Gemini contract; keep the primary provider out of the way."""
    monkeypatch.setattr(
        "chat.nvidia.generate_reply_detailed",
        lambda *args, **kwargs: {"text": None, "model": None, "preferred": None, "attempts": []},
    )

REPLY = "That sounds draining, and there are a few likely reasons this is happening."

NATURAL_CONCERNS = (
    "I am working continuously but not getting any clients",
    "My business isn't growing",
    "I keep studying but my marks aren't improving",
    "Things have been difficult at work lately",
    "I haven't heard back from her",
)

ASK = {"timestamp": "2026-09-26T10:00:00+05:30", "latitude": 28.6139, "longitude": 77.209,
       "timezone": "Asia/Kolkata", "location_label": "New Delhi"}


class Response:
    status_code = 200
    text = ""

    def json(self):
        return {"steps": [{"type": "model_output", "content": [{"type": "text", "text": REPLY}]}]}


def _stub(monkeypatch, status: int = 200, body: str = "{}"):
    calls = []

    def fake_post(url, **kwargs):
        calls.append(kwargs["json"])
        if status != 200:
            response = Response()
            response.status_code = status
            response.text = body
            return response
        return Response()

    monkeypatch.setattr(gemini.httpx, "post", fake_post)
    return calls


def _ask(question, conversation_id):
    return TestClient(__import__("main").app).post(
        "/api/ask", json={**ASK, "question": question, "conversation_id": conversation_id}).json()


# --- 9/10: natural concerns go through the real pipeline -------------------
def test_exact_clients_concern_full_pipeline_with_mocked_gemini(monkeypatch):
    calls = _stub(monkeypatch)
    session.reset("natural-1")
    trace.clear("natural-1")
    question = "I am working continuously but not getting any clients"

    body = _ask(question, "natural-1")
    assert body["status"] == "ok"
    assert body["answered"] is True
    assert body["answer"] == REPLY
    assert len(calls) == 1

    reading = session.get_reading("natural-1")
    assert reading is not None
    assert len(reading["cards"]) == 3
    assert all(card["orientation"] in ("upright", "reversed") for card in reading["cards"])
    assert any(item.get("reading") for item in reading["interpretations"])

    event = trace.list_events("natural-1")[0]
    sent = calls[0]["input"]
    assert "[PRIVATE KAVACH READING" in sent
    assert event["draw"]["after"] == reading["draw_id"]
    assert [card["card_id"] for card in event["cards"]] == [card["card_id"] for card in reading["cards"]]
    assert event["pipeline"]["status"] == "ok"


def test_clients_concern_context_is_career_like():
    from chat.reading import build_reading

    context = build_reading("I am working continuously but not getting any clients")["context"]
    assert context["domain"] in ("career", "money", "general")
    assert context["subcontext"]


def test_natural_concerns_do_not_crash(monkeypatch):
    _stub(monkeypatch)
    for index, question in enumerate(NATURAL_CONCERNS):
        conversation = f"natural-many-{index}"
        session.reset(conversation)
        trace.clear(conversation)
        body = _ask(question, conversation)
        assert body["status"] == "ok", question
        assert body["answered"] is True, question
        assert session.get_reading(conversation) is not None
        assert len(trace.list_events(conversation)) == 1


# --- 5: tracing is fail-safe ----------------------------------------------
def test_trace_failure_never_breaks_the_public_answer(monkeypatch):
    _stub(monkeypatch)

    def exploding(*args, **kwargs):
        raise RuntimeError("dev trace exploded")

    monkeypatch.setattr("chat.trace.record_event", exploding)
    session.reset("safety-1")
    body = _ask("Should I become an engineer?", "safety-1")
    assert body["status"] == "ok"
    assert body["answered"] is True
    assert body["answer"] == REPLY


def test_record_event_itself_swallows_errors(monkeypatch):
    import chat.reading as reading_module

    monkeypatch.setattr(reading_module, "private_context", lambda value: (_ for _ in ()).throw(RuntimeError("boom")))
    result = trace.record_event("swallow-1", question="q", reading={"draw_id": "x", "cards": [], "interpretations": []},
                                reused=False, before=None, model={}, raw=None, public=None)
    assert result is None


# --- 6/7/8: failed generations are still inspectable ----------------------
def test_quota_failure_keeps_reading_and_trace(monkeypatch):
    _stub(monkeypatch, status=429, body='{"error":{"message":"quota"}}')
    session.reset("quota-1")
    trace.clear("quota-1")
    body = _ask("I am working continuously but not getting any clients", "quota-1")
    assert body["answered"] is False
    assert body["answer"] == gemini.UNAVAILABLE_MESSAGE

    event = trace.list_events("quota-1")[0]
    assert event["pipeline"]["status"] == "model_unavailable"
    assert event["pipeline"]["stage"] == "generation"
    assert len(event["cards"]) == 3
    assert event["private_context"]
    assert event["model"]["actual"] is None
    assert len(event["model"]["attempts"]) == len(gemini.MODEL_PRIORITY)

    client = TestClient(__import__("main").app)
    fetched = client.post("/api/dev/kavach-trace", json={"conversation_id": "quota-1"}).json()
    assert fetched["draw"]["after"] == event["draw"]["after"]
    assert fetched["pipeline"]["status"] == "model_unavailable"
    assert session.get_history("quota-1") == []


def test_inspector_retrieval_matches_public_draw(monkeypatch):
    _stub(monkeypatch)
    session.reset("match-1")
    trace.clear("match-1")
    _ask("I am working continuously but not getting any clients", "match-1")
    stored = session.get_reading("match-1")
    client = TestClient(__import__("main").app)
    ids = set()
    for _ in range(4):
        fetched = client.post("/api/dev/kavach-trace", json={"conversation_id": "match-1", "index": 1}).json()
        ids.add(fetched["draw"]["after"])
        assert [card["card_id"] for card in fetched["cards"]] == [card["card_id"] for card in stored["cards"]]
        assert [card["orientation"] for card in fetched["cards"]] == [card["orientation"] for card in stored["cards"]]
    assert ids == {stored["draw_id"]}


def test_trace_has_no_secret_fields_or_values(monkeypatch):
    _stub(monkeypatch)
    session.reset("secret-1")
    trace.clear("secret-1")
    _ask("I am working continuously but not getting any clients", "secret-1")
    event = trace.list_events("secret-1")[0]

    def keys(node):
        found = set()
        if isinstance(node, dict):
            for key, value in node.items():
                found.add(str(key).lower())
                found |= keys(value)
        elif isinstance(node, list):
            for item in node:
                found |= keys(item)
        return found

    present = keys(event)
    for banned in ("api_key", "apikey", "gemini_api_key", "authorization", "x-goog-api-key",
                   "headers", "env", "environ", "secret", "token", "password", "credential"):
        assert banned not in present, banned

    blob = json.dumps(event)
    key = gemini.api_key()
    if key:
        assert key not in blob
