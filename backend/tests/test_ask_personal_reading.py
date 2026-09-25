"""Ask KAVACH: personal uncertainty/questions use the hidden KAVACH reading.

Requirement: personal predictive/decision questions ("will i be successful
moneywise?") must answer FROM the existing hidden Tarot reading, while general
knowledge questions stay ordinary chat and explicit astrology questions keep the
astrology context. Providers are mocked - zero live quota.
"""

from __future__ import annotations

import json
import pathlib
import shutil
import subprocess

import pytest
from fastapi.testclient import TestClient

import archive
import chat.gemini as gemini
import chat.groq as groq
import chat.natal as natal
import chat.router as router
import main
from chat.gemini import SYSTEM_INSTRUCTION, _system_instruction_for

REPO = pathlib.Path(__file__).resolve().parents[2]
ASK = {"timestamp": "2026-09-22T11:45:00+05:30", "latitude": 28.6139, "longitude": 77.209,
       "timezone": "Asia/Kolkata"}

# Complete birth details: chart questions are grounded in a calculated chart.
BIRTH = {"date": "1990-05-14", "time": "07:45", "place": "New Delhi, India",
         "latitude": 28.6139, "longitude": 77.209, "timezone": "Asia/Kolkata"}


def seed_chart(conversation_id):
    natal.seed(conversation_id, BIRTH)


CASUAL_QUESTIONS = ["hi", "hello", "thanks"]

# Genuinely unrelated requests: still refused with the short scope message,
# with no provider call and no reading.
OUT_OF_SCOPE_QUESTIONS = [
    "what is gravity?",
    "write an email",
    "write a Python script",
    "solve this equation",
    "will it rain tomorrow?",
]

# Ordinary informational questions: answered naturally as conversation - never
# refused for lacking astrology keywords, never turned into a reading.
GENERAL_QUESTIONS = [
    "what is financial success?",
    "explain investing",
    "how can a business improve profitability?",
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
    seen: dict = {"groq": [], "gemini": [], "geocoder": 0, "readings": [], "astrology": []}

    monkeypatch.setattr(archive, "store", FakeStore())
    monkeypatch.setattr("chat.reading.sensitive_response", lambda _q: None)

    def fake_reading(question):
        seen["readings"].append(question)
        return {"draw_id": "d1", "interpretations": [{"reading": "context"}]}

    monkeypatch.setattr("chat.reading.build_reading", fake_reading)
    monkeypatch.setattr("chat.reading.private_context", lambda _r: "PRIVATE READING CONTEXT")

    def fake_groq(_q, _h, private_context="", astrology_context=""):
        seen["groq"].append(private_context)
        seen["astrology"].append(astrology_context)
        return {"text": "Groq answer.", "model": groq.MODEL, "preferred": groq.MODEL,
                "provider": "groq", "attempts": [], "fallback": False,
                "reasoning_content": "HIDDEN CHAIN OF THOUGHT"}

    def fake_gemini(_q, _h, private_context="", astrology_context=""):
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
@pytest.mark.parametrize("question", CASUAL_QUESTIONS)
def test_casual_messages_are_not_readings(question):
    assert router.route_message(question, has_active_reading=False) == router.CASUAL, question


@pytest.mark.parametrize("question", OUT_OF_SCOPE_QUESTIONS)
def test_out_of_scope_questions_are_refused_not_readings(question):
    assert router.route_message(question, has_active_reading=False) == router.OUT_OF_SCOPE, question


@pytest.mark.parametrize("question", GENERAL_QUESTIONS)
def test_general_questions_are_answered_not_refused(question):
    """Answer by default: no astrology keyword required, never a scope message."""
    assert router.route_message(question, has_active_reading=False) == router.CASUAL, question


@pytest.mark.parametrize("question", PERSONAL_QUESTIONS)
def test_personal_questions_route_to_a_reading(question):
    assert router.route_message(question, has_active_reading=False) == router.PERSONAL_READING, question


@pytest.mark.parametrize("question", ASTROLOGY_QUESTIONS)
def test_astrology_questions_stay_astrology(question):
    assert router.route_message(question, has_active_reading=False) == router.ASTROLOGY, question
    assert router.has_astrology_signal(question) is True, question


def test_subject_words_alone_do_not_trigger_a_reading():
    """A general question about a life subject is conversation, not a reading."""
    for subject in ("financial success", "investing", "business profitability", "money",
                    "career", "relationships"):
        assert router.route_message(f"what is {subject}?", False) == router.CASUAL, subject


@pytest.mark.parametrize("question", [
    "How will my interview go?",
    "Should I be careful about this situation?",
    "How is this relationship situation looking?",
])
def test_product_starter_prompts_are_personal_readings(question):
    """The prompts Ask KAVACH itself suggests must open a reading."""
    assert router.route_message(question, has_active_reading=False) == router.PERSONAL_READING, question


# --- the hidden reading is actually invoked ---------------------------------
@pytest.mark.parametrize("question", PERSONAL_QUESTIONS)
def test_personal_questions_invoke_the_hidden_reading(env, client, question):
    body = ask(client, question, conversation_id=f"p-{abs(hash(question))}").json()

    assert body["answered"] is True
    assert env["readings"], "the existing hidden reading must be drawn"
    assert env["groq"], "the primary provider answers from the reading"
    assert "PRIVATE READING CONTEXT" in env["groq"][-1], "the reading must reach the model"


def test_out_of_scope_questions_never_reach_a_provider(env, client):
    for index, question in enumerate(OUT_OF_SCOPE_QUESTIONS):
        body = ask(client, question, conversation_id=f"oos-{index}").json()
        assert body["answered"] is True, question
        assert body["answer"] == router.SCOPE_MESSAGE, question

    assert env["readings"] == [], "an unrelated request must not draw a reading"
    assert env["groq"] == [], "an unrelated request must not be sent to the model"
    assert env["geocoder"] == 0, "ordinary Ask traffic must not geocode"


def test_general_questions_are_answered_without_reading_or_scope(env, client):
    for index, question in enumerate(GENERAL_QUESTIONS):
        body = ask(client, question, conversation_id=f"gen-{index}").json()
        assert body["answered"] is True, question
        assert body["answer"] != router.SCOPE_MESSAGE, question
        assert body["answer"] == "Groq answer.", question

    assert env["readings"] == [], "a general question must not draw a reading"
    assert all(private == "" for private in env["groq"]), "no reading context"
    assert all(astrology == "" for astrology in env["astrology"]), "no chart context"
    assert env["geocoder"] == 0, "ordinary Ask traffic must not geocode"


def test_astrology_questions_keep_the_astrology_context(env, client):
    seed_chart("astro")
    ask(client, "what does Saturn mean in my chart?", conversation_id="astro")
    assert env["groq"] == [""], "astrology must NOT carry the private Tarot reading"
    assert env["readings"] == [], "astrology must not draw a Tarot reading"
    assert env["astrology"], "astrology answers carry the chart context"
    assert "CHART CONTEXT" in env["astrology"][-1]


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

    before_readings = len(env["readings"])
    body = ask(client, "Explain compound interest.", conversation_id="reuse").json()
    assert body["answer"] == "Groq answer.", "an ordinary question is answered, not refused"
    assert len(env["readings"]) == before_readings, "an unrelated question must not redraw"
    assert env["groq"][-1] == "", "the active reading must not leak into a general answer"


def test_personal_reading_never_leaks_into_an_astrology_question(env, client):
    """BUG 1: the active Tarot reading must not be supplied for a chart question."""
    seed_chart("isolation")
    ask(client, "will i be successful in life?", conversation_id="isolation")
    assert len(env["readings"]) == 1
    assert env["groq"][-1] == "PRIVATE READING CONTEXT"

    body = ask(client, "what does the saturn in my chart mean?", conversation_id="isolation").json()

    assert body["answered"] is True
    assert len(env["readings"]) == 1, "an astrology question must not redraw the reading"
    assert env["groq"][-1] == "", "the Tarot private context must NOT reach the chart answer"
    assert env["astrology"][-1], "the chart context must be supplied instead"
    assert "CHART CONTEXT" in env["astrology"][-1]


def test_personal_reading_to_astrology_to_new_reading(env, client):
    """astrology -> personal reading -> astrology keeps each context separate."""
    seed_chart("switch-2")
    ask(client, "read my kundli", conversation_id="switch-2")
    assert env["astrology"][-1], "astrology context supplied"
    assert env["groq"][-1] == ""

    ask(client, "will my new project work?", conversation_id="switch-2")
    assert len(env["readings"]) == 1, "a personal question opens a reading"
    assert env["groq"][-1] == "PRIVATE READING CONTEXT"
    assert env["astrology"][-1] == "", "no chart context on a personal reading"

    ask(client, "how is my dasha?", conversation_id="switch-2")
    assert env["groq"][-1] == "", "astrology again carries no Tarot evidence"
    assert "CHART CONTEXT" in env["astrology"][-1]


def test_personal_reading_to_general_carries_no_hidden_context(env, client):
    ask(client, "will my project work?", conversation_id="to-general")
    assert env["groq"][-1] == "PRIVATE READING CONTEXT"

    body = ask(client, "explain gravity", conversation_id="to-general").json()
    assert body["answer"] == router.SCOPE_MESSAGE
    assert env["groq"][-1] == "PRIVATE READING CONTEXT", "no provider call was made"
    assert env["astrology"][-1] == "", "no chart context either"


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
    assert "<pre" in renderer and "whitespace-pre" in renderer, "fenced code preserves layout"
    assert "type: 'code'" in formatter, "fenced code is a distinct block"
    assert "\\*\\*" in formatter, "double-asterisk bold is parsed, not shown"
    assert "parseSpans" in formatter and "FENCE" in formatter


def test_format_answer_tokenizes_code_before_emphasis(tmp_path):
    """Run the real formatter: fenced code must survive intact and never leak."""
    node = shutil.which("node")
    if not node:
        pytest.skip("node is not available")

    module = (REPO / "frontend-next" / "lib" / "formatAnswer.ts").as_uri()
    script = tmp_path / "check_format.mjs"
    script.write_text(
        'import { formatAnswer } from "MODULE";\n'
        'const blocks = formatAnswer("Intro\\n\\n```python\\nmenu = {}\\n'
        'if __name__ == \\"__main__\\":\\n    get_choice()\\n```\\n\\nDone");\n'
        'const code = blocks.find((b) => b.type === "code");\n'
        'if (!code) throw new Error("code block not parsed");\n'
        'if (code.language !== "python") throw new Error("language lost");\n'
        'if (!code.code.includes("__name__")) throw new Error("identifier corrupted: " + code.code);\n'
        'if (!code.code.includes("    get_choice()")) throw new Error("indentation lost: " + JSON.stringify(code.code));\n'
        'if (JSON.stringify(blocks).includes("```")) throw new Error("fence leaked to the user");\n'
        'const spans = JSON.stringify(formatAnswer("**Bold** and __name__"));\n'
        'if (!spans.includes(\'"bold":true\')) throw new Error("bold not parsed");\n'
        'if (!spans.includes("__name__")) throw new Error("underscore identifier corrupted");\n'
        'if (JSON.stringify(formatAnswer("<script>alert(1)</script>")).indexOf("<script>") < 0) '
        'throw new Error("html must stay literal text");\n'
        'console.log("FORMATTER_OK");\n'.replace("MODULE", module),
        encoding="utf-8",
    )
    result = subprocess.run([node, str(script)], capture_output=True, text=True, timeout=90)
    assert result.returncode == 0, result.stderr
    assert "FORMATTER_OK" in result.stdout
