"""Simplified Ask KAVACH chat-first pipeline.

NORMAL_CHAT      : history + message -> Gemini (Tarot never touched)
NEW_READING      : one local draw + approved meanings -> Gemini (private)
READING_FOLLOWUP : history + existing reading -> Gemini (no redraw)

Tarot, inspector and dev tracing are optional: any failure in them must leave
normal conversation working.
"""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

import chat.gemini as gemini
import chat.router as router
import chat.session as session
import chat.trace as trace


@pytest.fixture(autouse=True)
def _pin_primary_provider_off(monkeypatch):
    """These tests assert the Gemini request contract, so the primary provider is pinned off."""
    monkeypatch.setattr(
        "chat.groq.generate_reply_detailed",
        lambda *args, **kwargs: {"text": None, "model": None, "preferred": None, "attempts": []},
    )


REPLY = "Here is a natural conversational reply."

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


# --- 4: routing -----------------------------------------------------------
@pytest.mark.parametrize("message", ["hi", "what", "I'm sad", "thanks", "how are you",
                                     "I am working continuously but not getting any clients",
                                     "What is marketing?", "I don't understand", "tell me more"])
def test_normal_chat_routing(message):
    assert router.route_message(message, has_active_reading=False) == router.NORMAL_CHAT


@pytest.mark.parametrize("message", ["How will my business go as per my chart?", "Should I open my shop on Friday as per my chart?",
                                     "How will my exam go tomorrow as per my chart?", "Will this opportunity work out as per my chart?",
                                     "What does KAVACH say about my career right now?",
                                     "Give me a reading about my relationship."])
def test_reading_routing(message):
    assert router.route_message(message, has_active_reading=False) == router.NEW_READING


@pytest.mark.parametrize("message", ["why?", "are you sure?", "explain", "what does that mean?",
                                     "what should I do then?", "but why?", "what if I wait?",
                                     "tell me more"])
def test_follow_up_routing(message):
    assert router.route_message(message, has_active_reading=True) == router.READING_FOLLOWUP


# --- 5/21: NORMAL_CHAT never touches Tarot --------------------------------
def test_normal_chat_never_draws(monkeypatch):
    calls = _stub(monkeypatch)
    draws = []

    def spy(*args, **kwargs):
        draws.append(1)
        raise AssertionError("Tarot must not run for normal chat")

    monkeypatch.setattr("tarot.engine.draw_cards", spy)
    monkeypatch.setattr("chat.reading.draw_cards", spy)

    for index, message in enumerate(("hi", "what", "I'm sad",
                                     "I am working continuously but not getting any clients")):
        conversation = f"chat-{index}"
        session.reset(conversation)
        trace.clear(conversation)
        body = _ask(message, conversation)
        assert body["answered"] is True, message
        assert body["answer"] == REPLY
        assert session.get_reading(conversation) is None
        event = trace.list_events(conversation)[0]
        assert event["route"] == router.NORMAL_CHAT
        assert event["tarot"] == "NOT USED"
    assert draws == []
    assert len(calls) == 4


def test_normal_chat_uses_no_private_context(monkeypatch):
    calls = _stub(monkeypatch)
    session.reset("chat-ctx")
    _ask("hi", "chat-ctx")
    assert "PRIVATE KAVACH READING" not in calls[0]["input"]


# --- 6/21: NEW_READING draws exactly once ---------------------------------
def test_new_reading_draws_exactly_once(monkeypatch):
    _stub(monkeypatch)
    original = __import__("tarot.engine", fromlist=["draw_cards"]).draw_cards
    draws = []

    def spy(*args, **kwargs):
        draws.append(1)
        return original(*args, **kwargs)

    monkeypatch.setattr("chat.reading.draw_cards", spy)
    session.reset("reading-1")
    trace.clear("reading-1")
    body = _ask("Should I open my shop on Friday as per my chart?", "reading-1")
    assert body["answered"] is True
    assert len(draws) == 1
    reading = session.get_reading("reading-1")
    assert reading is not None
    assert len(reading["cards"]) == 3
    assert len(set(card["card_id"] for card in reading["cards"])) == 3
    event = trace.list_events("reading-1")[0]
    assert event["route"] == router.NEW_READING
    assert event["tarot"] == "USED"
    assert len(event["cards"]) == 3


# --- 7/21: follow-up reuses, new question draws again ---------------------
def test_follow_up_reuses_and_new_question_draws(monkeypatch):
    _stub(monkeypatch)
    session.reset("reading-2")
    trace.clear("reading-2")
    first = _ask("Should I open my shop on Friday as per my chart?", "reading-2")
    assert first["answered"] is True
    draw_a = session.get_reading("reading-2")["draw_id"]
    cards_a = [card["card_id"] for card in session.get_reading("reading-2")["cards"]]

    follow = _ask("why?", "reading-2")
    assert follow["answered"] is True
    assert session.get_reading("reading-2")["draw_id"] == draw_a
    assert [card["card_id"] for card in session.get_reading("reading-2")["cards"]] == cards_a

    again = _ask("How will my exam go tomorrow as per my chart?", "reading-2")
    assert again["answered"] is True
    assert session.get_reading("reading-2")["draw_id"] != draw_a

    events = trace.list_events("reading-2")
    assert [event["route"] for event in events] == [router.NEW_READING,
                                                    router.READING_FOLLOWUP,
                                                    router.NEW_READING]
    assert events[1]["tarot"] == "REUSED"
    assert events[1]["draw"]["after"] == events[0]["draw"]["after"]


def test_subject_change_then_normal_chat(monkeypatch):
    _stub(monkeypatch)
    session.reset("reading-3")
    trace.clear("reading-3")
    _ask("How will my exam go as per my chart?", "reading-3")
    _ask("why?", "reading-3")
    _ask("okay thanks", "reading-3")
    _ask("what is photosynthesis?", "reading-3")
    routes = [event["route"] for event in trace.list_events("reading-3")]
    assert routes == [router.NEW_READING, router.READING_FOLLOWUP,
                      router.NORMAL_CHAT, router.NORMAL_CHAT]


# --- 8/9/10: error boundaries --------------------------------------------
def test_tarot_crash_does_not_break_normal_chat(monkeypatch):
    _stub(monkeypatch)

    def exploding(*args, **kwargs):
        raise RuntimeError("tarot exploded")

    monkeypatch.setattr("chat.reading.build_reading", exploding)
    session.reset("bound-1")
    body = _ask("hi", "bound-1")
    assert body["answered"] is True
    assert body["answer"] == REPLY


def test_tarot_crash_falls_back_to_normal_chat(monkeypatch):
    _stub(monkeypatch)

    def exploding(*args, **kwargs):
        raise RuntimeError("tarot exploded")

    monkeypatch.setattr("chat.reading.build_reading", exploding)
    session.reset("bound-2")
    trace.clear("bound-2")
    body = _ask("Should I open my shop on Friday as per my chart?", "bound-2")
    assert body["status"] == "ok"
    assert body["answered"] is True
    assert session.get_reading("bound-2") is None
    assert trace.list_events("bound-2")[0]["tarot"] == "NOT USED"


def test_inspector_crash_does_not_break_chat(monkeypatch):
    _stub(monkeypatch)

    def exploding(*args, **kwargs):
        raise RuntimeError("inspector exploded")

    monkeypatch.setattr("chat.inspector._card_payload", exploding)
    session.reset("bound-3")
    body = _ask("Should I open my shop on Friday as per my chart?", "bound-3")
    assert body["answered"] is True


def test_trace_crash_does_not_break_chat(monkeypatch):
    _stub(monkeypatch)

    def exploding(*args, **kwargs):
        raise RuntimeError("trace exploded")

    monkeypatch.setattr("chat.trace.record_event", exploding)
    session.reset("bound-4")
    body = _ask("hi", "bound-4")
    assert body["answered"] is True
    assert body["answer"] == REPLY


def test_model_unavailable_keeps_reading_for_inspection(monkeypatch):
    _stub(monkeypatch, status=429, body='{"error":{"message":"quota"}}')
    session.reset("bound-5")
    trace.clear("bound-5")
    body = _ask("Should I open my shop on Friday as per my chart?", "bound-5")
    assert body["answered"] is False
    assert body["answer"] == gemini.UNAVAILABLE_MESSAGE
    event = trace.list_events("bound-5")[0]
    assert event["route"] == router.NEW_READING
    assert len(event["cards"]) == 3
    assert event["pipeline"]["status"] == "model_unavailable"


# --- 11: public contract --------------------------------------------------
def test_public_contract_unchanged(monkeypatch):
    _stub(monkeypatch)
    session.reset("contract-1")
    body = _ask("Should I open my shop on Friday as per my chart?", "contract-1")
    assert set(body) == {"status", "answered", "answer", "conversation_id"}
    blob = json.dumps(body).lower()
    for banned in ("card", "draw", "tarot", "route", "model", "reading"):
        assert banned not in blob, banned
