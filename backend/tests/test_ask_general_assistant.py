"""Ask KAVACH is a GENERAL conversational assistant with astrology as a capability.

Astrology must never look like the boundary of Ask's intelligence. This file
proves the product behaves as:

    GENERAL CONVERSATIONAL ASSISTANT
              + KAVACH ASTROLOGY CAPABILITIES
              + PERSONAL KUNDLI CONTEXT WHEN NEEDED

Ten required checks: general questions answered, follow-ups use history,
non-astrology personal problems get normal help, astrology gets astrology
knowledge, chart questions hit the calculated Kundli path, the nine-planet
framework stays out of unrelated chat, identity is not astrology-only, the
welcome advertises both, no provider leaks, and 9649ff0 grounding still works.

Providers, geocoder and reading engine are mocked: zero live quota.
"""

from __future__ import annotations

import pathlib

import pytest
from fastapi.testclient import TestClient

import chat.gemini as gemini
import chat.groq as groq
import chat.natal as natal
import chat.planet_framework as planet_framework
import chat.router as router
import main
from chat.identity import mentions_provider

ASK = {"timestamp": "2026-09-25T11:45:00+05:30", "latitude": 28.6139,
       "longitude": 77.209, "timezone": "Asia/Kolkata",
       "location_label": "New Delhi"}

BIRTH = {"date": "1990-05-14", "time": "07:45", "place": "New Delhi, India",
         "latitude": 28.6139, "longitude": 77.209, "timezone": "Asia/Kolkata"}

# Static first-run greeting rendered by the Ask page (single source of truth).
ASK_PAGE = (pathlib.Path(__file__).resolve().parents[2]
            / "frontend-next" / "app" / "ask" / "page.tsx")


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
    """Mock providers + reading engine; count calls, charts and context use."""
    import archive

    seen: dict = {"groq": [], "gemini": [], "readings": 0, "kundli": 0}

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
        return {"text": "A natural conversational reply.", "model": groq.MODEL,
                "preferred": groq.MODEL, "provider": "groq", "attempts": [],
                "fallback": False}

    def fake_gemini(_q, history, private_context="", astrology_context=""):
        seen["gemini"].append({"private": private_context,
                               "astrology": astrology_context})
        return {"text": "Gemini reply.", "model": "gemini-3.5-flash-lite",
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
    yield seen


@pytest.fixture()
def client():
    return TestClient(main.app)


def ask(client, question, conversation_id="c1"):
    return client.post("/api/ask", json={**ASK, "question": question,
                                         "conversation_id": conversation_id})


# --- 1. normal general question answered normally -----------------------------
@pytest.mark.parametrize("question", [
    "Why is the sky blue?",
    "What is 25 times 16?",
    "translate this sentence into French",
    "write an email to my teacher",
    "explain this code",
    "give me a recipe for pasta",
])
def test_normal_general_questions_are_answered(env, client, question):
    body = ask(client, question, "gen-1").json()

    assert body["answered"] is True
    assert body["answer"] != router.SCOPE_MESSAGE, \
        "a harmless non-astrology question must never get the scope message"
    assert env["groq"], "the assistant actually answered"
    assert env["kundli"] == 0, "no chart calculation for general chat"


def test_astrology_words_are_not_required_to_be_answered(env, client):
    """The reply must never be gated on astrology keywords."""
    body = ask(client, "Who was the first person on the moon?", "gen-2").json()

    assert body["answered"] is True
    assert body["answer"] != router.SCOPE_MESSAGE


# --- 2. short follow-ups use conversation history ------------------------------
@pytest.mark.parametrize("follow_up", [
    "simpler", "give example", "why?", "explain that", "okay", "then?",
    "make it simpler", "and relationships?", "no I meant career",
])
def test_short_follow_ups_are_resolved_with_history(env, client, follow_up):
    """Follow-ups are answered, and the previous turns are passed to the model."""
    ask(client, "Explain how photosynthesis works.", "conv-1")
    history_before = len(env["groq"][-1]["history"])

    body = ask(client, follow_up, "conv-1").json()

    assert body["answered"] is True
    assert body["answer"] != router.SCOPE_MESSAGE, f"{follow_up} was refused"
    # The earlier exchange is passed to the assistant, not treated in isolation.
    assert len(env["groq"][-1]["history"]) >= history_before
    joined = " ".join(str(item.get("content", "")) for item in env["groq"][-1]["history"])
    assert "photosynthesis" in joined.lower(), "prior topic is in the transcript"


def test_follow_up_never_forces_astrology_context(env, client):
    ask(client, "Why is the sky blue?", "conv-2")
    body = ask(client, "why?", "conv-2").json()

    assert body["answered"] is True
    assert env["groq"][-1]["astrology"] == "", \
        "a general follow-up carries no chart or framework context"


# --- 3. non-astrology personal problem -> normal help --------------------------
def test_personal_problem_without_chart_intent_gets_normal_help(env, client):
    """Not every personal problem is astrology-analysed."""
    body = ask(
        client,
        "I'm having trouble concentrating while studying. What can I do?",
        "study-1").json()

    assert body["answered"] is True
    assert env["kundli"] == 0, "no chart was calculated - no chart was requested"
    assert env["groq"][-1]["astrology"] == "", "no chart context supplied"
    # Optionally offered the reading, but never an unrequested chart analysis.
    assert env["readings"] <= 1


def test_same_problem_with_chart_intent_uses_the_kundli(env, client):
    """The identical topic WITH chart intent takes the astrology path."""
    natal.seed("study-2", BIRTH)
    ask(client, "Why do I struggle to concentrate according to my Kundli?",
        "study-2")

    assert env["kundli"] == 1, "the chart was calculated for a chart question"
    assert "KAVACH CHART CONTEXT" in env["groq"][-1]["astrology"]


# --- 4. astrology question -> astrology explanation ----------------------------
@pytest.mark.parametrize("question", [
    "What does Mars represent?",
    "tell me about Saturn",
    "what is a nakshatra?",
])
def test_general_astrology_questions_reach_the_assistant(env, client, question):
    body = ask(client, question, "astro-1").json()

    assert body["answered"] is True
    assert env["groq"], "answered naturally by the assistant"
    assert env["kundli"] == 0, "general astrology needs no personal calculation"


# --- 5. personal Kundli question -> calculated Kundli path ---------------------
@pytest.mark.parametrize("question", [
    "tell me about my kundli",
    "what is my lagna?",
    "where is my Saturn?",
    "what does my chart say about relationships?",
])
def test_personal_chart_questions_use_the_calculated_kundli(env, client, question):
    conversation_id = "chart-" + str(abs(hash(question)) % 10000)
    natal.seed(conversation_id, BIRTH)
    body = ask(client, question, conversation_id).json()

    assert body["answered"] is True
    context = env["groq"][-1]["astrology"]
    assert "KAVACH CHART CONTEXT" in context, "placements came from build_kundli"
    assert planet_framework.FRAMEWORK_NAME in context
    assert env["kundli"] == 1


# --- 6. the framework only applies where astrology/chart requires it -----------
def test_framework_does_not_leak_into_general_conversation(env, client):
    """The nine-planet framework must stay out of unrelated chat."""
    ask(client, "Why is the sky blue?", "leak-1")
    assert planet_framework.FRAMEWORK_NAME not in env["groq"][-1]["astrology"]

    ask(client, "give me a recipe for pasta", "leak-1")
    assert planet_framework.FRAMEWORK_NAME not in env["groq"][-1]["astrology"]
    assert env["groq"][-1]["astrology"] == ""


def test_framework_does_not_leak_into_an_astrology_definition_question(env, client):
    """Even an astrology question only gets the framework with a real chart."""
    ask(client, "What does Mars represent?", "leak-2")

    context = env["groq"][-1]["astrology"]
    assert planet_framework.FRAMEWORK_NAME not in context
    assert env["kundli"] == 0


def test_framework_arrives_only_with_the_calculated_chart(env, client):
    natal.seed("leak-3", BIRTH)
    ask(client, "tell me about my kundli", "leak-3")

    assert planet_framework.FRAMEWORK_NAME in env["groq"][-1]["astrology"]


# --- 7. identity is not astrology-only -----------------------------------------
def test_identity_advertises_general_assistance_and_astrology(env, client):
    body = ask(client, "Who are you?", "who-1").json()
    answer = body["answer"]

    assert "Ask KAVACH" in answer
    assert "ai assistant" in answer.lower()
    astrology_words = ("astrology", "kundli")
    assert any(word in answer.lower() for word in astrology_words)
    general_words = ("chat", "questions", "tasks", "everyday")
    assert any(word in answer.lower() for word in general_words), \
        "identity must not make astrology sound like the only job"
    assert not mentions_provider(answer)


# --- 8. welcome message advertises both ---------------------------------------
def test_welcome_message_covers_general_and_astrology():
    """The static greeting presents both capabilities and costs no API call."""
    source = ASK_PAGE.read_text(encoding="utf-8")
    assert "WELCOME_MESSAGE" in source, "the greeting is a static constant"

    start = source.index("const WELCOME_MESSAGE")
    block = source[start:source.index(";", start)].lower()

    assert "ask anything" in block or "anything" in block
    assert "explanations" in block or "ideas" in block
    assert "writing" in block
    assert "kundli" in block and "astrology" in block
    # Rendered only for a fresh conversation, and never via the API.
    assert "turns.length === 0" in source
    assert "api_base" not in block


# --- 9. no provider/model leakage ----------------------------------------------
@pytest.mark.parametrize("question", [
    "Who are you?", "Which model are you?", "Who made you?", "what can you do",
])
def test_no_provider_or_model_leakage(env, client, question):
    body = ask(client, question, f"leak-{question[:6]}").json()

    assert not mentions_provider(body["answer"]), body["answer"]


# --- 10. existing natal grounding still works ----------------------------------
def test_natal_gate_still_collects_missing_details(env, client):
    """9649ff0: no chart details means a deterministic request, no invention."""
    body = ask(client, "tell me about my kundli", "fresh").json()

    assert body["answered"] is True
    assert "date of birth" in body["answer"].lower()
    assert env["kundli"] == 0, "nothing is invented without details"
    assert env["groq"] == [], "no provider call for the details request"


def test_chart_is_calculated_once_and_reused(env, client):
    natal.seed("reuse-1", BIRTH)
    ask(client, "tell me about my kundli", "reuse-1")
    ask(client, "what about my Mars?", "reuse-1")

    assert env["kundli"] == 1, "the chart is calculated once and reused"


def test_hidden_tarot_isolation_still_holds(env, client):
    """A chart answer never receives the private reading context."""
    ask(client, "will my project work?", "iso-1")
    assert env["groq"][-1]["private"] == "PRIVATE READING CONTEXT"

    natal.seed("iso-1", BIRTH)
    ask(client, "tell me about my kundli", "iso-1")
    assert env["groq"][-1]["private"] == "", "reading never leaks to a chart answer"


def test_live_data_requests_are_still_refused(env, client):
    """The only remaining deterministic refusal: unproducible live data."""
    body = ask(client, "will it rain tomorrow?", "rain-1").json()

    assert body["answered"] is True
    assert body["answer"] == router.SCOPE_MESSAGE
    assert env["groq"] == [], "no provider call for a refusal"
