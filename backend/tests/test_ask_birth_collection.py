"""Conversational birth-detail collection: the real owner-reported flow.

"21/01/2010" followed by "08:19 am delhi" must accumulate into complete birth
data, resolve the place through the approved location pipeline, invoke the
authoritative kundli.build_kundli() and answer from the calculated chart plus
the KAVACH planet framework. A random date inside an ordinary question must
never trigger astrology, and internal architecture phrases ("chart context
block", "build_kundli", "provider"...) must never reach the user.

Providers, the geocoder and the reading engine are mocked: zero live quota.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import chat.gemini as gemini
import chat.groq as groq
import chat.natal as natal
import chat.planet_framework as planet_framework
import main

ASK = {"timestamp": "2026-09-25T11:45:00+05:30", "latitude": 28.6139,
       "longitude": 77.209, "timezone": "Asia/Kolkata",
       "location_label": "New Delhi"}

# The geocoder only resolves these places, so a stray query can never pass.
GEOCODED = {"Delhi": (28.6139, 77.209), "New Delhi": (28.6139, 77.209),
            "Jaipur": (26.9124, 75.7873)}

# The exact leak the owner observed: a model answer asking the USER for the
# internal context block. It must never reach the public answer again.
LEAKY_ANSWER = (
    "To look into a chart for this birth data, I need the official chart "
    "context block to be provided with your message. Without those calculated "
    "placements, I cannot run an interpretation."
)

INTERNAL_PHRASES = ("chart context", "context block", "official chart",
                    "provided chart", "authoritative context", "build_kundli",
                    "provider", "system instruction", "system prompt",
                    "calculated placement")


class FakeStore:
    def __init__(self):
        self.rows: list[dict] = []

    def configured(self):
        return True

    def insert(self, row):
        stored = dict(row)
        stored["id"] = f"row-{len(self.rows) + 1}"
        self.rows.append(stored)
        return stored["id"]

    def verify_token(self, token):
        return None


@pytest.fixture()
def env(monkeypatch):
    """Mock both providers, the geocoder and the reading engine; count charts."""
    import archive

    seen: dict = {"groq": [], "gemini": [], "geocode": [], "kundli": 0,
                  "readings": 0}
    script = {"groq_text": "Groq answer."}

    monkeypatch.setattr(archive, "store", FakeStore())
    monkeypatch.setattr("chat.reading.sensitive_response", lambda _q: None)
    monkeypatch.setattr("chat.reading.build_reading",
                        lambda _q: {"draw_id": "d1", "cards": []})
    monkeypatch.setattr("chat.reading.private_context",
                        lambda _r: "PRIVATE READING CONTEXT")

    def fake_groq(_q, history, private_context="", astrology_context=""):
        seen["groq"].append({"private": private_context,
                             "astrology": astrology_context,
                             "history": list(history)})
        return {"text": script["groq_text"], "model": groq.MODEL,
                "preferred": groq.MODEL, "provider": "groq", "attempts": [],
                "fallback": False}

    def fake_gemini(_q, history, private_context="", astrology_context=""):
        seen["gemini"].append({"private": private_context,
                               "astrology": astrology_context})
        return {"text": "Gemini answer.", "model": "gemini-3.5-flash-lite",
                "preferred": "gemini-3.5-flash-lite", "provider": "gemini",
                "attempts": []}

    monkeypatch.setattr("chat.groq.generate_reply_detailed", fake_groq)
    monkeypatch.setattr("chat.gemini.generate_reply_detailed", fake_gemini)
    gemini.reset_health()

    import geocoding

    def fake_resolve(place):
        seen["geocode"].append(place)
        return GEOCODED.get((place or "").strip().title())

    monkeypatch.setattr(geocoding, "resolve_coordinates", fake_resolve)

    import kundli as kundli_module

    original = kundli_module.build_kundli

    def counting(payload):
        seen["kundli"] += 1
        return original(payload)

    monkeypatch.setattr(kundli_module, "build_kundli", counting)
    yield {"seen": seen, "script": script}


@pytest.fixture()
def client():
    return TestClient(main.app)


def ask(client, question, conversation_id):
    return client.post("/api/ask", json={**ASK, "question": question,
                                         "conversation_id": conversation_id}).json()


# --- 1: the exact reported conversation ----------------------------------------
def test_owner_flow_date_then_time_and_place(env, client):
    first = ask(client, "21/01/2010", "flow-1")

    # A lone date is acknowledged naturally: no chart yet, no fake context.
    assert first["answered"] is True
    assert env["seen"]["kundli"] == 0
    assert env["seen"]["groq"][0]["astrology"] == ""
    state = natal.get_state("flow-1")
    assert state["date"] == "2010-01-21", "the date is retained across turns"

    second = ask(client, "08:19 am delhi", "flow-1")

    assert second["answered"] is True
    assert env["seen"]["kundli"] == 1, "the completed details calculate once"
    assert env["seen"]["geocode"] == ["delhi"], "Delhi went through the approved pipeline"
    context = env["seen"]["groq"][-1]["astrology"]
    assert "KAVACH CHART CONTEXT" in context
    assert "Birth: 2010-01-21 08:19" in context
    assert planet_framework.FRAMEWORK_NAME in context, "owner framework applied"
    assert second["answer"] == "Groq answer.", "a natural answer reaches the user"
    assert env["seen"]["groq"][-1]["private"] == "", "no reading context"


# --- 2: date, then time, then place --------------------------------------------
def test_flow_date_time_then_place_calculates(env, client):
    ask(client, "21/01/2010", "flow-2")
    ask(client, "08:19 am", "flow-2")
    body = ask(client, "Delhi", "flow-2")

    assert body["answered"] is True
    assert env["seen"]["kundli"] == 1
    assert env["seen"]["geocode"] == ["Delhi"]
    assert "Birth: 2010-01-21 08:19" in env["seen"]["groq"][-1]["astrology"]


# --- 3: date, then place, then time --------------------------------------------
def test_flow_date_place_then_time_calculates(env, client):
    ask(client, "21/01/2010", "flow-3")
    ask(client, "Delhi", "flow-3")
    body = ask(client, "08:19 am", "flow-3")

    assert body["answered"] is True
    assert env["seen"]["kundli"] == 1
    assert env["seen"]["geocode"] == ["Delhi"]
    assert "Birth: 2010-01-21 08:19" in env["seen"]["groq"][-1]["astrology"]


# --- 4: everything in one message ----------------------------------------------
def test_single_message_with_all_details_calculates(env, client):
    body = ask(client, "21/01/2010 08:19 am Delhi", "flow-4")

    assert body["answered"] is True
    assert env["seen"]["kundli"] == 1
    assert env["seen"]["geocode"] == ["Delhi"]
    assert "KAVACH CHART CONTEXT" in env["seen"]["groq"][-1]["astrology"]


# --- 5: a random date in an ordinary question stays general ---------------------
@pytest.mark.parametrize("question", [
    "What happened on 21/01/2010?",
    "Explain 21/01/2010 as a date format",
])
def test_random_dates_in_normal_questions_stay_general(env, client, question):
    conversation_id = f"gen-{abs(hash(question)) % 10000}"
    body = ask(client, question, conversation_id)

    assert body["answered"] is True
    assert natal.get_state(conversation_id) is None, "no collection state opened"
    assert env["seen"]["kundli"] == 0
    assert env["seen"]["geocode"] == []
    assert env["seen"]["groq"][-1]["astrology"] == ""


def test_date_in_a_question_never_overwrites_collected_details(env, client):
    ask(client, "21/01/2010", "flow-5")
    ask(client, "what about events on 23.11.2009", "flow-5")

    state = natal.get_state("flow-5")
    assert state["date"] == "2010-01-21", "an unrelated date is not ingested"
    assert state["place"] is None, "leftover words are not a birth place"
    assert env["seen"]["kundli"] == 0


# --- 6: internal architecture never reaches the user ----------------------------
def test_leaky_model_answer_is_scrubbed_before_the_user_sees_it(env, client):
    env["script"]["groq_text"] = LEAKY_ANSWER
    body = ask(client, "08:19 am delhi", "leak-1")

    answer = body["answer"]
    for phrase in INTERNAL_PHRASES:
        assert phrase not in answer.lower(), f"internal leak: {phrase}"
    assert answer != LEAKY_ANSWER


def test_deterministic_replies_never_contain_internal_phrases():
    from chat.router import SCOPE_MESSAGE

    for reply in (natal.ALL_DETAILS_REPLY, natal.PLACE_AND_TIME_REPLY,
                  natal.PLACE_REPLY, natal.TIME_REPLY, natal.DETAILS_REPLY,
                  natal.GEOCODER_BUSY_REPLY, natal.CALCULATION_FAILED_REPLY,
                  natal.CHART_FALLBACK_REPLY, SCOPE_MESSAGE):
        for phrase in INTERNAL_PHRASES:
            assert phrase not in reply.lower(), f"{phrase} leaked in a reply"


def test_system_prompt_never_directs_the_user_to_internal_mechanisms():
    from chat.gemini import SYSTEM_INSTRUCTION

    lowered = SYSTEM_INSTRUCTION.lower()
    assert "chart context block" not in lowered
    assert "never ask them to provide calculated placements" in lowered
    assert "users only ever share ordinary details" in lowered


# --- 7: completion rides the approved pipeline only -----------------------------
def test_completion_uses_build_kundli_and_caches_for_follow_ups(env, client):
    ask(client, "21/01/2010", "pipe-1")
    ask(client, "08:19 am delhi", "pipe-1")
    assert env["seen"]["kundli"] == 1

    ask(client, "what does my chart say about my career?", "pipe-1")
    assert env["seen"]["kundli"] == 1, "the calculated chart is reused, not redrawn"
    assert "KAVACH CHART CONTEXT" in env["seen"]["groq"][-1]["astrology"]
    assert env["seen"]["groq"][-1]["private"] == "", "Tarot stays isolated"
