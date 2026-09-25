"""Ask KAVACH natal grounding: calculated Kundli or birth details, never a third path.

Root behaviour under test: a personal chart question is answered ONLY from the
existing KAVACH Kundli engine (`kundli.build_kundli`, Swiss Ephemeris/Lahiri,
the /api/kundli pipeline), or with a deterministic request for the missing
birth details. The model is never allowed to invent, derive or calculate a
placement itself; birth details are collected conversationally, the calculated
chart is reused for follow-ups, a corrected detail forces recalculation and
fabricated claims are scrubbed from the output. Readings, reading follow-ups,
out-of-scope requests, safety handling and the provider order are untouched.
Providers are mocked - zero live quota, zero geocoding quota.
"""

from __future__ import annotations

import pathlib

import pytest
from fastapi.testclient import TestClient

import chat.gemini as gemini
import chat.groq as groq
import chat.natal as natal
import chat.router as router
import main
from kundli.aggregate import build_kundli as raw_build_kundli

ASK = {"timestamp": "2026-09-25T11:45:00+05:30", "latitude": 28.6139,
       "longitude": 77.209, "timezone": "Asia/Kolkata",
       "location_label": "New Delhi"}

BIRTH = {"date": "1990-05-14", "time": "07:45", "place": "New Delhi, India",
         "latitude": 28.6139, "longitude": 77.209, "timezone": "Asia/Kolkata"}

# The geocoder only resolves this city, so a stray query can never pass.
GEOCODED = {"Jaipur": (26.9124, 75.7873)}


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
    import chat.reading as reading_module

    seen: dict = {"groq": [], "gemini": [], "geocode": [], "kundli": 0,
                  "readings": 0}
    script = {"groq_text": "Groq answer."}

    monkeypatch.setattr(archive, "store", FakeStore())
    monkeypatch.setattr("chat.reading.sensitive_response", lambda _q: None)

    original_build = reading_module.build_reading

    def counting_build(question):
        seen["readings"] += 1
        return original_build(question)

    monkeypatch.setattr("chat.reading.build_reading", counting_build)
    monkeypatch.setattr("chat.reading.private_context", lambda _r: "PRIVATE READING CONTEXT")

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

    original_kundli = kundli_module.build_kundli

    def counting_kundli(payload):
        seen["kundli"] += 1
        return original_kundli(payload)

    monkeypatch.setattr(kundli_module, "build_kundli", counting_kundli)
    yield {"seen": seen, "script": script}


@pytest.fixture()
def client():
    return TestClient(main.app)


def ask(client, question, conversation_id):
    return client.post("/api/ask", json={**ASK, "question": question,
                                         "conversation_id": conversation_id}).json()


# --- 1: no birth details -> deterministic ask, never the model ---------------
def test_chart_question_without_birth_details_asks_deterministically(env, client):
    body = ask(client, "What does Saturn mean in my chart?", "natal-1")

    assert body["answered"] is True
    assert "date of birth" in body["answer"].lower()
    assert "birth time" in body["answer"].lower()
    assert "birth place" in body["answer"].lower()
    assert env["seen"]["groq"] == [], "no provider may answer without a chart"
    assert env["seen"]["gemini"] == []
    assert env["seen"]["kundli"] == 0, "nothing to calculate yet"
    assert "CHART CONTEXT" not in body["answer"]


# --- 2: birth details are collected across turns ----------------------------
def test_birth_details_are_collected_across_turns(env, client):
    first = ask(client, "read my kundli", "natal-2")
    assert "date of birth" in first["answer"].lower()

    second = ask(client, "23.11.2009", "natal-2")
    assert "time" in second["answer"].lower()
    assert "where" in second["answer"].lower()

    third = ask(client, "2:30 pm", "natal-2")
    assert "where were you born" in third["answer"].lower()

    fourth = ask(client, "Jaipur", "natal-2")
    assert fourth["answered"] is True
    assert env["seen"]["geocode"] == ["Jaipur"], "the place is geocoded once"
    assert env["seen"]["groq"], "the completed flow finally reaches the model"
    assert "CHART CONTEXT" in env["seen"]["groq"][-1]["astrology"]

    state = natal.get_state("natal-2")
    assert state["date"] == "2009-11-23"
    assert state["time"] == "14:30"
    assert state["place"] == "Jaipur"


# --- 3: the context IS the calculated Kundli --------------------------------
def test_chart_context_comes_from_the_calculated_kundli(env, client):
    expected = raw_build_kundli(dict(BIRTH))
    natal.seed("natal-3", BIRTH)

    ask(client, "read my kundli", "natal-3")
    context = env["seen"]["groq"][-1]["astrology"]

    assert "CHART CONTEXT" in context
    assert f"Birth: {BIRTH['date']} {BIRTH['time']}" in context
    assert expected["summary"]["lagnaRashi"] in context
    assert expected["summary"]["moonRashi"] in context
    assert expected["summary"]["nakshatra"] in context
    assert any(planet["planet"] in context for planet in expected["planets"])
    assert env["seen"]["geocode"] == [], "coordinates were already supplied"
    assert env["seen"]["kundli"] == 1


# --- 4: the prompt forbids a third path -------------------------------------
def test_prompt_forbids_the_model_from_calculating_placements():
    from chat.gemini import (ASTROLOGY_INSTRUCTION, SYSTEM_INSTRUCTION,
                             _system_instruction_for)

    assert ("unless an authoritative calculated chart context block is supplied"
            in SYSTEM_INSTRUCTION)
    assert ("Birth details mentioned in the conversation are not permission to "
            "calculate" in SYSTEM_INSTRUCTION)
    assert "never recalculate or derive a placement yourself" in ASTROLOGY_INSTRUCTION.lower()
    assert "only source of truth about this person's chart" in ASTROLOGY_INSTRUCTION

    # Without a chart context the astrology instruction is never attached, and
    # the default system prompt still forbids personal placements.
    assert _system_instruction_for("") == SYSTEM_INSTRUCTION
    assert "Never invent chart data" in SYSTEM_INSTRUCTION


def test_general_astrology_gets_no_chart_context_and_no_calculation(env, client):
    body = ask(client, "What is Saturn?", "natal-4b")

    assert body["answered"] is True
    assert env["seen"]["groq"][-1]["astrology"] == "", "no context, no chart"
    assert env["seen"]["kundli"] == 0


# --- 5: fabricated claims are scrubbed from the output ----------------------
def test_fabricated_placements_are_stripped_from_the_answer(env, client):
    expected = raw_build_kundli(dict(BIRTH))
    lagna = expected["summary"]["lagnaRashi"]
    moon = expected["summary"]["moonRashi"]
    saturn = next(p for p in expected["planets"] if p["planet"] == "Saturn")["rashi"]
    unused = [sign for sign in natal.SIGNS if sign not in (lagna, moon, saturn)]
    wrong_lagna, wrong_moon, wrong_saturn = unused[0], unused[1], unused[2]

    natal.seed("natal-5", BIRTH)
    env["script"]["groq_text"] = (
        f"Your ascendant is {wrong_lagna}. Your Moon sign is {wrong_moon}. "
        f"Saturn is in {wrong_saturn}. You are doing fine."
    )
    body = ask(client, "read my kundli", "natal-5")

    assert wrong_lagna not in body["answer"]
    assert wrong_moon not in body["answer"]
    assert wrong_saturn not in body["answer"]
    assert "You are doing fine." in body["answer"]


def test_grounded_statements_survive_the_scrub(env, client):
    expected = raw_build_kundli(dict(BIRTH))
    lagna = expected["summary"]["lagnaRashi"]

    natal.seed("natal-5b", BIRTH)
    env["script"]["groq_text"] = f"Your ascendant is {lagna}. Saturn brings discipline."
    body = ask(client, "read my kundli", "natal-5b")

    assert f"Your ascendant is {lagna}." in body["answer"]
    assert "Saturn brings discipline." in body["answer"]


def test_an_entirely_fabricated_answer_falls_back_to_a_grounded_reply(env, client):
    expected = raw_build_kundli(dict(BIRTH))
    unused = [sign for sign in natal.SIGNS
              if sign not in (expected["summary"]["lagnaRashi"],
                              expected["summary"]["moonRashi"])]

    natal.seed("natal-5c", BIRTH)
    env["script"]["groq_text"] = (
        f"Your ascendant is {unused[0]}. Your Moon sign is {unused[1]}."
    )
    body = ask(client, "read my kundli", "natal-5c")

    assert body["answer"] == natal.CHART_FALLBACK_REPLY
    assert unused[0] not in body["answer"]


# --- 6: the calculated chart is reused for follow-ups -----------------------
def test_chart_is_calculated_once_and_reused_for_follow_ups(env, client):
    natal.seed("natal-6", BIRTH)

    ask(client, "read my kundli", "natal-6")
    ask(client, "what about Jupiter?", "natal-6")
    ask(client, "and my dasha?", "natal-6")

    assert env["seen"]["kundli"] == 1, "the cached chart is reused"
    assert len(env["seen"]["groq"]) == 3
    assert all(item["astrology"] for item in env["seen"]["groq"])
    assert all(item["private"] == "" for item in env["seen"]["groq"])


# --- 7: a corrected detail invalidates and recalculates ---------------------
def test_corrected_birth_date_recalculates_the_chart(env, client):
    natal.seed("natal-7", BIRTH)
    ask(client, "read my kundli", "natal-7")
    assert env["seen"]["kundli"] == 1

    ask(client, "sorry, my date of birth is actually 5.5.1995", "natal-7")

    assert env["seen"]["kundli"] == 2, "a correction forces recalculation"
    assert natal.get_state("natal-7")["date"] == "1995-05-05"
    assert "1995-05-05" in env["seen"]["groq"][-1]["astrology"]


# --- 8: ordinary chat is never hijacked by the collection flow --------------
def test_chit_chat_during_collection_is_not_hijacked(env, client):
    ask(client, "read my kundli", "natal-8")  # state open, details missing

    body = ask(client, "thanks", "natal-8")

    assert body["answer"] == "Groq answer."
    assert env["seen"]["groq"][-1]["astrology"] == ""
    assert env["seen"]["kundli"] == 0


# --- 9: natal state never leaks between conversations -----------------------
def test_natal_state_is_isolated_per_conversation(env, client):
    natal.seed("natal-9a", BIRTH)

    body = ask(client, "read my chart", "natal-9b")

    assert "date of birth" in body["answer"].lower(), "a fresh conversation starts over"
    assert env["seen"]["kundli"] == 0
    assert natal.get_state("natal-9a")["date"] == BIRTH["date"]


# --- 10: reading and chart contexts stay isolated ---------------------------
def test_reading_and_chart_contexts_stay_isolated(env, client):
    ask(client, "will i be successful?", "natal-10")
    assert env["seen"]["readings"] == 1
    assert env["seen"]["groq"][-1]["private"] == "PRIVATE READING CONTEXT"
    assert env["seen"]["groq"][-1]["astrology"] == ""

    natal.seed("natal-10", BIRTH)
    ask(client, "read my kundli", "natal-10")

    assert env["seen"]["readings"] == 1, "a chart question never redraws"
    assert env["seen"]["groq"][-1]["private"] == "", "no Tarot on a chart answer"
    assert "CHART CONTEXT" in env["seen"]["groq"][-1]["astrology"]


# --- 11: personal readings are never blocked by the natal flow --------------
def test_personal_reading_questions_never_enter_the_natal_flow(env, client):
    natal.seed("natal-11", BIRTH)

    body = ask(client, "will my business succeed?", "natal-11")

    assert body["answered"] is True
    assert env["seen"]["readings"] == 1, "the reading is still drawn"
    assert env["seen"]["groq"][-1]["private"] == "PRIVATE READING CONTEXT"
    assert env["seen"]["groq"][-1]["astrology"] == ""
    assert env["seen"]["kundli"] == 0, "a reading never triggers a chart"


# --- 12: safety and out-of-scope still answer first, without providers ------
def test_safety_gate_is_answered_before_any_natal_flow(env, client, monkeypatch):
    monkeypatch.setattr("chat.reading.sensitive_response",
                        lambda _q: "Real-world support comes first.")
    body = ask(client, "I want to kill myself", "natal-12")

    assert body["answer"] == "Real-world support comes first."
    assert env["seen"]["groq"] == []
    assert natal.get_state("natal-12") is None


def test_live_data_is_still_answered_without_a_provider(env, client):
    body = ask(client, "will it rain tomorrow?", "natal-12b")

    assert body["answer"] == router.SCOPE_MESSAGE
    assert env["seen"]["groq"] == [] and env["seen"]["gemini"] == []
    assert env["seen"]["kundli"] == 0


# --- 13: an unknown birth place asks again, deterministically ---------------
def test_unknown_birth_place_asks_again_without_a_provider(env, client):
    ask(client, "read my kundli", "natal-13")
    ask(client, "23.11.2009", "natal-13")
    ask(client, "14:30", "natal-13")

    body = ask(client, "Gotham City", "natal-13")

    assert "couldn't find" in body["answer"].lower()
    assert env["seen"]["geocode"] == ["Gotham City"]
    assert env["seen"]["groq"] == [], "an unresolvable place never reaches the model"


# --- 14: guest flow, no account, no profile --------------------------------
def test_natal_flow_is_guest_only_and_reads_no_profile(env, client):
    source = (pathlib.Path(natal.__file__).resolve()).read_text(encoding="utf-8")
    for forbidden in ("Authorization", "supabase", "SUPABASE", "service_role",
                      "profile", "JWT"):
        assert forbidden not in source, forbidden

    # The whole collection flow works with no credentials on the request.
    natal.reset("natal-14")
    ask(client, "read my kundli", "natal-14")
    body = ask(client, "23.11.2009 14:30 Jaipur", "natal-14")

    assert body["answered"] is True
    assert "CHART CONTEXT" in env["seen"]["groq"][-1]["astrology"]


# --- 15: provider architecture is unchanged --------------------------------
def test_provider_order_is_unchanged_with_chart_context(env, client, monkeypatch):
    natal.seed("natal-15", BIRTH)
    monkeypatch.setattr("chat.groq.generate_reply_detailed",
                        lambda *a, **k: {"text": None, "provider": "groq",
                                         "preferred": groq.MODEL,
                                         "attempts": [{"model": groq.MODEL,
                                                       "reason": "timeout"}],
                                         "fallback": True})

    body = ask(client, "read my kundli", "natal-15")

    assert body["answer"] == "Gemini answer.", "Gemini stays the fallback"
    assert env["seen"]["gemini"], "the fallback received the request"
    assert "CHART CONTEXT" in env["seen"]["gemini"][-1]["astrology"], \
        "the chart context reaches the fallback provider too"


# --- detail parsers ---------------------------------------------------------
def test_detail_parsers_handle_common_formats():
    assert natal.parse_date("23.11.2009") == "2009-11-23"
    assert natal.parse_date("23rd November 2009") == "2009-11-23"
    assert natal.parse_date("November 23, 2009") == "2009-11-23"
    assert natal.parse_date("2009-11-23") == "2009-11-23"
    assert natal.parse_date("31.02.2000") is None, "an impossible date is rejected"
    assert natal.parse_date("I was born in 2009") is None, "a year alone is not a date"

    assert natal.parse_time("14:30") == "14:30"
    assert natal.parse_time("2:30 pm") == "14:30"
    assert natal.parse_time("12:00 am") == "00:00"
    assert natal.parse_time("nine o'clock") is None


def test_only_personal_chart_questions_trigger_the_natal_flow():
    assert natal.needs_natal("What does Saturn mean in my chart?")
    assert natal.needs_natal("read my kundli")
    assert natal.needs_natal("how is my dasha?")
    assert natal.needs_natal("What did my 2010 chart say about Mars?")
    assert natal.needs_natal("Which house is Mars in?")
    assert natal.needs_natal("How will my business go as per my chart?")

    assert not natal.needs_natal("What is Saturn?")
    assert not natal.needs_natal("Explain retrograde")
    assert not natal.needs_natal("what is my career going to be")
