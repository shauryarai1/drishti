"""Owner-defined KAVACH Nine Planet Interpretation Framework + product identity.

Scope under test:

1. The nine owner definitions exist centrally and are supplied to the provider
   as KAVACH's authoritative basic planetary meanings (Sun = regular actions,
   Venus = outer connections, ... Ketu = past-life results/acceptance).
2. The framework REACHES Ask joined to the calculated chart, and never without
   it - and never changes a placement. Every sign/house/degree still comes from
   `kundli.build_kundli`.
3. Ask KAVACH product identity is answered deterministically at the product
   level, never exposing the underlying provider/model.
4. Existing 9649ff0 natal grounding, hidden-Tarot isolation, general
   conversation, out-of-scope handling and the safety gate stay intact.

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
from chat.identity import (CREATOR_REPLY, IDENTITY_REPLY, MODEL_REPLY,
                           mentions_provider)

ASK = {"timestamp": "2026-09-25T11:45:00+05:30", "latitude": 28.6139,
       "longitude": 77.209, "timezone": "Asia/Kolkata",
       "location_label": "New Delhi"}

BIRTH = {"date": "1990-05-14", "time": "07:45", "place": "New Delhi, India",
         "latitude": 28.6139, "longitude": 77.209, "timezone": "Asia/Kolkata"}

EXPECTED_CORES = {
    "Sun": "REGULAR ACTIONS",
    "Moon": "CREATION",
    "Mars": "INNER SATISFACTION",
    "Mercury": "SKILLS",
    "Jupiter": "INNER CIRCLE",
    "Venus": "CONNECTIONS",
    "Saturn": "NECESSITY",
    "Rahu": "CONNECT",
    "Ketu": "PAST-LIFE RESULTS",
}


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
    """Mock providers + reading engine; count Groq/Gemini calls and charts."""
    import archive

    seen: dict = {"groq": [], "gemini": [], "readings": 0, "kundli": 0}
    script = {"groq_text": "Groq answer."}

    monkeypatch.setattr(archive, "store", FakeStore())
    monkeypatch.setattr("chat.reading.sensitive_response", lambda _q: None)
    monkeypatch.setattr("chat.reading.build_reading",
                        lambda _q: {"draw_id": "d1", "cards": []})
    monkeypatch.setattr("chat.reading.private_context",
                        lambda _r: "PRIVATE READING CONTEXT")

    def fake_groq(_q, history, private_context="", astrology_context=""):
        seen["groq"].append({"private": private_context,
                             "astrology": astrology_context})
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


def ask(client, question, conversation_id="c1"):
    return client.post("/api/ask", json={**ASK, "question": question,
                                         "conversation_id": conversation_id})


# --- 1. the nine owner definitions -------------------------------------------
@pytest.mark.parametrize("planet,expected", list(EXPECTED_CORES.items()))
def test_each_planet_carries_its_owner_core_meaning(planet, expected):
    core = planet_framework.core_for(planet)
    assert core, f"{planet} has no owner definition"
    assert expected in core


def test_all_nine_planets_are_defined_in_kavach_order():
    assert planet_framework.PLANETS == (
        "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
        "Rahu", "Ketu")
    for planet in planet_framework.PLANETS:
        entry = planet_framework.meaning_for(planet)
        assert entry["core"] and entry["meaning"] and entry["interpret_through"]


def test_framework_distinguishes_venus_outer_from_jupiter_inner():
    venus = planet_framework.meaning_for("Venus")
    jupiter = planet_framework.meaning_for("Jupiter")
    assert "outer" in str(venus["meaning"]).lower()
    assert "inner" in str(jupiter["meaning"]).lower()
    assert "jupiter" in str(venus["guardrail"]).lower(), "distinction is preserved"


def test_guardrails_keep_output_responsible():
    assert "medical" in str(planet_framework.meaning_for("Mars")["guardrail"]).lower()
    assert "no choice" in str(planet_framework.meaning_for("Saturn")["guardrail"]).lower()
    ketu = str(planet_framework.meaning_for("Ketu")["guardrail"]).lower()
    assert "vedic astrology framework" in ketu
    assert "scientifically established" in ketu


def test_usage_rules_forbid_reciting_definitions():
    joined = " ".join(planet_framework.USAGE_RULES).lower()
    assert "do not recite" in joined
    assert "compose" in joined
    assert "marginally relevant" not in joined or "never keyword-match" in joined


# --- 2. the framework reaches Ask with the calculated chart -------------------
def test_framework_is_supplied_with_the_calculated_chart(env, client):
    natal.seed("f1", BIRTH)
    body = ask(client, "Tell me about my Kundli.", "f1").json()

    assert body["answered"] is True
    context = env["seen"]["groq"][0]["astrology"]
    assert "KAVACH CHART CONTEXT" in context
    assert planet_framework.FRAMEWORK_NAME in context
    for planet, core in EXPECTED_CORES.items():
        assert f"{planet} = {planet_framework.SHORT_MAP[planet]}" in context
        assert core.replace(" ", " ").split()[0] in str(
            planet_framework.core_for(planet))
    assert env["seen"]["kundli"] == 1, "placements came from build_kundli"


def test_framework_never_arrives_without_a_calculated_chart(env, client):
    """A general astrology question stays ordinary chat: no chart, no framework."""
    ask(client, "What does Saturn represent in astrology?", "f2")

    assert env["seen"]["groq"][0]["astrology"] == ""
    assert env["seen"]["kundli"] == 0, "no unnecessary personal calculation"


def test_framework_block_states_it_never_computes_placements(env, client):
    natal.seed("f3", BIRTH)
    ask(client, "How is my Jupiter placed?", "f3")

    context = env["seen"]["groq"][0]["astrology"]
    block = planet_framework.context_block()
    assert "never lets you derive a placement" in block
    assert planet_framework.FRAMEWORK_NAME in context
    assert block in context, "the full framework block is supplied verbatim"


def test_framework_composes_with_other_owner_rules_not_replaces(env, client):
    joined = " ".join(planet_framework.USAGE_RULES).lower()
    for owner_rule in ("bnn", "navtara", "retrograde", "combustion",
                       "atmakaraka", "yogakaraka", "dasha"):
        assert owner_rule in joined, f"{owner_rule} must be composed, not replaced"


def test_chart_facts_are_unchanged_by_the_framework(env, client):
    """The framework must not alter what the engine calculated."""
    from kundli.aggregate import build_kundli

    baseline = build_kundli({**BIRTH, "place": BIRTH["place"]})

    natal.seed("f4", BIRTH)
    ask(client, "Tell me about my Kundli.", "f4")
    after = natal.get_state("f4")["chart"]

    # Signs and houses are time-independent, so they must match exactly.
    baseline_signs = {p["planet"]: (p["rashi"], p["house"]) for p in baseline["planets"]}
    after_signs = {p["planet"]: (p["rashi"], p["house"]) for p in after["planets"]}
    assert after_signs == baseline_signs, "framework did not move a placement"
    assert after["summary"]["lagnaRashi"] == baseline["summary"]["lagnaRashi"]
    assert after["summary"]["moonRashi"] == baseline["summary"]["moonRashi"]
    assert after["summary"]["nakshatra"] == baseline["summary"]["nakshatra"]


def test_focused_problem_gets_a_reasoning_lens_not_all_nine(env, client):
    """A focused question is nudged toward the grahas that genuinely bear on it."""
    natal.seed("f5", BIRTH)
    ask(client, "Why does my career keep stalling in my chart?", "f5")

    context = env["seen"]["groq"][0]["astrology"]
    hint = planet_framework.lens_hint("Why does my career keep stalling in my chart?")
    assert hint, "a recognisable personal problem maps to a KAVACH lens"
    assert hint in context
    assert "guidance only" in hint.lower()
    expected = planet_framework.planets_for_lenses(
        planet_framework.relevant_lenses("Why does my career keep stalling in my chart?"))
    for planet in expected:
        assert planet in hint, f"{planet} is genuinely relevant here"
    # Not all nine are dumped: the hint names only the lenses that apply.
    assert len(expected) < len(planet_framework.PLANETS)


def test_lens_is_absent_for_a_generic_question(env, client):
    assert planet_framework.lens_hint("What is gravity?") == ""


# --- 3. product identity ------------------------------------------------------
@pytest.mark.parametrize("question", [
    "Who are you?", "What are you?", "Are you ChatGPT?", "Are you OpenAI?",
    "what is your name", "are you a bot",
])
def test_identity_questions_answer_from_the_product(env, client, question):
    body = ask(client, question, "id-1").json()

    assert body["answered"] is True
    assert "KAVACH" in body["answer"]
    assert not mentions_provider(body["answer"]), \
        f"provider leaked in: {body['answer']}"


def test_identity_is_an_astrology_companion(env, client):
    """Identity presents KAVACH's astrological companion, not a generic assistant."""
    body = ask(client, "Who are you?", "id-only").json()
    answer = body["answer"].lower()

    assert "ask kavach" in answer
    assert "astrolog" in answer or "kundli" in answer
    assert "general-purpose assistant" not in answer


def test_purpose_question_describes_astrology_companion(env, client):
    """'What can you do?' describes astrology capabilities, not generic ones."""
    body = ask(client, "what can you do", "id-both").json()
    answer = body["answer"].lower()

    assert "astrolog" in answer or "kundli" in answer
    assert "general-purpose assistant" not in answer


def test_identity_questions_never_spend_provider_quota(env, client):
    ask(client, "Who are you?", "id-2")

    assert env["seen"]["groq"] == [], "no Groq call for an identity question"
    assert env["seen"]["gemini"] == [], "no Gemini call for an identity question"
    assert env["seen"]["kundli"] == 0


@pytest.mark.parametrize("question", ["Which model are you?", "what model are you"])
def test_model_question_returns_product_identity(env, client, question):
    body = ask(client, question, "id-3").json()

    assert body["answer"] == MODEL_REPLY
    assert not mentions_provider(body["answer"])


@pytest.mark.parametrize("question", ["Who made you?", "who built you"])
def test_creator_question_stays_at_kavach_level(env, client, question):
    body = ask(client, question, "id-4").json()

    assert body["answer"] == CREATOR_REPLY
    assert "KAVACH" in body["answer"]
    assert not mentions_provider(body["answer"])


@pytest.mark.parametrize("question", ["your purpose", "what can you do"])
def test_purpose_question_describes_the_product(env, client, question):
    body = ask(client, question, "id-5").json()

    assert "KAVACH" in body["answer"]
    assert not mentions_provider(body["answer"])
    assert "astrolog" in body["answer"].lower() or "kundli" in body["answer"].lower()


# --- 4. preserved behaviour ---------------------------------------------------
def test_general_non_astrology_question_still_answers_normally(env, client):
    """General conversation is untouched by the framework and costs no chart."""
    env["script"]["groq_text"] = "25 times 16 is 400."
    body = ask(client, "What is 25 times 16?", "g1").json()

    assert body["answered"] is True
    assert "400" in body["answer"]
    assert env["seen"]["kundli"] == 0
    assert env["seen"]["groq"][0]["astrology"] == "", \
        "no chart or framework context for general chat"


def test_hidden_tarot_isolation_still_holds(env, client):
    """A chart question must never receive the private reading context."""
    ask(client, "will I be successful in life?", "iso")
    assert env["seen"]["groq"][-1]["private"] == "PRIVATE READING CONTEXT"

    natal.seed("iso", BIRTH)
    ask(client, "Tell me about my Kundli.", "iso")
    assert env["seen"]["groq"][-1]["private"] == "", \
        "reading context never leaks into a chart answer"
    assert planet_framework.FRAMEWORK_NAME in env["seen"]["groq"][-1]["astrology"]


def test_natal_gate_still_asks_for_missing_details(env, client):
    body = ask(client, "Tell me about my Kundli.", "fresh").json()

    assert body["answered"] is True
    assert "date of birth" in body["answer"].lower()
    assert env["seen"]["kundli"] == 0, "nothing is invented without details"


def test_no_invented_placement_is_survives_scrubbing(env, client):
    """A fabricated placement claim is still dropped with the framework active."""
    natal.seed("scrub", BIRTH)
    env["script"]["groq_text"] = (
        "Your Sun is in Pisces in the 4th house. Generally stay focused.")
    body = ask(client, "Tell me about my Kundli.", "scrub").json()

    answer = body["answer"]
    chart = natal.get_state("scrub")["chart"]
    actual_sun_sign = next(p["rashi"] for p in chart["planets"]
                           if p["planet"] == "Sun")
    if actual_sun_sign != "Pisces":
        assert "Pisces" not in answer, "fabricated Sun placement was scrubbed"


def test_live_data_is_still_refused_deterministically(env, client):
    body = ask(client, "will it rain tomorrow?", "o1").json()

    assert body["answered"] is True
    assert env["seen"]["kundli"] == 0
    assert env["seen"]["groq"] == [], "a refusal never reaches a provider"


def test_follow_up_reuses_the_calculated_chart(env, client):
    natal.seed("reuse", BIRTH)
    ask(client, "Tell me about my Kundli.", "reuse")
    ask(client, "what about my Mars?", "reuse")

    assert env["seen"]["kundli"] == 1, "the chart is calculated once and reused"
    assert planet_framework.FRAMEWORK_NAME in env["seen"]["groq"][-1]["astrology"]
