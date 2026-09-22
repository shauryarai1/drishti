"""Hidden-Tarot Ask KAVACH tests. Gemini is always mocked: zero API quota used."""

from __future__ import annotations

import inspect
import json

import pytest
from fastapi.testclient import TestClient

import chat.gemini as gemini
import chat.session as session
from chat.reading import build_reading, is_new_question, private_context
from tarot.engine import draw_cards


@pytest.fixture(autouse=True)
def _pin_primary_provider_off(monkeypatch):
    """These tests assert the Gemini contract; keep the primary provider out of the way."""
    monkeypatch.setattr(
        "chat.nvidia.generate_reply_detailed",
        lambda *args, **kwargs: {"text": None, "model": None, "preferred": None, "attempts": []},
    )

BASE = {"timestamp": "2026-09-20T14:15:00+05:30", "latitude": 28.6139, "longitude": 77.209,
        "timezone": "Asia/Kolkata", "location_label": "New Delhi"}
REPLY = "There is potential here, but it depends on staying consistent."


class Response:
    def __init__(self, status_code: int, text: str = "{}"):
        self.status_code = status_code
        self.text = text

    def json(self):
        return {"steps": [{"type": "model_output", "content": [{"type": "text", "text": REPLY}]}]}


def _capture(monkeypatch, status: int = 200, body: str = "{}"):
    calls = []

    def fake_post(url, **kwargs):
        calls.append(kwargs["json"])
        return Response(status, body)

    monkeypatch.setattr(gemini.httpx, "post", fake_post)
    return calls


def _ask(client, question, conversation_id):
    return client.post("/api/ask", json={**BASE, "question": question,
                                         "conversation_id": conversation_id}).json()


# --- A/B/C: one reading, three unique cards, valid orientations -----------
def test_a_new_question_creates_exactly_one_three_card_reading():
    reading = build_reading("Should I become an engineer as per my chart?")
    assert len(reading["cards"]) == 3
    assert reading["draw_id"]


def test_b_reading_has_three_unique_cards():
    for _ in range(25):
        draws = draw_cards()
        ids = [card["card_id"] for card in draws]
        assert len(ids) == 3
        assert len(set(ids)) == 3


def test_c_orientations_are_valid():
    for _ in range(25):
        for card in draw_cards():
            assert card["orientation"] in ("upright", "reversed")


def test_card_selection_takes_no_question_input():
    assert "question" not in inspect.signature(draw_cards).parameters


# --- D/E/F: follow-up reuse vs fresh draw ---------------------------------
def test_d_and_e_follow_ups_reuse_the_reading():
    reading = build_reading("Should I become an engineer as per my chart?")
    assert is_new_question("Are you sure?", reading) is False
    assert is_new_question("Why?", reading) is False
    assert is_new_question("What if I don't like coding?", reading) is False


def test_f_new_subject_creates_a_fresh_reading():
    reading = build_reading("Should I become an engineer as per my chart?")
    assert is_new_question("How will my exam go tomorrow as per my chart?", reading) is True


def test_f_subject_change_via_api_gets_a_new_draw(monkeypatch):
    _capture(monkeypatch)
    session.reset("fresh-draw-1")
    client = TestClient(__import__("main").app)
    first = _ask(client, "Should I become an engineer as per my chart?", "fresh-draw-1")
    assert first["answered"] is True
    draw_a = session.get_reading("fresh-draw-1")["draw_id"]

    second = _ask(client, "Are you sure?", "fresh-draw-1")
    assert second["answered"] is True
    assert session.get_reading("fresh-draw-1")["draw_id"] == draw_a

    third = _ask(client, "How will my exam go tomorrow as per my chart?", "fresh-draw-1")
    assert third["answered"] is True
    assert session.get_reading("fresh-draw-1")["draw_id"] != draw_a


# --- G/I: privacy ---------------------------------------------------------
def test_g_public_api_never_contains_card_information(monkeypatch):
    _capture(monkeypatch)
    session.reset("privacy-1")
    client = TestClient(__import__("main").app)
    body = _ask(client, "Will I be successful as per my chart?", "privacy-1")
    assert set(body) == {"status", "answered", "answer", "conversation_id"}
    blob = json.dumps(body).lower()
    for banned in ("tarot", "card", "upright", "reversed", "spread", "wands", "cups",
                   "swords", "pentacles", "draw"):
        assert banned not in blob, banned


def test_i_gemini_never_receives_the_api_key(monkeypatch):
    calls = _capture(monkeypatch)
    session.reset("key-1")
    client = TestClient(__import__("main").app)
    _ask(client, "Will I be successful as per my chart?", "key-1")
    key = gemini.api_key() or "no-key"
    assert calls
    for payload in calls:
        assert key not in json.dumps(payload)


# --- H: the model receives the approved private meanings ------------------
def test_h_gemini_receives_the_private_contextual_meanings(monkeypatch):
    calls = _capture(monkeypatch)
    session.reset("context-1")
    client = TestClient(__import__("main").app)
    _ask(client, "How will my exam go as per my chart?", "context-1")
    reading = session.get_reading("context-1")
    sent = calls[0]["input"]
    for item in reading["interpretations"][:3]:
        meaning = item["reading"]
        if meaning:
            assert meaning[:60] in sent
    assert "PRIVATE KAVACH READING" in sent


# --- J: failure does not corrupt reading or history -----------------------
def test_j_failed_gemini_does_not_corrupt_state(monkeypatch):
    _capture(monkeypatch, status=429, body='{"error":{"message":"quota"}}')
    session.reset("fail-1")
    client = TestClient(__import__("main").app)
    first = _ask(client, "Should I become an engineer as per my chart?", "fail-1")
    assert first["answered"] is False
    assert first["answer"] == gemini.UNAVAILABLE_MESSAGE
    assert session.get_reading("fail-1") is None
    assert session.get_history("fail-1") == []


def test_j_success_then_failure_keeps_the_reading(monkeypatch):
    client = TestClient(__import__("main").app)
    session.reset("fail-2")
    _capture(monkeypatch)
    _ask(client, "Should I become an engineer as per my chart?", "fail-2")
    draw_id = session.get_reading("fail-2")["draw_id"]
    before = len(session.get_history("fail-2"))

    _capture(monkeypatch, status=429, body='{"error":{"message":"quota"}}')
    body = _ask(client, "Are you sure?", "fail-2")
    assert body["answered"] is False
    assert session.get_reading("fail-2")["draw_id"] == draw_id
    assert len(session.get_history("fail-2")) == before


# --- L: no old composer prose --------------------------------------------
def test_l_public_answer_is_gemini_text_untouched(monkeypatch):
    _capture(monkeypatch)
    session.reset("composer-1")
    client = TestClient(__import__("main").app)
    body = _ask(client, "How will my evening go as per my chart?", "composer-1")
    assert body["answer"] == REPLY
    for banned in ("looking at your situation", "here it points to", "as it stands",
                   "for guidance", "the useful move"):
        assert banned not in body["answer"].lower()


def test_l_sanitiser_strips_internal_language(monkeypatch):
    def fake_post(url, **kwargs):
        return Response(200, "{}")

    def json_with_leak():
        return {"steps": [{"type": "model_output", "content": [
            {"type": "text", "text": "The cards say yes. Stay consistent and patient."}]}]}

    class Leaky(Response):
        def json(self):
            return json_with_leak()

    monkeypatch.setattr(gemini.httpx, "post", lambda url, **kwargs: Leaky(200))
    session.reset("leak-1")
    client = TestClient(__import__("main").app)
    body = _ask(client, "Will I be successful as per my chart?", "leak-1")
    assert "card" not in body["answer"].lower()
    assert "consistent" in body["answer"].lower()


# --- private context formatting ------------------------------------------
def test_private_context_lists_three_positions():
    reading = build_reading("Will I be successful as per my chart?")
    text = private_context(reading)
    assert "Situation:" in text and "Influence:" in text and "Guidance:" in text
