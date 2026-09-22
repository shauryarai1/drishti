"""Router intent: three conceptual question types.

    general knowledge  -> NORMAL_CHAT
    personal uncertainty / decision -> NEW_READING (the hidden KAVACH reading)
    explicit astrology -> NEW_READING (KAVACH astrology context)

The signal for a personal reading is first-person predictive or decision
wording, never a bare subject word such as "money", "career" or "business".
"""

from __future__ import annotations

import pytest

from chat.router import (NEW_READING, NORMAL_CHAT, READING_FOLLOWUP,
                         has_astrology_signal, is_personal_uncertainty, route_message)

GENERAL_QUESTIONS = [
    "hi",
    "hello",
    "how are you?",
    "what is gravity?",
    "explain photosynthesis",
    "explain Newton's second law",
    "write an email to my teacher",
    "help me write an email",
    "give me study tips",
    "what does this word mean?",
    "what is financial success?",
    "explain investing",
    "how can a business improve profitability?",
    "how do I make pasta?",
    "thanks!",
]

PERSONAL_READING_QUESTIONS = [
    "will i be successful?",
    "will i be successful moneywise?",
    "will my project work?",
    "will my business succeed?",
    "should i take this opportunity?",
    "how will this situation turn out?",
    "what is blocking me?",
    "what should i be careful about?",
    "will i get the result i want?",
    "why is this happening to me?",
    "what is likely to happen with this situation?",
    "should i take the job?",
    "how will the meeting go?",
]

ASTROLOGY_QUESTIONS = [
    "read my kundli",
    "read my chart",
    "what does Saturn mean in my chart?",
    "how is my week astrologically?",
    "what should I be cautious about according to my chart?",
    "what does my Kundli indicate about this?",
    "what does the transit of Jupiter mean for me?",
    "tell me about my nakshatra",
    "which dasha am I running?",
    "what is my moon sign?",
    "give me a reading",
    "how is my career period?",
]


@pytest.mark.parametrize("question", GENERAL_QUESTIONS)
def test_general_questions_stay_general(question):
    assert route_message(question, has_active_reading=False) == NORMAL_CHAT, question


@pytest.mark.parametrize("question", PERSONAL_READING_QUESTIONS)
def test_personal_uncertainty_questions_create_a_reading(question):
    assert route_message(question, has_active_reading=False) == NEW_READING, question


@pytest.mark.parametrize("question", ASTROLOGY_QUESTIONS)
def test_astrology_questions_create_a_reading(question):
    assert route_message(question, has_active_reading=False) == NEW_READING, question


@pytest.mark.parametrize("word", ["money", "career", "success", "business", "relationship"])
def test_bare_subject_words_never_trigger_a_reading(word):
    """The reported over-correction: subject words alone are not personal intent."""
    assert route_message(f"what is {word}?", False) == NORMAL_CHAT
    assert route_message(f"tell me about {word} planning", False) == NORMAL_CHAT
    assert is_personal_uncertainty(f"explain {word}") is False


def test_personal_signal_needs_first_person_intent():
    assert is_personal_uncertainty("will i be successful moneywise?") is True
    assert is_personal_uncertainty("should i take this opportunity?") is True
    assert is_personal_uncertainty("how will this situation turn out?") is True
    # General questions, even with the same subject matter, stay general.
    assert is_personal_uncertainty("what is financial success?") is False
    assert is_personal_uncertainty("how can a business improve profitability?") is False
    assert is_personal_uncertainty("explain investing") is False


def test_general_questions_are_not_trapped_by_an_active_reading():
    """A reading on the table must never force ordinary questions into astrology."""
    for question in ("what is gravity?", "explain photosynthesis", "write an email to my teacher",
                     "give me study tips", "help me write an email", "how do I bake bread?"):
        assert route_message(question, has_active_reading=True, active_reading={}) == NORMAL_CHAT, question


def test_astrology_follow_up_reuses_the_active_reading():
    for question in ("what about Jupiter?", "why?", "tell me more", "and Saturn?"):
        assert route_message(question, has_active_reading=True,
                             active_reading={}) == READING_FOLLOWUP, question


def test_conversation_is_not_locked_into_astrology():
    """astrology -> astrology follow-up -> unrelated general question."""
    assert route_message("read my kundli", False) == NEW_READING
    assert route_message("what about Jupiter?", True, {}) == READING_FOLLOWUP
    assert route_message("thanks. Now explain gravity.", True, {}) == NORMAL_CHAT
    assert route_message("what is photosynthesis?", True, {}) == NORMAL_CHAT


def test_astrology_signal_helper_is_narrow():
    assert has_astrology_signal("read my kundli") is True
    assert has_astrology_signal("what does Saturn mean in my chart?") is True
    # Situational/future wording is NOT an astrology signal - it is personal.
    assert has_astrology_signal("will my project work?") is False
    assert has_astrology_signal("should I take the job?") is False
    assert has_astrology_signal("how are you?") is False


def test_personal_follow_up_reuses_the_active_reading():
    """A personal reading keeps its short follow-ups (requirement: context reuse)."""
    assert route_message("Will I be successful financially?", False) == NEW_READING
    for follow_up in ("What's the biggest obstacle?", "And what should I focus on?"):
        assert route_message(follow_up, True, {}) == READING_FOLLOWUP, follow_up


def test_personal_reading_does_not_lock_the_conversation():
    """reading -> relevant follow-up -> unrelated factual question -> general chat."""
    assert route_message("Will I be successful financially?", False) == NEW_READING
    assert route_message("What's the biggest obstacle?", True, {}) == READING_FOLLOWUP
    assert route_message("And what should I focus on?", True, {}) == READING_FOLLOWUP
    assert route_message("Explain compound interest.", True, {}) == NORMAL_CHAT
    assert route_message("How do I make pasta?", True, {}) == NORMAL_CHAT
    assert route_message("thanks", True, {}) == NORMAL_CHAT


def test_astrology_is_checked_before_personal():
    """An explicit astrology question keeps astrology context, not a fresh speculation."""
    assert route_message("will my dasha be good?", False) == NEW_READING
    assert route_message("what does Saturn mean in my chart?", False) == NEW_READING


def test_empty_message_is_general_chat():
    assert route_message("", False) == NORMAL_CHAT
    assert route_message("   ", False) == NORMAL_CHAT
