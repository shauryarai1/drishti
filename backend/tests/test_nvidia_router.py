"""Ask KAVACH provider router: NVIDIA NIM primary, Gemini emergency fallback.

All provider HTTP is mocked; no live NVIDIA or Gemini quota is used.
"""

from __future__ import annotations

import json

import httpx
import pytest
from fastapi.testclient import TestClient

import archive
import chat.nvidia as nvidia
import main
from chat.gemini import READING_INSTRUCTION, SYSTEM_INSTRUCTION

FAKE_KEY = "nvapi-test-key-should-never-leak"
REASONING = "HIDDEN CHAIN OF THOUGHT that must never surface"


class FakeResponse:
    def __init__(self, status_code: int = 200, payload=None, text: str = "") -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = text or (json.dumps(payload) if payload is not None else "")

    def json(self):
        if self._payload is None:
            raise ValueError("no json")
        return self._payload


def reply_payload(content: str = "A clear, direct answer.", reasoning: str | None = None) -> dict:
    message = {"role": "assistant", "content": content}
    if reasoning is not None:
        message["reasoning_content"] = reasoning
    return {"id": "cmpl-1", "model": "test", "choices": [{"index": 0, "message": message, "finish_reason": "stop"}]}


def all_model_ids() -> list[str]:
    return [model_id for model_id, _tier, _timeout in nvidia.approved_models()]


def scripted(calls: list, script: dict):
    """A fake httpx.post that records each attempt and follows a per-model script."""

    def fake_post(url, headers=None, json=None, timeout=None):  # noqa: A002 - mirrors httpx
        model = (json or {}).get("model")
        calls.append({"url": url, "model": model, "messages": (json or {}).get("messages"),
                      "headers": headers, "timeout": timeout, "body_keys": sorted((json or {}).keys())})
        item = script.get(model, FakeResponse(429, text="rate limited"))
        if isinstance(item, Exception):
            raise item
        return item

    return fake_post


def unusable_for_everyone(reason_status: int = 429):
    return {model_id: FakeResponse(reason_status, text="rate limited") for model_id in all_model_ids()}


@pytest.fixture(autouse=True)
def _isolated(monkeypatch):
    nvidia.reset_health()
    monkeypatch.setenv("NVIDIA_API_KEY", FAKE_KEY)
    monkeypatch.delenv("NVIDIA_MODELS", raising=False)
    yield
    nvidia.reset_health()


# --- 1, 2, 3: success and content extraction --------------------------------
def test_nvidia_primary_success(monkeypatch):
    calls: list = []
    script = {all_model_ids()[0]: FakeResponse(200, reply_payload("NVIDIA answered first."))}
    monkeypatch.setattr(nvidia.httpx, "post", scripted(calls, script))

    detail = nvidia.generate_reply_detailed("Is this thing on?", [])

    assert detail["text"] == "NVIDIA answered first."
    assert detail["provider"] == "nvidia"
    assert detail["model"] == all_model_ids()[0]
    assert len(calls) == 1


def test_final_assistant_content_is_extracted(monkeypatch):
    calls: list = []
    payload = reply_payload("Exactly this text.")
    payload["choices"][0]["message"]["reasoning_content"] = REASONING
    monkeypatch.setattr(nvidia.httpx, "post", scripted(calls, {all_model_ids()[0]: FakeResponse(200, payload)}))

    detail = nvidia.generate_reply_detailed("hello", [])
    assert detail["text"] == "Exactly this text."


def test_reasoning_content_is_discarded(monkeypatch):
    calls: list = []
    payload = reply_payload("Public answer only.", reasoning=REASONING)
    monkeypatch.setattr(nvidia.httpx, "post", scripted(calls, {all_model_ids()[0]: FakeResponse(200, payload)}))

    detail = nvidia.generate_reply_detailed("hello", [])
    assert REASONING not in json.dumps(detail)


# --- 5, 6: instructions and history preserved -------------------------------
def test_system_instructions_are_preserved(monkeypatch):
    calls: list = []
    monkeypatch.setattr(nvidia.httpx, "post",
                        scripted(calls, {all_model_ids()[0]: FakeResponse(200, reply_payload())}))

    nvidia.generate_reply_detailed("plain question", [])

    messages = calls[0]["messages"]
    assert messages[0]["role"] == "system"
    assert SYSTEM_INSTRUCTION in messages[0]["content"]


def test_reading_instruction_added_only_with_private_context(monkeypatch):
    calls: list = []
    monkeypatch.setattr(nvidia.httpx, "post",
                        scripted(calls, {all_model_ids()[0]: FakeResponse(200, reply_payload())}))

    nvidia.generate_reply_detailed("q", [], private_context="PRIVATE READING CONTEXT")

    messages = calls[0]["messages"]
    assert READING_INSTRUCTION in messages[0]["content"]
    assert "PRIVATE READING CONTEXT" in messages[-1]["content"]


def test_multi_turn_history_is_preserved(monkeypatch):
    calls: list = []
    monkeypatch.setattr(nvidia.httpx, "post",
                        scripted(calls, {all_model_ids()[0]: FakeResponse(200, reply_payload())}))
    history = [
        {"role": "user", "content": "first question"},
        {"role": "assistant", "content": "first answer"},
        {"role": "user", "content": "follow-up"},
        {"role": "assistant", "content": "second answer"},
    ]

    nvidia.generate_reply_detailed("and what about that?", history)

    messages = calls[0]["messages"]
    assert [m["role"] for m in messages] == ["system", "user", "assistant", "user", "assistant", "user"]
    assert [m["content"] for m in messages[1:5]] == [h["content"] for h in history]
    assert messages[-1]["content"] == "and what about that?"


def test_history_is_bounded_by_the_existing_session_window():
    import chat.session as session

    conversation = "router-bounds"
    session.reset(conversation)
    for index in range(40):
        session.append(conversation, "user", f"message {index}")
    assert len(session.get_history(conversation)) == session.MAX_MESSAGES


# --- 7, 8, 9, 10: failover across models ------------------------------------
def test_first_model_429_falls_over_to_the_second(monkeypatch):
    calls: list = []
    first, second = all_model_ids()[0], all_model_ids()[1]
    script = {first: FakeResponse(429, text="quota"), second: FakeResponse(200, reply_payload("Second model here."))}
    monkeypatch.setattr(nvidia.httpx, "post", scripted(calls, script))

    detail = nvidia.generate_reply_detailed("hello", [])

    assert detail["text"] == "Second model here."
    assert detail["model"] == second
    assert [attempt["model"] for attempt in detail["attempts"]] == [first, second]


def test_timeout_falls_over_to_another_model(monkeypatch):
    calls: list = []
    first, second = all_model_ids()[0], all_model_ids()[1]
    script = {first: httpx.TimeoutException("too slow"),
              second: FakeResponse(200, reply_payload("Recovered after timeout."))}
    monkeypatch.setattr(nvidia.httpx, "post", scripted(calls, script))

    detail = nvidia.generate_reply_detailed("hello", [])

    assert detail["text"] == "Recovered after timeout."
    assert detail["attempts"][0]["reason"] == "timeout"
    assert detail["model"] == second


def test_five_xx_falls_over_to_another_model(monkeypatch):
    calls: list = []
    first, second = all_model_ids()[0], all_model_ids()[1]
    script = {first: FakeResponse(503, text="upstream unavailable"),
              second: FakeResponse(200, reply_payload("After 5xx."))}
    monkeypatch.setattr(nvidia.httpx, "post", scripted(calls, script))

    detail = nvidia.generate_reply_detailed("hello", [])

    assert detail["model"] == second
    assert detail["attempts"][0]["reason"] == "transient_503"


def test_unavailable_model_falls_over_to_another_model(monkeypatch):
    calls: list = []
    first, second = all_model_ids()[0], all_model_ids()[1]
    script = {first: FakeResponse(404, text="model not found"),
              second: FakeResponse(200, reply_payload("After 404."))}
    monkeypatch.setattr(nvidia.httpx, "post", scripted(calls, script))

    detail = nvidia.generate_reply_detailed("hello", [])

    assert detail["model"] == second
    assert detail["attempts"][0]["reason"] == "model_404"


# --- 11, 12: routing breadth and the attempt bound --------------------------
def test_at_least_three_distinct_models_can_participate():
    order = nvidia.select_order()
    assert len({model_id for model_id, _timeout in order}) >= 3
    assert len(nvidia.approved_models()) >= 5


def test_nvidia_attempts_are_bounded(monkeypatch):
    calls: list = []
    monkeypatch.setattr(nvidia.httpx, "post", scripted(calls, unusable_for_everyone(429)))

    detail = nvidia.generate_reply_detailed("hello", [])

    assert detail["text"] is None
    assert len(detail["attempts"]) <= nvidia.MAX_ATTEMPTS
    assert len(calls) <= nvidia.MAX_ATTEMPTS


def test_budget_stops_further_attempts(monkeypatch):
    calls: list = []
    monkeypatch.setattr(nvidia.httpx, "post", scripted(calls, unusable_for_everyone(500)))
    monkeypatch.setattr(nvidia, "TOTAL_BUDGET_SECONDS", -1.0)

    detail = nvidia.generate_reply_detailed("hello", [])

    assert calls == []
    assert detail["attempts"][0]["reason"] == "budget_exhausted"


# --- 13, 14: health, cooldown, healthy preference ---------------------------
def test_transient_failure_sets_a_cooldown(monkeypatch):
    calls: list = []
    first = all_model_ids()[0]
    script = {first: FakeResponse(503, text="down"), all_model_ids()[1]: FakeResponse(200, reply_payload())}
    monkeypatch.setattr(nvidia.httpx, "post", scripted(calls, script))

    nvidia.generate_reply_detailed("hello", [])

    health = nvidia.health_snapshot()[first]
    assert health["failures"] >= 1
    assert health["cooldown_for"] > 0


def test_healthy_model_is_preferred_over_a_parked_model(monkeypatch):
    first = all_model_ids()[0]
    calls: list = []
    script = {first: FakeResponse(503, text="down"), all_model_ids()[1]: FakeResponse(200, reply_payload())}
    monkeypatch.setattr(nvidia.httpx, "post", scripted(calls, script))
    nvidia.generate_reply_detailed("hello", [])

    order = [model_id for model_id, _timeout in nvidia.select_order()]
    assert order.index(first) > 0, "a parked model must not be tried first"


# --- 16: no key ------------------------------------------------------------
def test_missing_nvidia_key_is_safe(monkeypatch):
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    monkeypatch.setattr(nvidia.httpx, "post", scripted([], {}))

    detail = nvidia.generate_reply_detailed("hello", [])

    assert detail["text"] is None
    assert detail["attempts"][0]["reason"] == "no_api_key"


# --- 17: no provider hopping for application-level problems -----------------
def test_application_error_does_not_hop_models(monkeypatch):
    calls: list = []
    monkeypatch.setattr(nvidia.httpx, "post",
                        scripted(calls, {model_id: FakeResponse(400, text="invalid request payload")
                                         for model_id in all_model_ids()}))

    detail = nvidia.generate_reply_detailed("hello", [])

    assert len(calls) == 1
    assert detail["text"] is None
    assert detail["attempts"][0]["reason"] == "request_400"


def test_auth_failure_does_not_hop_models(monkeypatch):
    calls: list = []
    monkeypatch.setattr(nvidia.httpx, "post",
                        scripted(calls, {model_id: FakeResponse(403, text="Authorization failed")
                                         for model_id in all_model_ids()}))

    detail = nvidia.generate_reply_detailed("hello", [])

    assert len(calls) == 1
    assert detail["attempts"][0]["reason"] == "auth"


# --- 15, 16, 18, 19, 20: end-to-end through the public Ask KAVACH endpoint ---
class FakeStore:
    def __init__(self) -> None:
        self.rows: list[dict] = []

    def configured(self) -> bool:
        return True

    def insert(self, row: dict):
        stored = dict(row)
        stored["id"] = f"id-{len(self.rows) + 1}"
        self.rows.append(stored)
        return stored["id"]

    def verify_token(self, token):
        return None


@pytest.fixture()
def ask_env(monkeypatch):
    """The public endpoint with mocked providers and an in-memory archive."""
    store = FakeStore()
    monkeypatch.setattr(archive, "store", store)
    monkeypatch.setattr("chat.reading.sensitive_response", lambda _question: None)

    def no_reading(_question):
        raise RuntimeError("no tarot in tests")

    monkeypatch.setattr("chat.reading.build_reading", no_reading)
    return store


def ask(client: TestClient, question: str = "What does my chart say about Mars?"):
    return client.post("/api/ask", json={"question": question, "timestamp": "2026-09-21T22:40:00+05:30",
                                         "conversation_id": "router-test"})


def test_all_nvidia_attempts_fail_then_gemini_answers(monkeypatch, ask_env):
    calls: list = []
    monkeypatch.setattr(nvidia.httpx, "post", scripted(calls, unusable_for_everyone(429)))
    monkeypatch.setattr("chat.gemini.generate_reply_detailed",
                        lambda *a, **k: {"text": "Gemini emergency answer.", "model": "gemini-3.6-flash",
                                         "preferred": "gemini-3.6-flash", "attempts": []})

    response = ask(TestClient(main.app))

    assert response.status_code == 200
    assert response.json()["answer"] == "Gemini emergency answer."
    assert len(calls) <= nvidia.MAX_ATTEMPTS


def test_gemini_used_when_nvidia_key_is_absent(monkeypatch, ask_env):
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    monkeypatch.setattr(nvidia.httpx, "post", scripted([], {}))
    monkeypatch.setattr("chat.gemini.generate_reply_detailed",
                        lambda *a, **k: {"text": "Gemini carried it.", "model": "gemini-3.6-flash",
                                         "preferred": "gemini-3.6-flash", "attempts": []})

    response = ask(TestClient(main.app))

    assert response.status_code == 200
    assert response.json()["answer"] == "Gemini carried it."


def test_secrets_never_appear_in_the_response(monkeypatch, ask_env):
    calls: list = []
    monkeypatch.setattr(nvidia.httpx, "post",
                        scripted(calls, {all_model_ids()[0]: FakeResponse(200, reply_payload("Fine."))}))

    body = ask(TestClient(main.app)).text

    assert FAKE_KEY not in body
    assert "Bearer" not in body
    assert REASONING not in body


def test_response_schema_is_backwards_compatible(monkeypatch, ask_env):
    calls: list = []
    monkeypatch.setattr(nvidia.httpx, "post",
                        scripted(calls, {all_model_ids()[0]: FakeResponse(200, reply_payload("Schema check."))}))

    body = ask(TestClient(main.app)).json()

    assert set(body.keys()) == {"status", "answered", "answer", "conversation_id"}
    assert body["status"] == "ok"
    assert body["answered"] is True
    assert isinstance(body["answer"], str) and body["answer"]


def test_reasoning_content_is_never_archived(monkeypatch, ask_env):
    calls: list = []
    payload = reply_payload("Archived answer only.", reasoning=REASONING)
    monkeypatch.setattr(nvidia.httpx, "post", scripted(calls, {all_model_ids()[0]: FakeResponse(200, payload)}))

    ask(TestClient(main.app))

    assert len(ask_env.rows) == 1
    row = ask_env.rows[0]
    assert row["product"] == "ask"
    assert row["result_data"] == {"answered": True, "answer": "Archived answer only."}
    assert row["input_data"]["question"] == "What does your chart say about Mars?".replace("your", "my")
    assert REASONING not in json.dumps(row)
    assert FAKE_KEY not in json.dumps(row)


def test_invalid_public_request_never_reaches_a_provider(monkeypatch, ask_env):
    calls: list = []
    monkeypatch.setattr(nvidia.httpx, "post", scripted(calls, {}))
    monkeypatch.setattr("chat.gemini.generate_reply_detailed", lambda *a, **k: {"text": "should not run"})

    response = TestClient(main.app).post("/api/ask", json={"timestamp": "2026-09-21T22:40:00+05:30"})

    assert response.status_code == 422
    assert calls == []


# --- hardened registry, latency budget and unavailable-model handling --------
PRIMARY = "nvidia/nemotron-3.5-lightning-30b-a3b"
NANO = "nvidia/nemotron-nano-3-30b-a3b"
GPT_OSS_20B = "openai/gpt-oss-20b"


def test_lightning_is_the_clear_primary_model():
    assert nvidia.primary_model() == PRIMARY
    assert nvidia.MODEL_REGISTRY[0][0] == PRIMARY
    assert nvidia.MODEL_REGISTRY[0][1] == nvidia.TIER_FAST
    assert nvidia.select_order()[0][0] == PRIMARY


def test_account_unavailable_model_is_removed_from_the_registry():
    ids = [model_id for model_id, _tier, _timeout in nvidia.MODEL_REGISTRY]
    assert NANO not in ids, "a model returning account-specific 404 must not be in the default registry"


def test_gpt_oss_20b_is_only_a_last_resort_fallback():
    registry = nvidia.MODEL_REGISTRY
    assert registry[-1][0] == GPT_OSS_20B
    assert registry[-1][1] == nvidia.TIER_FALLBACK
    # It must never be reached while any other approved model is healthy.
    order = [model_id for model_id, _timeout in nvidia.select_order()]
    assert order[-1] == GPT_OSS_20B


def test_max_attempts_is_two():
    assert nvidia.MAX_ATTEMPTS == 2


def test_attempt_timeouts_and_budget_are_short():
    timeouts = {model_id: timeout for model_id, _tier, timeout in nvidia.MODEL_REGISTRY}
    assert timeouts[PRIMARY] == 10.0
    for timeout in timeouts.values():
        assert 8.0 <= timeout <= 12.0, timeout
    assert 15.0 <= nvidia.TOTAL_BUDGET_SECONDS <= 20.0
    assert nvidia.TOTAL_BUDGET_SECONDS == 20.0


def test_cooldown_durations():
    assert nvidia.COOLDOWN_SECONDS == 90.0
    assert nvidia.UNAVAILABLE_COOLDOWN_SECONDS >= 600.0
    assert nvidia.UNAVAILABLE_COOLDOWN_SECONDS > nvidia.COOLDOWN_SECONDS


def test_primary_then_at_most_one_fallback(monkeypatch):
    calls: list = []
    expected = [model_id for model_id, _timeout in nvidia.select_order()][:2]
    monkeypatch.setattr(nvidia.httpx, "post", scripted(calls, unusable_for_everyone(503)))

    detail = nvidia.generate_reply_detailed("hello", [])

    assert detail["text"] is None
    assert len(calls) == 2, "primary plus exactly one fallback"
    assert [attempt["model"] for attempt in detail["attempts"]] == expected
    assert calls[0]["model"] == PRIMARY


def test_per_attempt_timeout_is_clipped_to_the_remaining_budget(monkeypatch):
    calls: list = []
    monkeypatch.setattr(nvidia.httpx, "post", scripted(calls, unusable_for_everyone(429)))
    monkeypatch.setattr(nvidia, "TOTAL_BUDGET_SECONDS", 5.0)

    nvidia.generate_reply_detailed("hello", [])

    assert calls, "at least one attempt should still run inside the budget"
    for call in calls:
        assert call["timeout"] <= 5.0, call["timeout"]


def test_account_unavailable_model_is_parked_for_a_long_time(monkeypatch):
    calls: list = []
    monkeypatch.setattr(nvidia.httpx, "post", scripted(calls, unusable_for_everyone(404)))

    nvidia.generate_reply_detailed("hello", [])

    health = nvidia.health_snapshot()[PRIMARY]
    assert health["cooldown_for"] > nvidia.COOLDOWN_SECONDS * 10, "404 must park far longer than a transient error"


def test_transient_overload_parks_only_briefly(monkeypatch):
    calls: list = []
    monkeypatch.setattr(nvidia.httpx, "post", scripted(calls, unusable_for_everyone(503)))

    nvidia.generate_reply_detailed("hello", [])

    health = nvidia.health_snapshot()[PRIMARY]
    assert 0 < health["cooldown_for"] <= nvidia.COOLDOWN_SECONDS


def test_primary_failure_then_fallback_then_gemini(monkeypatch, ask_env):
    """The production flow: Lightning -> one fallback -> Gemini."""
    calls: list = []
    gemini_calls: list = []
    monkeypatch.setattr(nvidia.httpx, "post", scripted(calls, unusable_for_everyone(503)))

    def gemini(*args, **kwargs):
        gemini_calls.append(1)
        return {"text": "Gemini answered after NVIDIA.", "model": "gemini-3.6-flash",
                "preferred": "gemini-3.6-flash", "attempts": []}

    monkeypatch.setattr("chat.gemini.generate_reply_detailed", gemini)

    body = ask(TestClient(main.app)).json()

    assert body["answered"] is True
    assert body["answer"] == "Gemini answered after NVIDIA."
    assert [call["model"] for call in calls] == [PRIMARY, nvidia.MODEL_REGISTRY[1][0]]
    assert len(calls) == nvidia.MAX_ATTEMPTS
    assert gemini_calls == [1]


def test_gemini_is_only_tried_after_nvidia_is_exhausted(monkeypatch, ask_env):
    calls: list = []
    gemini_calls: list = []
    monkeypatch.setattr(nvidia.httpx, "post",
                        scripted(calls, {PRIMARY: FakeResponse(200, reply_payload("NVIDIA first."))}))

    def gemini(*args, **kwargs):
        gemini_calls.append(1)
        return {"text": "should not be used"}

    monkeypatch.setattr("chat.gemini.generate_reply_detailed", gemini)

    body = ask(TestClient(main.app)).json()

    assert body["answer"] == "NVIDIA first."
    assert gemini_calls == []
    assert len(calls) == 1


def test_reasoning_privacy_survives_the_new_configuration(monkeypatch, ask_env):
    calls: list = []
    payload = reply_payload("Final answer only.", reasoning=REASONING)
    monkeypatch.setattr(nvidia.httpx, "post", scripted(calls, {PRIMARY: FakeResponse(200, payload)}))

    body = ask(TestClient(main.app)).json()

    assert body["answer"] == "Final answer only."
    assert REASONING not in json.dumps(body)
    assert REASONING not in json.dumps(ask_env.rows)
    assert FAKE_KEY not in json.dumps(body)
