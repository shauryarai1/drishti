"""Ask KAVACH: personal uncertainty/questions use the hidden KAVACH reading.

Requirement: personal predictive/decision questions ("will i be successful
moneywise?") must answer FROM the existing hidden Tarot reading, while general
knowledge questions stay ordinary chat and explicit astrology questions keep the
astrology context. Providers are mocked - zero live quota.
"""

from __future__ import annotations

import json
import pathlib

import pytest
from fastapi.testclient import TestClient

import archive
import chat.gemini as gemini
import chat.groq as groq
import chat.router as router
import main
from chat.gemini import SYSTEM_INSTRUCTION, _system_instruction_for

REPO = pathlib.Path(__file__).resolve().parents[2]
ASK = {"timestamp": "2026-09-22T11:45:00+05:30", "latitude": 28.6139, "longitude": 77.209,
       "timezone": "Asia/Kolkata"}

GENERAL_QUESTIONS = [
    "hi",
    "what is gravity?",
    "what is financial success?",
    "explain investing",
    "how can a business improve profitability?",
    "write an email",
]

PERSONAL_QUESTIONS = [
    "will i be successful?",
    "will i be successful moneywise?",
    "will my project work?",
    "will my business succeed?",
    "should i take this opportunity?",
    "how will this situation turn out?",
    "what is blocking me?",
    "what should i be careful about?",
    "why is this happening to me?",
]

ASTROLOGY_QUESTIONS = [
    "what does Saturn mean in my chart?",
    "read my kundli",
    "how is my dasha?",
]

HIDDEN_TOKENS = ("PRIVATE READING CONTEXT", "You are Ask KAVACH", "system_instruction",
                 "groq", "gpt-oss", "gemini", "trace", "reasoning_content", "tarot",
                 "draw_id", "GEMINI_API_KEY", "GROQ_API_KEY", "chain-of-thought")


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
    """Mock providers, the reading engine and the geocoder; record what each saw."""
    seen: dict = {"groq": [], "gemini": [], "geocoder": 0, "readings": []}

    monkeypatch.setattr(archive, "store", FakeStore())
    monkeypatch.setattr("chat.reading.sensitive_response", lambda _q: None)

    def fake_reading(question):
        seen["readings"].append(question)
        return {"draw_id": "d1", "interpretations": [{"reading": "context"}]}

    monkeypatch.setattr("chat.reading.build_reading", fake_reading)
    monkeypatch.setattr("chat.reading.private_context", lambda _r: "PRIVATE READING CONTEXT")

    def fake_groq(_q, _h, private_context=""):
        seen["groq"].append(private_context)
        return {"text": "Groq answer.", "model": groq.MODEL, "preferred": groq.MODEL,
                "provider": "groq", "attempts": [], "fallback": False,
                "reasoning_content": "HIDDEN CHAIN OF THOUGHT"}

    def fake_gemini(_q, _h, private_context=""):
        seen["gemini"].append(private_context)
        return {"text": "Gemini answer.", "model": "gemini-3.5-flash-lite",
                "preferred": "gemini-3.5-flash-lite", "provider": "gemini", "attempts": []}

    monkeypatch.setattr("chat.groq.generate_reply_detailed", fake_groq)
    monkeypatch.setattr("chat.gemini.generate_reply_detailed", fake_gemini)

    import geocoding

    monkeypatch.setattr(geocoding, "_provider_search",
                        lambda _q, _l: seen.__setitem__("geocoder", seen["geocoder"] + 1))
    gemini.reset_health()
    yield seen


@pytest.fixture()
def client():
    return TestClient(main.app)


def ask(client, question, conversation_id="pr"):
    return client.post("/api/ask", json={**ASK, "question": question, "conversation_id": conversation_id})


# --- routing: the three conceptual types ------------------------------------
@pytest.mark.parametrize("question", GENERAL_QUESTIONS)
def test_general_questions_are_not_personal_readings(question):
    assert router.route_message(question, has_active_reading=False) == router.NORMAL_CHAT, question
    assert router.is_personal_uncertainty(question) is False, question


@pytest.mark.parametrize("question", PERSONAL_QUESTIONS)
def test_personal_questions_route_to_a_reading(question):
    assert router.route_message(question, has_active_reading=False) == router.NEW_READING, question


@pytest.mark.parametrize("question", ASTROLOGY_QUESTIONS)
def test_astrology_questions_stay_astrology(question):
    assert router.route_message(question, has_active_reading=False) == router.NEW_READING, question
    assert router.has_astrology_signal(question) is True, question


def test_subject_words_alone_do_not_trigger_a_reading():
    for subject in ("financial success", "investing", "business profitability", "money",
                    "career", "relationships"):
        assert router.route_message(f"what is {subject}?", False) == router.NORMAL_CHAT, subject


@pytest.mark.parametrize("question", [
    "How will my interview go?",
    "Should I be careful about this situation?",
    "How is this relationship situation looking?",
])
def test_product_starter_prompts_are_personal_readings(question):
    """The prompts Ask KAVACH itself suggests must open a reading, not general chat."""
    assert router.route_message(question, has_active_reading=False) == router.NEW_READING, question


# --- the hidden reading is actually invoked ---------------------------------
@pytest.mark.parametrize("question", PERSONAL_QUESTIONS)
def test_personal_questions_invoke_the_hidden_reading(env, client, question):
    body = ask(client, question, conversation_id=f"p-{abs(hash(question))}").json()

    assert body["answered"] is True
    assert env["readings"], "the existing hidden reading must be drawn"
    assert env["groq"], "the primary provider answers from the reading"
    assert "PRIVATE READING CONTEXT" in env["groq"][-1], "the reading must reach the model"


def test_general_questions_never_use_the_reading(env, client):
    for index, question in enumerate(GENERAL_QUESTIONS):
        ask(client, question, conversation_id=f"g-{index}")

    assert env["readings"] == [], "general chat must not draw/interpret a reading"
    assert env["geocoder"] == 0, "ordinary Ask traffic must not geocode"
    assert all(private == "" for private in env["groq"]), "no reading context in general chat"


def test_astrology_questions_keep_the_astrology_context(env, client):
    ask(client, "what does Saturn mean in my chart?", conversation_id="astro")
    assert env["groq"][-1] == "PRIVATE READING CONTEXT"


def test_no_keyword_trigger_for_financial_vocabulary(env, client):
    """The reported bug: a bare financial question must not become a reading."""
    for index, question in enumerate(("what is financial success?", "explain investing",
                                      "how can a business improve profitability?")):
        ask(client, question, conversation_id=f"finance-{index}")

    assert env["readings"] == []
    assert all(private == "" for private in env["groq"])


# --- follow-up context reuse and exit ---------------------------------------
def test_personal_follow_ups_reuse_then_exit_the_reading(env, client):
    ask(client, "Will I be successful financially?", conversation_id="reuse")
    assert len(env["readings"]) == 1
    assert env["groq"][-1] == "PRIVATE READING CONTEXT"

    ask(client, "What's the biggest obstacle?", conversation_id="reuse")
    assert len(env["readings"]) == 1, "a follow-up must reuse the active reading, not redraw"
    assert env["groq"][-1] == "PRIVATE READING CONTEXT"

    ask(client, "And what should I focus on?", conversation_id="reuse")
    assert len(env["readings"]) == 1, "the same reading stays active for relevant follow-ups"
    assert env["groq"][-1] == "PRIVATE READING CONTEXT"

    ask(client, "Explain compound interest.", conversation_id="reuse")
    assert len(env["readings"]) == 1, "an unrelated factual question must not redraw"
    assert env["groq"][-1] == "", "an unrelated question returns to general chat"


def test_new_personal_situation_starts_a_new_reading(env, client):
    ask(client, "Will I be successful financially?", conversation_id="new-topic")
    ask(client, "Will my business succeed?", conversation_id="new-topic")

    assert len(env["readings"]) == 2, "a genuinely new situation draws a new reading"


# --- hidden internals --------------------------------------------------------
def test_reading_internals_and_provider_metadata_stay_hidden(env, client, caplog):
    with caplog.at_level("INFO"):
        response = ask(client, "Will I be successful moneywise?", conversation_id="hidden")

    body_text = response.text
    assert set(json.loads(body_text)) == {"status", "answered", "answer", "conversation_id"}
    for token in HIDDEN_TOKENS:
        assert token not in body_text, token

    log_text = caplog.text
    assert "PRIVATE READING CONTEXT" not in log_text
    assert "HIDDEN CHAIN OF THOUGHT" not in log_text
    assert "GROQ_API_KEY" not in log_text and "GEMINI_API_KEY" not in log_text


def test_provider_architecture_is_unchanged():
    assert groq.MODEL == "openai/gpt-oss-120b", "Groq stays primary"
    assert groq.ENDPOINT == "https://api.groq.com/openai/v1/chat/completions"
    assert gemini.MODEL_PRIORITY[0].startswith("gemini-3.5-flash"), "Gemini stays the fallback"
    source = (REPO / "backend" / "main.py").read_text(encoding="utf-8")
    assert "chat.groq" in source and "chat.gemini" in source
    assert "chat.nvidia" not in source, "NVIDIA must stay out of the active path"
    assert not list((REPO / "backend" / "chat").glob("nvidia.py"))


def test_response_style_instruction_remains_active(env, client):
    assert "Match the length to the question" in SYSTEM_INSTRUCTION
    assert _system_instruction_for("") == SYSTEM_INSTRUCTION
    body = ask(client, "Will I be successful moneywise?", conversation_id="style").json()
    assert body["answer"] == "Groq answer."


# --- frontend rendering safety ----------------------------------------------
def test_frontend_renders_supported_formatting_without_raw_html():
    ask_page = (REPO / "frontend-next" / "app" / "ask" / "page.tsx").read_text(encoding="utf-8")
    renderer = (REPO / "frontend-next" / "components" / "RichAnswer.tsx").read_text(encoding="utf-8")
    formatter = (REPO / "frontend-next" / "lib" / "formatAnswer.ts").read_text(encoding="utf-8")

    assert "dangerouslySetInnerHTML=" not in renderer, "no raw HTML injection path"
    assert "dangerouslySetInnerHTML=" not in formatter
    assert "<RichAnswer text={turn.answer} />" in ask_page, "assistant answers use the safe renderer"
    assert "<strong" in renderer and "<em>" in renderer, "bold and italics are rendered as elements"
    assert "list-disc" in renderer and "list-decimal" in renderer, "bullet and numbered lists"
    assert "\\*\\*" in formatter, "double-asterisk bold is parsed, not shown"
