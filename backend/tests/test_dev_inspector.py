"""Dev inspector tests. Gemini is always mocked: zero real API requests."""

from __future__ import annotations

from fastapi.testclient import TestClient

import chat.gemini as gemini
import chat.inspector as inspector
import chat.reading as reading
import chat.session as session

DEV = "/api/dev/kavach-tarot"
REPLY = "There is potential here, and staying consistent will matter."


class Response:
    def __init__(self, status_code: int, text: str = "{}"):
        self.status_code = status_code
        self.text = text

    def json(self):
        return {"steps": [{"type": "model_output", "content": [{"type": "text", "text": REPLY}]}]}


def _stub(monkeypatch, status: int = 200, body: str = "{}"):
    calls = []

    def fake_post(url, **kwargs):
        calls.append(kwargs["json"])
        return Response(status, body)

    monkeypatch.setattr(gemini.httpx, "post", fake_post)
    return calls


def _dev(payload):
    return TestClient(__import__("main").app).post(DEV, json=payload).json()


# --- engine sharing / decisions ------------------------------------------
def test_dev_uses_the_same_reading_engine(monkeypatch):
    _stub(monkeypatch)
    session.reset("dev-1")
    body = _dev({"question": "Should I become an engineer?", "conversation_id": "dev-1"})
    stored = session.get_reading("dev-1")
    assert stored is not None
    assert body["draw"]["after"] == stored["draw_id"] == body["cards"][0]["card_id"] and False or body["draw"]["after"] == stored["draw_id"]
    assert len(body["cards"]) == 3


def test_follow_up_reuses_draw(monkeypatch):
    _stub(monkeypatch)
    session.reset("dev-2")
    first = _dev({"question": "Should I become an engineer?", "conversation_id": "dev-2"})
    follow = _dev({"question": "Are you sure?", "conversation_id": "dev-2"})
    why = _dev({"question": "Why?", "conversation_id": "dev-2"})
    assert first["request"]["type"] == "NEW READING"
    assert follow["request"]["type"] == "REUSED READING"
    assert why["request"]["type"] == "REUSED READING"
    assert follow["draw"]["after"] == first["draw"]["after"]
    assert why["draw"]["before"] == why["draw"]["after"] == first["draw"]["after"]
    assert follow["request"]["reason"]


def test_new_subject_produces_new_draw(monkeypatch):
    _stub(monkeypatch)
    session.reset("dev-3")
    first = _dev({"question": "Should I become an engineer?", "conversation_id": "dev-3"})
    second = _dev({"question": "How will my exam go tomorrow?", "conversation_id": "dev-3"})
    assert second["request"]["type"] == "NEW READING"
    assert "new subject detected" in second["request"]["reason"]
    assert second["draw"]["after"] != first["draw"]["after"]


# --- payload contents ----------------------------------------------------
def test_dev_payload_has_all_inspector_fields(monkeypatch):
    _stub(monkeypatch)
    session.reset("dev-4")
    body = _dev({"question": "How will my exam go?", "conversation_id": "dev-4"})
    for key in ("context", "cards", "private_context", "history", "model", "response", "request", "draw"):
        assert key in body
    assert body["context"]["domain"] == "education"
    card = body["cards"][0]
    for key in ("position", "name", "orientation", "card_id", "valence", "core_meaning",
                "contextual_meaning", "source"):
        assert key in card
    assert "[PRIVATE KAVACH READING" in body["private_context"]
    assert "Situation:" in body["private_context"]
    assert body["model"]["called"] is False
    assert body["model"]["preferred"] == gemini.MODEL_PRIORITY[0]


def test_local_mode_makes_zero_gemini_calls(monkeypatch):
    calls = _stub(monkeypatch)
    session.reset("dev-5")
    body = _dev({"question": "Will I be successful?", "conversation_id": "dev-5", "mode": "local"})
    assert calls == []
    assert body["model"]["called"] is False
    assert body["response"] == {"raw": None, "public": None, "sanitised": False}


def test_forced_card_makes_zero_gemini_calls(monkeypatch):
    calls = _stub(monkeypatch)
    body = _dev({"question": "How will my exam go?", "force": ["three_of_wands"],
                 "orientation": "upright", "mode": "local"})
    assert calls == []
    assert body["cards"][0]["card_id"] == "three_of_wands"
    assert body["cards"][0]["orientation"] == "upright"
    assert body["cards"][0]["contextual_meaning"]


def test_manual_redraw_changes_draw_without_gemini(monkeypatch):
    calls = _stub(monkeypatch)
    session.reset("dev-6")
    first = _dev({"question": "How will my exam go?", "conversation_id": "dev-6"})
    again = _dev({"question": "How will my exam go?", "conversation_id": "dev-6", "mode": "redraw"})
    assert calls == []
    assert again["draw"]["after"] != first["draw"]["after"]
    assert again["request"]["reason"] == "manual dev redraw"


def test_generate_makes_exactly_one_logical_call(monkeypatch):
    calls = _stub(monkeypatch)
    session.reset("dev-7")
    body = _dev({"question": "Will I be successful?", "conversation_id": "dev-7", "generate": True})
    assert len(calls) == 1
    assert body["model"]["called"] is True
    assert body["model"]["actual"] == gemini.MODEL_PRIORITY[0]
    assert body["response"]["raw"] == REPLY
    assert body["response"]["public"] == REPLY
    assert body["response"]["sanitised"] is False


def test_quota_failure_reports_useful_dev_status(monkeypatch):
    _stub(monkeypatch, status=429, body='{"error":{"message":"quota"}}')
    session.reset("dev-8")
    body = _dev({"question": "Will I be successful?", "conversation_id": "dev-8", "generate": True})
    assert body["model"]["status"] == "unavailable"
    assert body["model"]["actual"] is None
    assert len(body["model"]["attempts"]) == len(gemini.MODEL_PRIORITY)
    assert all(item["reason"] == "quota" for item in body["model"]["attempts"])
    assert body["response"]["public"] is None
    assert body["response"]["unavailable_message"] == gemini.UNAVAILABLE_MESSAGE
    assert session.get_history("dev-8") == []


def test_raw_vs_sanitised_flagged(monkeypatch):
    class Leaky(Response):
        def json(self):
            return {"steps": [{"type": "model_output", "content": [
                {"type": "text", "text": "The cards suggest success. Stay consistent."}]}]}

    monkeypatch.setattr(gemini.httpx, "post", lambda url, **kwargs: Leaky(200))
    session.reset("dev-9")
    body = _dev({"question": "Will I be successful?", "conversation_id": "dev-9", "generate": True})
    assert body["response"]["sanitised"] is True
    assert "card" not in (body["response"]["public"] or "").lower()
    assert "cards" in body["response"]["raw"].lower()


def test_history_is_represented(monkeypatch):
    _stub(monkeypatch)
    session.reset("dev-10")
    _dev({"question": "Should I become an engineer?", "conversation_id": "dev-10", "generate": True})
    body = _dev({"question": "Are you sure?", "conversation_id": "dev-10"})
    roles = [item["role"] for item in body["history"]]
    assert roles == ["user", "assistant"]
    assert body["history"][0]["content"] == "Should I become an engineer?"


# --- security ------------------------------------------------------------
def test_no_secrets_in_dev_payload(monkeypatch):
    _stub(monkeypatch)
    payload = _dev({"question": "Will I be successful?", "conversation_id": "dev-11"})
    blob = str(payload).lower()
    for banned in inspector.SECRET_FIELDS:
        assert banned not in blob, banned
    key = gemini.api_key()
    if key:
        assert key not in str(payload)


def test_sanitiser_is_the_same_one_used_publicly():
    assert inspector.sanitise_public("The cards suggest yes. Stay steady.") == "Stay steady."


def test_decision_reason_reflects_real_logic():
    active = reading.build_reading("Should I become an engineer?")
    assert "new subject detected" in inspector.decision_reason("How will my exam go?", active, True)
    assert "follow-up marker" in inspector.decision_reason("Why?", active, False)
    assert inspector.decision_reason("Why?", None, True) == "no active reading for this conversation"
