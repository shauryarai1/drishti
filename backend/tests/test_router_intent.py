"""Router intent: general conversation by default, astrology only when asked.

This replaces the earlier intent suite, which treated situational/future
questions ("will my project work?") as reading requests. That behaviour was the
reported bug: ordinary questions were forced into an astrology reading.
"""

from __future__ import annotations

import pytest

from chat.router import NEW_READING, NORMAL_CHAT, READING_FOLLOWUP, has_astrology_signal, route_message

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
    "will my project work?",
    "will I be successful?",
    "should I take the job?",
    "how will the meeting go?",
    "thanks!",
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


@pytest.mark.parametrize("question", ASTROLOGY_QUESTIONS)
def test_astrology_questions_create_a_reading(question):
    assert route_message(question, has_active_reading=False) == NEW_READING, question


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
    # Future tense alone is NOT an astrology signal (the reported bug).
    assert has_astrology_signal("will my project work?") is False
    assert has_astrology_signal("should I take the job?") is False
    assert has_astrology_signal("how are you?") is False


def test_empty_message_is_general_chat():
    assert route_message("", False) == NORMAL_CHAT
    assert route_message("   ", False) == NORMAL_CHAT
