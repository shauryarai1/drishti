"""Ask KAVACH chat service: fallback policy, history and failure handling.

Gemini is always mocked here (see tests/conftest.py): zero API quota is used.
"""

from __future__ import annotations

import json

import pytest

import chat.gemini as gemini
import chat.session as session


class Response:
    def __init__(self, status_code: int, text: str = "{}"):
        self.status_code = status_code
        self.text = text

    def json(self):
        if self.status_code != 200:
            return json.loads(self.text)
        return {"steps": [{"type": "model_output", "content": [{"type": "text", "text": "Reply from model."}]}]}


def test_fallback_order_is_evidence_based():
    # Live evidence: flash-lite answered in ~4s, so it is tried first; the daily
    # quota for gemini-3.6-flash is exhausted and gemini-2.5-flash was retired.
    assert gemini.MODEL_PRIORITY[0] == "gemini-3.5-flash-lite"
    assert gemini.MODEL_PRIORITY[1] == "gemini-3.5-flash"
    assert "gemini-3.6-flash" not in gemini.MODEL_PRIORITY
    assert "gemini-2.5-flash" not in gemini.MODEL_PRIORITY
    assert len(set(gemini.MODEL_PRIORITY)) == len(gemini.MODEL_PRIORITY)


def test_success_on_preferred_model(monkeypatch):
    seen = []

    def fake_post(url, **kwargs):
        seen.append(kwargs["json"]["model"])
        return Response(200)

    monkeypatch.setattr(gemini.httpx, "post", fake_post)
    assert gemini.generate_reply("hello", []) == "Reply from model."
    assert seen == [gemini.MODEL_PRIORITY[0]]


def test_quota_falls_back_to_next_model(monkeypatch):
    seen = []

    def fake_post(url, **kwargs):
        seen.append(kwargs["json"]["model"])
        if kwargs["json"]["model"] == gemini.MODEL_PRIORITY[0]:
            return Response(429, '{"error":{"message":"Rate limit exceeded"}}')
        return Response(200)

    monkeypatch.setattr(gemini.httpx, "post", fake_post)
    assert gemini.generate_reply("hello", []) == "Reply from model."
    assert seen == [gemini.MODEL_PRIORITY[0], gemini.MODEL_PRIORITY[1]]


def test_each_model_attempted_at_most_once(monkeypatch):
    seen = []

    def fake_post(url, **kwargs):
        seen.append(kwargs["json"]["model"])
        return Response(429, '{"error":{"message":"quota"}}')

    monkeypatch.setattr(gemini.httpx, "post", fake_post)
    assert gemini.generate_reply("hello", []) is None
    assert len(seen) == len(gemini.MODEL_PRIORITY)
    assert len(set(seen)) == len(seen)


def test_auth_error_does_not_fall_back(monkeypatch):
    seen = []

    def fake_post(url, **kwargs):
        seen.append(kwargs["json"]["model"])
        return Response(401, '{"error":{"message":"invalid credentials"}}')

    monkeypatch.setattr(gemini.httpx, "post", fake_post)
    assert gemini.generate_reply("hello", []) is None
    assert seen == [gemini.MODEL_PRIORITY[0]]


def test_bad_request_does_not_fall_back(monkeypatch):
    seen = []

    def fake_post(url, **kwargs):
        seen.append(kwargs["json"]["model"])
        return Response(400, '{"error":{"message":"malformed request"}}')

    monkeypatch.setattr(gemini.httpx, "post", fake_post)
    assert gemini.generate_reply("hello", []) is None
    assert len(seen) == 1


def test_unsupported_model_error_falls_back(monkeypatch):
    seen = []

    def fake_post(url, **kwargs):
        seen.append(kwargs["json"]["model"])
        if len(seen) == 1:
            return Response(404, '{"error":{"message":"model not found"}}')
        return Response(200)

    monkeypatch.setattr(gemini.httpx, "post", fake_post)
    assert gemini.generate_reply("hello", []) == "Reply from model."
    assert len(seen) == 2


def test_network_error_returns_none_without_cycling(monkeypatch):
    seen = []

    def fake_post(url, **kwargs):
        seen.append(kwargs["json"]["model"])
        raise gemini.httpx.HTTPError("boom")

    monkeypatch.setattr(gemini.httpx, "post", fake_post)
    assert gemini.generate_reply("hello", []) is None
    assert len(seen) == 1


def test_history_survives_a_model_switch():
    session.reset("switch-test")
    session.append("switch-test", "user", "Should I become an engineer as per my chart?")
    session.append("switch-test", "assistant", "Depends on what you enjoy.")
    history = session.get_history("switch-test")
    assert [item["role"] for item in history] == ["user", "assistant"]
    assert history[0]["content"] == "Should I become an engineer as per my chart?"


def test_history_is_bounded():
    session.reset("bounded")
    for index in range(30):
        session.append("bounded", "user", f"message {index}")
    assert len(session.get_history("bounded")) == session.MAX_MESSAGES


def test_new_chat_isolation():
    session.reset("conv-a")
    session.reset("conv-b")
    session.append("conv-a", "user", "engineering discussion")
    session.append("conv-b", "user", "something else")
    assert session.get_history("conv-a")[0]["content"] == "engineering discussion"
    assert session.get_history("conv-b")[0]["content"] == "something else"
    session.reset("conv-b")
    assert session.get_history("conv-b") == []


def test_api_returns_stub_and_reuses_conversation_id(monkeypatch):
    from fastapi.testclient import TestClient

    import main

    client = TestClient(main.app)
    payload = {"question": "Should I become an engineer as per my chart?", "conversation_id": "api-test-1",
               "timestamp": "2026-09-20T14:15:00+05:30", "latitude": 28.6, "longitude": 77.2,
               "timezone": "Asia/Kolkata", "location_label": "New Delhi"}
    first = client.post("/api/ask", json=payload).json()
    assert first["conversation_id"] == "api-test-1"
    assert first["answered"] is True
    assert first["answer"]
    assert set(first) == {"status", "answered", "answer", "conversation_id"}

    second = client.post("/api/ask", json={**payload, "question": "Are you sure?"}).json()
    assert second["conversation_id"] == "api-test-1"


def test_api_all_models_exhausted(monkeypatch):
    from fastapi.testclient import TestClient

    import main

    def fake_post(url, **kwargs):
        return Response(429, '{"error":{"message":"quota"}}')

    monkeypatch.setattr(gemini.httpx, "post", fake_post)
    session.reset("exhausted-1")
    client = TestClient(main.app)
    body = client.post("/api/ask", json={
        "question": "What does Saturn represent in astrology?", "conversation_id": "exhausted-1",
        "timestamp": "2026-09-20T14:15:00+05:30", "latitude": 28.6, "longitude": 77.2,
        "timezone": "Asia/Kolkata", "location_label": "New Delhi"}).json()
    assert body["answered"] is False
    assert body["answer"] == gemini.UNAVAILABLE_MESSAGE
    assert session.get_history("exhausted-1") == []
    lowered = str(body).lower()
    for banned in ("tarot", "card", "spread", "for guidance", "looking at your situation"):
        assert banned not in lowered
