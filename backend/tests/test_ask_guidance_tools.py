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
    ("What's today's prediction for Aries?", "daily", "/daily"),
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


def test_kundli_tool_context_survives_ambiguous_followup(env, client):
    first = ask(client, "21/01/2010 tell me about my kundli", "sticky-kundli")
    second = ask(client, "so what can u tell me?", "sticky-kundli")

    assert first["tool_action"]["tool"] == "kundli"
    assert second["tool_action"]["tool"] == "kundli"
    assert "date of birth" not in second["answer"].lower()
    assert env["groq"] == [], "ambiguous personal-chart follow-up is blocked before the model"


@pytest.mark.parametrize("followup", [
    "tell me more", "what about Saturn?", "and Jupiter?", "what does that mean for me?",
    "anything else?", "why?",
])
def test_kundli_followups_never_generate_personal_placements(env, client, followup):
    ask(client, "Tell me about my Kundli", f"sticky-{followup[:3]}")
    body = ask(client, followup, f"sticky-{followup[:3]}")

    assert body["tool_action"]["tool"] == "kundli"
    assert env["groq"] == []
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


def test_contextual_kundli_followups_make_zero_provider_calls(env, client):
    ask(client, "Tell me about my Kundli", "zero-provider")
    before = len(env["groq"])
    for index, followup in enumerate(("tell me more", "what about Saturn?", "and Jupiter?")):
        body = ask(client, followup, "zero-provider")
        assert body["tool_action"]["tool"] == "kundli"
        assert len(env["groq"]) == before, f"{followup} reached the provider"
        assert _no_placements(body["answer"])


def test_topic_change_after_kundli_redirect_is_not_blocked(env, client):
    ask(client, "21/01/2010 tell me about my kundli", "topic-change")
    body = ask(client, "anyway explain gravity", "topic-change")
    followup = ask(client, "tell me more", "topic-change")

    assert "tool_action" not in body
    assert "tool_action" not in followup
    assert len(env["groq"]) == 2
