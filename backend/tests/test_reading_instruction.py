"""Reading answers must instruct Gemini to stay inside the supplied interpretation."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

import chat.gemini as gemini


@pytest.fixture(autouse=True)
def _pin_primary_provider_off(monkeypatch):
    """These tests assert the Gemini request contract; keep the primary provider out of the way."""
    monkeypatch.setattr(
        "chat.groq.generate_reply_detailed",
        lambda *args, **kwargs: {"text": None, "model": None, "preferred": None, "attempts": []},
    )

ASK = {"timestamp": "2026-09-26T13:00:00+05:30", "latitude": 28.6139, "longitude": 77.209,
       "timezone": "Asia/Kolkata", "location_label": "New Delhi"}
READING_QUESTION = "Why am I continuously working but not getting any clients? What is blocking me?"


class Response:
    status_code = 200
    text = ""

    def json(self):
        return {"steps": [{"type": "model_output", "content": [{"type": "text", "text": "A focused interpretive reply."}]}]}


def _capture(monkeypatch):
    calls = []

    def fake_post(url, **kwargs):
        calls.append(kwargs["json"])
        return Response()

    monkeypatch.setattr(gemini.httpx, "post", fake_post)
    return calls


def _ask(question, conversation_id):
    return TestClient(__import__("main").app).post(
        "/api/ask", json={**ASK, "question": question, "conversation_id": conversation_id}).json()


def test_reading_prompt_is_the_authoritative_basis(monkeypatch):
    calls = _capture(monkeypatch)
    _ask(READING_QUESTION, "instr-1")
    system = calls[0]["system_instruction"]

    assert "authoritative interpretive basis" in system
    assert "primarily and directly from that context" in system
    assert "Synthesise the supplied meanings into one coherent interpretation" in system


def test_reading_prompt_bans_generic_advice(monkeypatch):
    calls = _capture(monkeypatch)
    _ask(READING_QUESTION, "instr-2")
    system = calls[0]["system_instruction"]

    assert "Do not add generic coaching" in system
    assert "motivational talk" in system
    assert "marketing" in system
    assert "Do not invent reasons beyond it" in system


def test_reading_prompt_hides_the_mechanism(monkeypatch):
    calls = _capture(monkeypatch)
    _ask(READING_QUESTION, "instr-3")
    system = calls[0]["system_instruction"]

    assert "Never mention cards, Tarot, spreads, orientations, positions" in system
    assert "astrologer giving a focused consultation" in system


def test_reading_prompt_sets_length_and_yesno_behaviour(monkeypatch):
    calls = _capture(monkeypatch)
    _ask(READING_QUESTION, "instr-4")
    system = calls[0]["system_instruction"]

    assert "three to six sentences" in system
    assert "For yes/no questions give a clear direction" in system
    assert "Do not claim certainty about future outcomes" in system


def test_private_context_is_attached_to_the_message(monkeypatch):
    calls = _capture(monkeypatch)
    _ask(READING_QUESTION, "instr-5")
    prompt = calls[0]["input"]

    assert "[PRIVATE KAVACH READING" in prompt
    assert "Situation:" in prompt and "Influence:" in prompt and "Guidance:" in prompt
    assert prompt.count("User:") >= 1


def test_normal_chat_does_not_get_the_reading_instruction(monkeypatch):
    calls = _capture(monkeypatch)
    body = _ask("hi", "instr-6")

    assert body["answered"] is True
    system = calls[0]["system_instruction"]
    assert "authoritative interpretive basis" not in system
    assert "Do not add generic coaching" not in system
    assert "PRIVATE KAVACH READING" not in calls[0]["input"]


def test_follow_up_keeps_the_reading_instruction(monkeypatch):
    calls = _capture(monkeypatch)
    _ask(READING_QUESTION, "instr-7")
    _ask("why?", "instr-7")

    assert len(calls) == 2
    assert "authoritative interpretive basis" in calls[1]["system_instruction"]
    assert "Situation:" in calls[1]["input"]


def test_public_answer_still_hides_card_language(monkeypatch):
    _capture(monkeypatch)
    body = _ask(READING_QUESTION, "instr-8")
    blob = json.dumps(body).lower()
    for banned in ("card", "tarot", "spread", "upright", "reversed", "draw"):
        assert banned not in blob, banned


def test_instruction_builder_switch():
    from chat.gemini import READING_INSTRUCTION, SYSTEM_INSTRUCTION, _system_instruction_for

    assert _system_instruction_for("") == SYSTEM_INSTRUCTION
    combined = _system_instruction_for("[PRIVATE KAVACH READING]")
    assert combined.startswith(SYSTEM_INSTRUCTION)
    assert READING_INSTRUCTION in combined

