"""Ask KAVACH provider router: ONE primary NVIDIA model, Gemini emergency fallback.

The previous multi-model NVIDIA chain was removed (see the Geoapify/routing
simplification): operational evidence showed the old primary timed out on every
attempt while a second model answered, so the registry is now a single primary
with a single attempt, followed by the Gemini fallback. Coverage of the Gemini
fallback path lives in test_production_bugfixes.py and test_ask_general_chat.py.
"""

from __future__ import annotations

import json

import httpx
import pytest

import chat.nvidia as nvidia

PRIMARY = "nvidia/nemotron-3-super-120b-a12b"
REASONING = "HIDDEN CHAIN OF THOUGHT that must never surface"
FAKE_KEY = "test-sentinel-key-never-a-real-credential"


class FakeResponse:
    def __init__(self, status_code: int = 200, payload=None, text: str = ""):
        self.status_code = status_code
        self._payload = payload
        self.text = text or (json.dumps(payload) if payload is not None else "")

    def json(self):
        if self._payload is None:
            raise ValueError("no json")
        return self._payload


def reply_payload(content: str = "An answer.", reasoning: str | None = None) -> dict:
    message = {"role": "assistant", "content": content}
    if reasoning is not None:
        message["reasoning_content"] = reasoning
    return {"choices": [{"index": 0, "message": message, "finish_reason": "stop"}]}


def scripted(calls: list, response):
    def fake_post(url, headers=None, json=None, timeout=None):  # noqa: A002 - mirrors httpx
        calls.append({"url": url, "model": (json or {}).get("model"),
                      "messages": (json or {}).get("messages"), "timeout": timeout})
        if isinstance(response, Exception):
            raise response
        return response
    return fake_post


@pytest.fixture(autouse=True)
def _isolated(monkeypatch):
    nvidia.reset_health()
    monkeypatch.setenv("NVIDIA_API_KEY", FAKE_KEY)
    monkeypatch.delenv("NVIDIA_MODELS", raising=False)
    yield
    nvidia.reset_health()


# --- provider contract ------------------------------------------------------
def test_one_primary_model_with_a_single_attempt():
    assert len(nvidia.MODEL_REGISTRY) == 1
    assert nvidia.primary_model() == PRIMARY
    assert nvidia.MAX_ATTEMPTS == 1
    assert nvidia.TOTAL_BUDGET_SECONDS <= 15.0
    assert nvidia.MODEL_REGISTRY[0][2] <= 15.0, "a dead model must not make the user wait"


def test_removed_models_are_gone():
    ids = {model_id for model_id, _tier, _timeout in nvidia.MODEL_REGISTRY}
    for removed in ("nvidia/nemotron-3.5-lightning-30b-a3b", "openai/gpt-oss-20b",
                    "nvidia/nemotron-nano-3-30b-a3b", "z-ai/glm-5.3", "google/gemma-4-31b-it"):
        assert removed not in ids, removed


def test_selection_order_is_the_single_primary():
    assert [model_id for model_id, _timeout in nvidia.select_order()] == [PRIMARY]


# --- success ----------------------------------------------------------------
def test_primary_success_returns_the_answer(monkeypatch):
    calls: list = []
    monkeypatch.setattr(nvidia.httpx, "post",
                        scripted(calls, FakeResponse(200, reply_payload("NVIDIA answered."))))

    detail = nvidia.generate_reply_detailed("what is gravity?", [])

    assert detail["text"] == "NVIDIA answered."
    assert detail["model"] == PRIMARY
    assert detail["provider"] == "nvidia"
    assert detail["fallback"] is False, "a first-attempt primary success is not a fallback"
    assert len(calls) == 1


def test_only_the_final_content_is_extracted_and_reasoning_is_discarded(monkeypatch):
    calls: list = []
    payload = reply_payload("Public answer only.", reasoning=REASONING)
    monkeypatch.setattr(nvidia.httpx, "post", scripted(calls, FakeResponse(200, payload)))

    detail = nvidia.generate_reply_detailed("hello", [])

    assert detail["text"] == "Public answer only."
    assert REASONING not in json.dumps(detail)


# --- instructions + history -------------------------------------------------
def test_system_instructions_are_preserved(monkeypatch):
    from chat.gemini import SYSTEM_INSTRUCTION

    calls: list = []
    monkeypatch.setattr(nvidia.httpx, "post",
                        scripted(calls, FakeResponse(200, reply_payload())))
    nvidia.generate_reply_detailed("plain question", [])

    messages = calls[0]["messages"]
    assert messages[0]["role"] == "system"
    assert SYSTEM_INSTRUCTION in messages[0]["content"]
    assert "general-purpose assistant" in messages[0]["content"]


def test_private_context_is_only_added_when_supplied(monkeypatch):
    from chat.gemini import READING_INSTRUCTION

    calls: list = []
    monkeypatch.setattr(nvidia.httpx, "post",
                        scripted(calls, FakeResponse(200, reply_payload())))
    nvidia.generate_reply_detailed("q", [], private_context="PRIVATE READING CONTEXT")

    messages = calls[0]["messages"]
    assert READING_INSTRUCTION in messages[0]["content"]
    assert "PRIVATE READING CONTEXT" in messages[-1]["content"]


def test_multi_turn_history_is_preserved(monkeypatch):
    calls: list = []
    monkeypatch.setattr(nvidia.httpx, "post",
                        scripted(calls, FakeResponse(200, reply_payload())))
    history = [{"role": "user", "content": "first"}, {"role": "assistant", "content": "answer"}]

    nvidia.generate_reply_detailed("follow-up", history)

    messages = calls[0]["messages"]
    assert [m["role"] for m in messages] == ["system", "user", "assistant", "user"]
    assert [m["content"] for m in messages[1:3]] == ["first", "answer"]
    assert messages[-1]["content"] == "follow-up"


# --- failure (single attempt, no retry storm) -------------------------------
@pytest.mark.parametrize("failure", [
    httpx.TimeoutException("slow"),
    httpx.ConnectError("refused"),
])
def test_network_failures_are_one_attempt_and_no_fallback_model(monkeypatch, failure):
    calls: list = []
    monkeypatch.setattr(nvidia.httpx, "post", scripted(calls, failure))

    detail = nvidia.generate_reply_detailed("hello", [])

    assert detail["text"] is None
    assert detail["fallback"] is True
    assert len(calls) == 1, "a dead model must not be retried"


@pytest.mark.parametrize("status,reason", [(429, "transient_429"), (503, "transient_503")])
def test_rate_limit_and_5xx_are_one_attempt(monkeypatch, status, reason):
    calls: list = []
    monkeypatch.setattr(nvidia.httpx, "post",
                        scripted(calls, FakeResponse(status, text="upstream error")))

    detail = nvidia.generate_reply_detailed("hello", [])

    assert detail["attempts"] == [{"model": PRIMARY, "reason": reason}]
    assert len(calls) == 1
    assert detail["fallback"] is True


def test_missing_key_is_reported_without_calling_out(monkeypatch):
    calls: list = []
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    monkeypatch.setattr(nvidia.httpx, "post", scripted(calls, FakeResponse(200, reply_payload())))

    detail = nvidia.generate_reply_detailed("hello", [])

    assert detail["text"] is None
    assert detail["attempts"][0]["reason"] == "no_api_key"
    assert calls == []


def test_health_parks_a_failing_primary(monkeypatch):
    calls: list = []
    monkeypatch.setattr(nvidia.httpx, "post",
                        scripted(calls, FakeResponse(503, text="down")))
    nvidia.generate_reply_detailed("hello", [])

    health = nvidia.health_snapshot()[PRIMARY]
    assert health["failures"] >= 1
    assert health["cooldown_for"] > 0


# --- observability + privacy ------------------------------------------------
def test_logs_contain_model_outcome_and_timing_without_content(monkeypatch, caplog):
    calls: list = []
    monkeypatch.setattr(nvidia.httpx, "post",
                        scripted(calls, FakeResponse(200, reply_payload("secret answer text"))))

    with caplog.at_level("INFO", logger="kavach.chat"):
        nvidia.generate_reply_detailed("what is gravity?", [])

    joined = "\n".join(record.getMessage() for record in caplog.records)
    assert "provider=nvidia" in joined and PRIMARY in joined
    assert "outcome=success" in joined and "elapsed_ms=" in joined
    assert "secret answer text" not in joined
    assert "gravity" not in joined.lower()
    assert FAKE_KEY not in joined
