"""Router intent tests: personal interpretative questions must create a reading."""

from __future__ import annotations

import json
from collections import Counter

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
        "chat.nvidia.generate_reply_detailed",
        lambda *args, **kwargs: {"text": None, "model": None, "preferred": None, "attempts": []},
    )


REPLY = "Here is a natural conversational reply."
ASK = {"timestamp": "2026-09-26T12:00:00+05:30", "latitude": 28.6139, "longitude": 77.209,
       "timezone": "Asia/Kolkata", "location_label": "New Delhi"}
EXACT = "I am continuously working but not getting any clients why?"


class Response:
    status_code = 200
    text = ""

    def json(self):
        return {"steps": [{"type": "model_output", "content": [{"type": "text", "text": REPLY}]}]}


def _stub(monkeypatch):
    calls = []

    def fake_post(url, **kwargs):
        calls.append(kwargs["json"])
        return Response()

    monkeypatch.setattr(gemini.httpx, "post", fake_post)
    return calls


def _ask(question, conversation_id):
    return TestClient(__import__("main").app).post(
        "/api/ask", json={**ASK, "question": question, "conversation_id": conversation_id}).json()


# --- NEW_READING: personal interpretation ---------------------------------
@pytest.mark.parametrize("message", [
    EXACT,
    "Why am I not getting clients?",
    "Why is my business not growing?",
    "Why am I stuck in my career?",
    "What is blocking my progress?",
    "Why do I keep facing the same problem?",
    "Why is my business not growing even though I am trying?",
    "Why do I keep facing problems at work?",
    "Why am I struggling despite putting in effort?",
    "What is going wrong in my business?",
    "What should I focus on right now?",
    "Why am I not seeing results?",
    "Should I open my shop on Friday?",
    "Will I pass my exam?",
    "How will my interview go?",
    "How will my business go?",
    "Will she accept me?",
    "What does KAVACH say about my career right now?",
    "Give me a reading about my relationship.",
])
def test_personal_interpretation_is_a_new_reading(message):
    assert router.route_message(message, has_active_reading=False) == router.NEW_READING, message


# --- NORMAL_CHAT: statements, facts, practical advice ---------------------
@pytest.mark.parametrize("message", [
    "I am not getting clients.",
    "What are common reasons businesses don't get clients?",
    "How can I get more clients?",
    "How can I market my business?",
    "Give me ways to find clients.",
    "What is marketing?",
    "What is engineering?",
    "Explain SEO",
    "How do I make an Instagram ad?",
    "I'm sad.",
    "hi",
    "thanks",
    "what?",
    "How are you?",
])
def test_ordinary_conversation_is_not_a_reading(message):
    assert router.route_message(message, has_active_reading=False) == router.NORMAL_CHAT, message


# --- READING_FOLLOWUP while a reading is active ---------------------------
@pytest.mark.parametrize("message", ["why?", "tell me more", "what do you mean?",
                                     "what should I do then?", "will it improve?",
                                     "so what should I change?"])
def test_follow_ups_stay_on_the_reading(message):
    assert router.route_message(message, has_active_reading=True) == router.READING_FOLLOWUP, message


def test_new_subject_during_a_reading_starts_a_new_one():
    assert router.route_message("How will my exam go tomorrow?", has_active_reading=True) == router.NEW_READING


# --- the exact clients question, end to end (Gemini mocked) ---------------
def test_exact_clients_question_creates_one_real_reading(monkeypatch):
    calls = _stub(monkeypatch)
    session.reset("intent-1")
    trace.clear("intent-1")

    body = _ask(EXACT, "intent-1")
    assert body["status"] == "ok"
    assert body["answered"] is True
    assert body["answer"] == REPLY
    assert "card" not in json.dumps(body).lower()
    assert "tarot" not in json.dumps(body).lower()

    reading = session.get_reading("intent-1")
    assert reading is not None, "the question must create a reading"
    cards = reading["cards"]
    assert len(cards) == 3
    assert len(set(card["card_id"] for card in cards)) == 3
    assert all(card["orientation"] in ("upright", "reversed") for card in cards)
    assert any(item.get("reading") for item in reading["interpretations"])

    assert len(calls) == 1, "exactly one logical Gemini generation"
    prompt = calls[0]["input"]
    assert "[PRIVATE KAVACH READING" in prompt
    assert "Situation:" in prompt and "Influence:" in prompt and "Guidance:" in prompt

    event = trace.list_events("intent-1")[0]
    assert event["route"] == router.NEW_READING
    assert event["tarot"] == "USED"
    assert event["draw"]["after"] == reading["draw_id"]
    assert len(event["cards"]) == 3


def test_no_tarot_draws_for_ordinary_conversation(monkeypatch):
    from tarot.engine import draw_cards as real_draw

    draws = []

    def spy(*args, **kwargs):
        draws.append(1)
        return real_draw(*args, **kwargs)

    monkeypatch.setattr("chat.reading.draw_cards", spy)
    _stub(monkeypatch)
    for index, message in enumerate(("hi", "what?", "I'm sad",
                                     "I am not getting clients.",
                                     "How can I get more clients?")):
        conversation = f"intent-chat-{index}"
        session.reset(conversation)
        body = _ask(message, conversation)
        assert body["answered"] is True, message
        assert session.get_reading(conversation) is None, message
    assert draws == [], "ordinary conversation must not draw cards"


def test_follow_up_does_not_redraw(monkeypatch):
    _stub(monkeypatch)
    session.reset("intent-2")
    _ask(EXACT, "intent-2")
    first = session.get_reading("intent-2")
    for message in ("why?", "what do you mean?", "so what should I change?", "will it improve?"):
        body = _ask(message, "intent-2")
        assert body["answered"] is True
        current = session.get_reading("intent-2")
        assert current["draw_id"] == first["draw_id"]
        assert [card["card_id"] for card in current["cards"]] == [card["card_id"] for card in first["cards"]]
