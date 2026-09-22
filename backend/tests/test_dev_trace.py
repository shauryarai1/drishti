"""DEV trace tests: /ask answers must be inspectable without redraws or quota."""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

import chat.gemini as gemini
import chat.session as session
import chat.trace as trace
from chat.reading import private_context
from tarot.engine import draw_cards

REPLY = "There is potential here, and consistency will matter."


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


ASK = {"timestamp": "2026-09-20T14:15:00+05:30", "latitude": 28.6139, "longitude": 77.209,
       "timezone": "Asia/Kolkata", "location_label": "New Delhi"}
TRACE = "/api/dev/kavach-trace"


def _ask(question, conversation_id):
    return TestClient(__import__("main").app).post(
        "/api/ask", json={**ASK, "question": question, "conversation_id": conversation_id}).json()


def _trace(conversation_id, index=None):
    payload = {"conversation_id": conversation_id}
    if index is not None:
        payload["index"] = index
    return TestClient(__import__("main").app).post(TRACE, json=payload)


# --- A: public contract unchanged ---------------------------------------
def test_a_public_contract_unchanged(monkeypatch):
    _stub(monkeypatch)
    session.reset("trace-a")
    trace.clear("trace-a")
    body = _ask("Should I become an engineer as per my chart?", "trace-a")
    assert set(body) == {"status", "answered", "answer", "conversation_id"}
    blob = json.dumps(body).lower()
    for banned in ("card", "draw", "context", "model", "orientation", "private"):
        assert banned not in blob, banned


# --- B/C: a public request creates a trace with the same drawing ----------
def test_b_public_request_creates_a_dev_trace(monkeypatch):
    _stub(monkeypatch)
    session.reset("trace-b")
    trace.clear("trace-b")
    _ask("Should I become an engineer as per my chart?", "trace-b")
    events = trace.list_events("trace-b")
    assert len(events) == 1
    assert events[0]["question"] == "Should I become an engineer as per my chart?"


def test_c_trace_contains_the_exact_draw_used(monkeypatch):
    _stub(monkeypatch)
    session.reset("trace-c")
    trace.clear("trace-c")
    _ask("How will my exam go tomorrow as per my chart?", "trace-c")
    stored = session.get_reading("trace-c")
    event = trace.list_events("trace-c")[0]
    assert event["draw"]["after"] == stored["draw_id"]
    assert [card["card_id"] for card in event["cards"]] == [card["card_id"] for card in stored["cards"]]


# --- D/E/F: retrieval performs no work ------------------------------------
def test_d_and_e_fetching_trace_makes_no_gemini_call_and_no_draw(monkeypatch):
    calls = _stub(monkeypatch)
    session.reset("trace-d")
    trace.clear("trace-d")
    _ask("Should I become an engineer as per my chart?", "trace-d")
    before_calls = len(calls)

    draws = []
    original = draw_cards

    def spy(*args, **kwargs):
        draws.append(1)
        return original(*args, **kwargs)

    monkeypatch.setattr("tarot.engine.draw_cards", spy)
    monkeypatch.setattr("chat.reading.draw_cards", spy)

    for _ in range(3):
        response = _trace("trace-d")
        assert response.status_code == 200
    assert len(calls) == before_calls
    assert draws == []


def test_f_repeated_fetches_keep_the_same_draw_id(monkeypatch):
    _stub(monkeypatch)
    session.reset("trace-f")
    trace.clear("trace-f")
    _ask("Should I become an engineer as per my chart?", "trace-f")
    ids = {_trace("trace-f").json()["draw"]["after"] for _ in range(4)}
    assert len(ids) == 1


# --- G/H: follow-up reuse vs new draw ------------------------------------
def test_g_follow_up_trace_reuses_draw(monkeypatch):
    _stub(monkeypatch)
    session.reset("trace-g")
    trace.clear("trace-g")
    first = _ask("Should I become an engineer as per my chart?", "trace-g")
    _ask("Are you sure?", "trace-g")
    _ask("Why?", "trace-g")
    events = trace.list_events("trace-g")
    assert len(events) == 3
    assert events[0]["request"]["type"] == "NEW READING"
    assert events[1]["request"]["type"] == "REUSED READING"
    assert events[2]["request"]["type"] == "REUSED READING"
    draw_ids = {event["draw"]["after"] for event in events}
    assert len(draw_ids) == 1
    assert events[1]["cards"] == events[0]["cards"]


def test_h_new_question_trace_gets_new_draw(monkeypatch):
    _stub(monkeypatch)
    session.reset("trace-h")
    trace.clear("trace-h")
    _ask("Should I become an engineer as per my chart?", "trace-h")
    _ask("How will my exam go tomorrow as per my chart?", "trace-h")
    events = trace.list_events("trace-h")
    assert events[1]["draw"]["after"] != events[0]["draw"]["after"]
    assert events[1]["request"]["type"] == "NEW READING"


# --- I: each answer has its own trace ------------------------------------
def test_i_each_answer_has_its_own_event(monkeypatch):
    _stub(monkeypatch)
    session.reset("trace-i")
    trace.clear("trace-i")
    _ask("Should I become an engineer as per my chart?", "trace-i")
    _ask("Are you sure?", "trace-i")
    _ask("How will my exam go tomorrow as per my chart?", "trace-i")
    client = TestClient(__import__("main").app)
    first = client.post(TRACE, json={"conversation_id": "trace-i", "index": 1}).json()
    third = client.post(TRACE, json={"conversation_id": "trace-i", "index": 3}).json()
    assert first["question"] == "Should I become an engineer as per my chart?"
    assert third["question"] == "How will my exam go tomorrow as per my chart?"
    assert first["draw"]["after"] != third["draw"]["after"]


# --- J/K/L/M/N: trace contents -------------------------------------------
def test_j_trace_has_core_and_contextual_meanings(monkeypatch):
    _stub(monkeypatch)
    session.reset("trace-j")
    trace.clear("trace-j")
    _ask("How will my exam go as per my chart?", "trace-j")
    card = trace.list_events("trace-j")[0]["cards"][0]
    assert card["core_meaning"]
    assert card["contextual_meaning"]


def test_k_trace_has_orientation(monkeypatch):
    _stub(monkeypatch)
    session.reset("trace-k")
    trace.clear("trace-k")
    _ask("How will my exam go as per my chart?", "trace-k")
    for card in trace.list_events("trace-k")[0]["cards"]:
        assert card["orientation"] in ("upright", "reversed")


def test_l_trace_has_private_context(monkeypatch):
    _stub(monkeypatch)
    session.reset("trace-l")
    trace.clear("trace-l")
    _ask("How will my exam go as per my chart?", "trace-l")
    body = _trace("trace-l").json()
    stored = session.get_reading("trace-l")
    assert body["private_context"] == private_context(stored)
    assert "Situation:" in body["private_context"]


def test_m_trace_has_raw_and_public_responses(monkeypatch):
    _stub(monkeypatch)
    session.reset("trace-m")
    trace.clear("trace-m")
    _ask("How will my exam go as per my chart?", "trace-m")
    response = _trace("trace-m").json()["response"]
    assert response["raw"] == REPLY
    assert response["public"] == REPLY
    assert response["sanitised"] is False


def test_n_trace_has_model_metadata(monkeypatch):
    _stub(monkeypatch)
    session.reset("trace-n")
    trace.clear("trace-n")
    _ask("How will my exam go as per my chart?", "trace-n")
    model = _trace("trace-n").json()["model"]
    assert model["called"] is True
    assert model["actual"] == gemini.MODEL_PRIORITY[0]
    assert model["preferred"] == gemini.MODEL_PRIORITY[0]
    assert "attempts" in model


def test_n_trace_reports_fallback(monkeypatch):
    calls = []

    def fake_post(url, **kwargs):
        calls.append(kwargs["json"]["model"])
        if kwargs["json"]["model"] == gemini.MODEL_PRIORITY[0]:
            response = Response()
            response.status_code = 429
            response.text = '{"error":{"message":"quota"}}'
            return response
        return Response()

    monkeypatch.setattr(gemini.httpx, "post", fake_post)
    session.reset("trace-n2")
    trace.clear("trace-n2")
    _ask("How will my exam go as per my chart?", "trace-n2")
    model = _trace("trace-n2").json()["model"]
    assert model["actual"] == gemini.MODEL_PRIORITY[1]
    assert model["attempts"][0]["reason"] == "quota"


# --- O/P: security and gating --------------------------------------------
def test_o_no_secrets_in_trace(monkeypatch):
    _stub(monkeypatch)
    session.reset("trace-o")
    trace.clear("trace-o")
    _ask("How will my exam go as per my chart?", "trace-o")
    blob = json.dumps(_trace("trace-o").json()).lower()
    for banned in ("api_key", "apikey", "authorization", "x-goog-api-key", "headers",
                   "secret", "token", "password", "credential"):
        assert banned not in blob, banned
    key = gemini.api_key()
    if key:
        assert key not in blob


def test_p_retrieval_is_gated_in_production(monkeypatch):
    _stub(monkeypatch)
    session.reset("trace-p")
    trace.clear("trace-p")
    _ask("How will my exam go as per my chart?", "trace-p")
    monkeypatch.setenv("KAVACH_ENV", "production")
    assert TestClient(__import__("main").app).post(
        TRACE, json={"conversation_id": "trace-p"}).status_code == 404
    monkeypatch.delenv("KAVACH_ENV", raising=False)
    monkeypatch.setenv("KAVACH_DEV_TOOLS", "0")
    assert TestClient(__import__("main").app).post(
        TRACE, json={"conversation_id": "trace-p"}).status_code == 404
    monkeypatch.delenv("KAVACH_DEV_TOOLS", raising=False)


def test_traces_are_bounded(monkeypatch):
    _stub(monkeypatch)
    session.reset("trace-bound")
    trace.clear("trace-bound")
    for index in range(15):
        _ask(f"Question number {index} about my exam and my chart", "trace-bound")
    assert len(trace.list_events("trace-bound")) == trace.MAX_EVENTS_PER_CONVERSATION
