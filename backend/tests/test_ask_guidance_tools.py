"""Focused tests for the redesigned Ask conversational guidance layer."""

from __future__ import annotations

import pathlib

import pytest
from fastapi.testclient import TestClient

import chat.gemini as gemini
import chat.groq as groq
import chat.natal as natal
import main

REPO = pathlib.Path(__file__).resolve().parents[2]
ASK_PAGE = REPO / "frontend-next" / "app" / "ask" / "page.tsx"

ASK = {"timestamp": "2026-09-25T11:45:00+05:30", "latitude": 28.6139,
       "longitude": 77.209, "timezone": "Asia/Kolkata",
       "location_label": "New Delhi"}


class FakeStore:
    def configured(self):
        return True

    def insert(self, row):
        return "row-1"

    def verify_token(self, token):
        return None


@pytest.fixture()
def env(monkeypatch):
    import archive

    seen = {"groq": [], "gemini": [], "reading": 0, "kundli": 0}
    script = {"groq_text": "A natural answer."}
    monkeypatch.setattr(archive, "store", FakeStore())
    monkeypatch.setattr("chat.reading.sensitive_response", lambda _q: None)

    def fake_reading(_question):
        seen["reading"] += 1
        return {"draw_id": "d1", "cards": []}

    monkeypatch.setattr("chat.reading.build_reading", fake_reading)
    monkeypatch.setattr("chat.reading.private_context", lambda _r: "PRIVATE GUIDANCE")

    def fake_groq(_question, history, private_context="", astrology_context=""):
        seen["groq"].append({"private": private_context, "astrology": astrology_context,
                             "history": list(history)})
        return {"text": script["groq_text"], "model": groq.MODEL,
                "preferred": groq.MODEL, "provider": "groq", "attempts": [],
                "fallback": False}

    monkeypatch.setattr("chat.groq.generate_reply_detailed", fake_groq)
    monkeypatch.setattr("chat.gemini.generate_reply_detailed", lambda *a, **k: {
        "text": "Gemini answer.", "model": "gemini-3.5-flash-lite",
        "preferred": "gemini-3.5-flash-lite", "provider": "gemini", "attempts": [],
    })
    gemini.reset_health()

    import kundli

    original_kundli = kundli.build_kundli

    def counting_kundli(payload):
        seen["kundli"] += 1
        return original_kundli(payload)

    monkeypatch.setattr(kundli, "build_kundli", counting_kundli)
    seen["script"] = script
    yield seen


@pytest.fixture()
def client():
    return TestClient(main.app)


def ask(client, question, conversation_id="guidance-1"):
    return client.post("/api/ask", json={**ASK, "question": question,
                                         "conversation_id": conversation_id}).json()


def test_general_question_stays_in_conversation(env, client):
    body = ask(client, "Explain gravity.")

    assert body["answer"] == "A natural answer."
    assert "tool_action" not in body
    assert env["groq"] and env["kundli"] == 0


def test_personal_guidance_reuses_private_tarot_without_exposing_method(env, client):
    body = ask(client, "I'm confused about a friendship.", "friend-1")

    assert body["answer"] == "A natural answer."
    assert env["reading"] == 1
    assert env["groq"][-1]["private"] == "PRIVATE GUIDANCE"
    assert all(term not in body["answer"].lower() for term in ("tarot", "card", "spread"))


@pytest.mark.parametrize("question,tool,route", [
    ("Tell me about my Kundli", "kundli", "/kundli"),
    ("Where is Saturn in my chart?", "kundli", "/kundli"),
    ("What Mahadasha am I running?", "dasha", "/kundli"),
    ("What is my Navtara?", "navtara", "/kundli"),
    ("Calculate today's detailed prediction", "daily", "/daily"),
    ("Are we compatible astrologically?", "matchmaking", "/compatibility"),
    ("Give me a yes/no reading", "yes_no", "/yes-no"),
    ("Panchang today", "panchang", "/panchang"),
    ("Give me my overall life reading", "life_summary", "/life-summary"),
])
def test_personal_dedicated_requests_return_allowlisted_actions(env, client, question, tool, route):
    body = ask(client, question, f"tool-{tool}")

    assert body["tool_action"] == {"tool": tool, "label": body["tool_action"]["label"], "href": route}
    assert env["groq"] == []
    assert env["reading"] == 0
    assert env["kundli"] == 0
    assert "date of birth" not in body["answer"].lower()
    assert "build_kundli" not in body["answer"]


def test_educational_astrology_stays_in_chat(env, client):
    for question in ("What is Mahadasha?", "What is Navtara?", "What does Saturn generally represent?"):
        body = ask(client, question, f"education-{question[:4]}")
        assert "tool_action" not in body
    assert len(env["groq"]) == 3
    assert env["kundli"] == 0


def test_bare_date_does_not_open_natal_collection(env, client):
    body = ask(client, "21/01/2010", "date-only")

    assert natal.get_state("date-only") is None
    assert "tool_action" not in body
    assert env["kundli"] == 0
    assert env["groq"]


def test_kundli_request_never_calls_build_kundli_inside_ask(env, client):
    body = ask(client, "Tell me about my Kundli", "no-kundli")

    assert body["tool_action"]["tool"] == "kundli"
    assert env["kundli"] == 0
    assert env["groq"] == []


def test_kundli_boundary_does_not_poison_later_conversation(env, client):
    """A Kundli boundary must not force later messages back to Kundli."""
    first = ask(client, "21/01/2010 tell me about my kundli", "after-kundli")
    assert first["tool_action"]["tool"] == "kundli"
    assert "separate chart experience" in first["answer"].lower()

    second = ask(client, "so what can u tell me?", "after-kundli")
    # The follow-up is ordinary conversation, not a repeated Kundli redirect.
    assert "tool_action" not in second
    assert "date of birth" not in second["answer"].lower()

    # A brand-new personal concern is answered conversationally, never Kundli.
    third = ask(client, "okay then how will my day go?", "after-kundli")
    assert third.get("tool_action", {}).get("tool") not in ("kundli", "daily")


@pytest.mark.parametrize("followup", [
    "tell me more", "what about Saturn?", "and Jupiter?", "what does that mean for me?",
    "anything else?", "why?",
])
def test_kundli_followups_never_generate_personal_placements(env, client, followup):
    ask(client, "Tell me about my Kundli", f"sticky-{followup[:3]}")
    body = ask(client, followup, f"sticky-{followup[:3]}")

    assert body.get("tool_action", {}).get("tool") != "kundli"
    assert all(sign not in body["answer"] for sign in (" in Aries", " in Aquarius", " in Capricorn"))


def test_educational_astrology_after_kundli_context_is_allowed(env, client):
    ask(client, "Tell me about my Kundli", "education-after-tool")
    body = ask(client, "What does Saturn generally represent?", "education-after-tool")

    assert "tool_action" not in body
    assert env["groq"]
    assert env["kundli"] == 0


def test_topic_change_clears_kundli_tool_context(env, client):
    ask(client, "Tell me about my Kundli", "change-topic")
    body = ask(client, "anyway explain gravity", "change-topic")
    followup = ask(client, "tell me more", "change-topic")

    assert "tool_action" not in body
    assert "tool_action" not in followup
    assert len(env["groq"]) == 2


def test_dasha_tool_context_survives_followup_without_dasha_calculation(env, client):
    ask(client, "What Mahadasha am I running?", "sticky-dasha")
    body = ask(client, "tell me more", "sticky-dasha")

    assert body["tool_action"]["tool"] == "dasha"
    assert env["groq"] == []


def test_identity_stays_product_level(env, client):
    body = ask(client, "Which model are you?", "identity-1")

    assert "Ask KAVACH" in body["answer"]
    assert all(term not in body["answer"].lower() for term in ("openai", "chatgpt", "groq", "gemini"))
    assert env["groq"] == []


def test_provider_instruction_forbids_personal_astrology_inference():
    from chat.gemini import SYSTEM_INSTRUCTION

    lowered = SYSTEM_INSTRUCTION.lower()
    assert "never calculate, estimate or infer" in lowered
    assert "from a date, time, location" in lowered
    assert "do not ask for birth details" in lowered


def test_welcome_is_exact_static_content_and_not_an_astrology_manual():
    source = ASK_PAGE.read_text(encoding="utf-8")
    expected = (
        "Hi, I’m Ask KAVACH.\\n\\nAsk me what’s on your mind — a situation, decision, relationship,\\n"
        "concern, or simply something you want clarity on. I’ll help you explore\\n"
        "it, and when one of KAVACH’s dedicated tools can give you a better\\nanswer, I’ll take you there."
    )
    assert expected in source
    assert "fetch(`${API_BASE}/ask`" in source
    assert "turns.length === 0" in source
    assert "date of birth" not in source[source.index("const WELCOME_MESSAGE"):source.index(";", source.index("const WELCOME_MESSAGE"))]


# --- hard block: model must never derive personal/date astrology ---------------
PLANET_TOKENS = ("sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn",
                 "rahu", "ketu", "capricorn", "aquarius", "cancer", "libra",
                 "virgo", "sagittarius")


def _no_placements(answer: str) -> bool:
    lowered = answer.lower()
    return not any(token in lowered for token in PLANET_TOKENS)


def test_date_followup_after_kundli_redirect_is_blocked_before_provider(env, client):
    first = ask(client, "21/01/2010 tell me about my kundli", "date-flow")
    assert first["tool_action"]["tool"] == "kundli"

    before = len(env["groq"])
    second = ask(client, "so what can u tell about 21/01/2010", "date-flow")

    assert second["tool_action"]["tool"] == "kundli"
    assert len(env["groq"]) == before, "the follow-up must not reach the provider"
    assert _no_placements(second["answer"])
    assert env["kundli"] == 0


def test_new_chat_astrological_date_request_is_blocked(env, client):
    body = ask(client, "Tell me astrologically about someone born 21 January 2010", "date-new")

    assert body["tool_action"]["tool"] == "kundli"
    assert env["groq"] == []
    assert _no_placements(body["answer"])


def test_new_chat_birth_data_planets_request_is_blocked(env, client):
    body = ask(client, "21 January 2010, 08:19 AM, Delhi — tell me my planets", "date-birth")

    assert body["tool_action"]["tool"] == "kundli"
    assert env["groq"] == []
    assert _no_placements(body["answer"])


def test_new_chat_generic_ask_about_a_birth_date_is_blocked(env, client):
    body = ask(client, "What can you tell me about someone born 21 Jan 2010?", "date-person")

    assert body["tool_action"]["tool"] == "kundli"
    assert env["groq"] == []


def test_moon_sign_on_a_birth_date_is_blocked(env, client):
    body = ask(client, "What sign was the Moon in on 21 Jan 2010?", "date-moon")

    assert body["tool_action"]["tool"] == "kundli"
    assert env["groq"] == []


def test_provider_placements_are_failed_closed_post_provider(env, client):
    env["script"]["groq_text"] = (
        "Sun in Capricorn, Moon in Cancer, Mercury in Capricorn, Venus in "
        "Sagittarius, Mars in Libra (using standard tropical astrology)."
    )
    body = ask(client, "Explain how astrology works in general", "failsafe")

    assert body.get("tool_action", {}).get("tool") == "kundli"
    assert _no_placements(body["answer"])
    assert "tropical" not in body["answer"].lower()


def test_educational_astrology_remains_allowed(env, client):
    for index, question in enumerate((
        "What does Saturn generally represent?",
        "What does Saturn in the 7th house generally mean?",
        "What is a Nakshatra?",
    )):
        before = len(env["groq"])
        body = ask(client, question, f"edu-{index}")
        assert "tool_action" not in body, question
        assert len(env["groq"]) == before + 1, question


def test_user_supplied_placement_interpretation_is_allowed(env, client):
    body = ask(
        client,
        "My Kundli says Saturn is in the 7th house. What does that generally mean?",
        "supplied-fact",
    )

    assert "tool_action" not in body
    assert env["groq"]


def test_ordinary_date_questions_stay_normal(env, client):
    for index, question in enumerate((
        "What day of the week was 21/01/2010?",
        "How old is someone born 21/01/2010?",
        "What happened in the world on 21 January 2010?",
    )):
        before = len(env["groq"])
        body = ask(client, question, f"plain-date-{index}")
        assert "tool_action" not in body, question
        assert len(env["groq"]) == before + 1, question


@pytest.mark.parametrize("question", [
    "How will my day go?",
    "How will today be for me?",
    "What should I focus on today?",
    "I'm nervous about tomorrow.",
    "Will things get better?",
    "I'm confused about a relationship.",
    "Should I talk to this person?",
    "I'm worried about an interview.",
    "I feel stuck. What should I do?",
    "How might this situation unfold?",
])
def test_personal_concerns_are_answered_conversationally(env, client, question):
    """Personal concerns get private guidance, never a forced tool redirect."""
    before = len(env["groq"])
    body = ask(client, question, f"concern-{abs(hash(question)) % 10000}")

    assert body.get("tool_action", {}).get("tool") not in (
        "kundli", "daily", "matchmaking", "yes_no"), question
    assert len(env["groq"]) == before + 1, question
    assert _no_placements(body["answer"])


def test_topic_change_after_kundli_redirect_is_not_blocked(env, client):
    ask(client, "21/01/2010 tell me about my kundli", "topic-change")
    body = ask(client, "anyway explain gravity", "topic-change")
    followup = ask(client, "tell me more", "topic-change")

    assert "tool_action" not in body
    assert "tool_action" not in followup
    assert len(env["groq"]) == 2


# --- astrology companion UX (not a generic assistant) --------------------------
GENERIC_PITCH = ("schoolwork", "science", "history", "story", "homework",
                 "brainstorm", "tutor")


def test_new_concern_after_kundli_is_conversational(env, client):
    """After a Kundli boundary, a new concern is answered conversationally."""
    first = ask(client, "tell me about my kundli 21/01/2010", "companion")
    assert first["tool_action"]["tool"] == "kundli"

    body = ask(client, "okay then how will my day go?", "companion")
    assert body.get("tool_action", {}).get("tool") not in ("kundli", "daily")
    assert "date of birth" not in body["answer"].lower()
    assert _no_placements(body["answer"])


def test_astrology_context_capability_followup_is_tool_specific(env, client):
    """A meta follow-up retains the active dedicated-tool context (not Kundli)."""
    ask(client, "Which dasha am I running?", "companion-dasha")
    body = ask(client, "what can you tell me then", "companion-dasha")

    assert body["tool_action"]["tool"] == "dasha"
    answer = body["answer"].lower()
    assert "dasha" in answer
    assert not any(term in answer for term in GENERIC_PITCH), answer


def test_capability_question_describes_astrology_companion(env, client):
    for index, question in enumerate(("What can you help me with?", "what can you do")):
        before = len(env["groq"])
        body = ask(client, question, f"cap-{index}")
        answer = body["answer"].lower()
        assert "kavach" in answer
        assert "astrolog" in answer or "kundli" in answer
        assert not any(term in answer for term in GENERIC_PITCH), answer
        assert len(env["groq"]) == before, "capability question is answered deterministically"


@pytest.mark.parametrize("question,tool", [
    ("Where is Saturn in my chart?", "kundli"),
    ("Which Mahadasha am I running?", "dasha"),
    ("Tell me my current mahadasha", "dasha"),
    ("What is my Navtara?", "navtara"),
    ("Show my 27 Navtara positions", "navtara"),
    ("Calculate today's detailed prediction", "daily"),
    ("Check compatibility between me and her", "matchmaking"),
    ("Calculate compatibility between us", "matchmaking"),
    ("Are me and this person compatible?", "matchmaking"),
    ("What is today's Tithi?", "panchang"),
    ("Tell me today's Nakshatra", "panchang"),
    ("Give me an overview of my life", "life_summary"),
    ("Show my life summary", "life_summary"),
    ("I need a yes or no answer", "yes_no"),
    ("Give me a strict Yes/No result", "yes_no"),
    ("Calculate my Navtara", "navtara"),
    ("Show my current Dasha timeline", "dasha"),
    ("21/01/2010 tell me my Moon sign", "kundli"),
])
def test_personal_calculation_routes_to_the_right_tool(env, client, question, tool):
    before = len(env["groq"])
    body = ask(client, question, f"route-{tool}-{abs(hash(question)) % 1000}")

    assert body["tool_action"]["tool"] == tool, question
    assert len(env["groq"]) == before, "deterministic tool routes never call the provider"
    assert env["kundli"] == 0


@pytest.mark.parametrize("question", [
    "What is Mahadasha?",
    "What does Navtara mean?",
    "What does Tithi mean?",
    "What does Saturn generally represent?",
    "What is Graha Maitri?",
])
def test_concept_questions_stay_conversational(env, client, question):
    before = len(env["groq"])
    body = ask(client, question, f"concept-{abs(hash(question)) % 1000}")

    assert "tool_action" not in body, question
    assert len(env["groq"]) == before + 1, question


def test_user_supplied_placement_is_interpreted_not_recalculated(env, client):
    before = len(env["groq"])
    body = ask(client, "My Kundli says Moon is in Chitra. Explain it.", "supplied-moon")

    assert "tool_action" not in body
    assert len(env["groq"]) == before + 1


def test_newest_clear_intent_replaces_stale_tool_context(env, client):
    first = ask(client, "Which dasha am I running?", "switch-intent")
    assert first["tool_action"]["tool"] == "dasha"

    second = ask(client, "actually check our compatibility", "switch-intent")
    assert second["tool_action"]["tool"] == "matchmaking"
    assert env["groq"] == []
