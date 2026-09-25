"""Router intent for Ask KAVACH: answer by default, filter only when real.

    CASUAL            greetings / thanks / light conversation, follow-ups and
                      ordinary informational questions (the default)
    ASTROLOGY         explicit chart, planet, rashi, nakshatra, dasha, transit...
    PERSONAL_READING  the user's own uncertain situation, decision or life topic
    OUT_OF_SCOPE      only genuinely unrelated requests (coding, writing, maths,
                      science...): refused with a short scope message

A message is never refused merely because it lacks astrology keywords:
conversational fragments fall through to CASUAL and are answered naturally.
"""

from __future__ import annotations

import pytest

from chat.router import (ASTROLOGY, CASUAL, OUT_OF_SCOPE, PERSONAL_READING,
                         READING_FOLLOWUP, SCOPE_MESSAGE, has_astrology_signal,
                         is_out_of_scope, is_personal_topic, is_personal_uncertainty,
                         route_message)

CASUAL_MESSAGES = ["hi", "hello", "hey", "thanks", "okay", "how are you?", "thanks!"]

ASTROLOGY_QUESTIONS = [
    "read my kundli",
    "read my chart",
    "what does Saturn mean in my chart?",
    "how is my dasha?",
    "what does my rashi indicate?",
    "what does the transit of Jupiter mean for me?",
    "tell me about my nakshatra",
    "what is my moon sign?",
    "give me a reading",
    "how is my career period?",
]

PERSONAL_READING_QUESTIONS = [
    "will i be successful?",
    "will i be successful moneywise?",
    "will my business work?",
    "will my relationship work?",
    "should i take this opportunity?",
    "what is blocking my career?",
    "will my project work?",
    "how will this situation turn out?",
    "what should i be careful about?",
    "why is this happening to me?",
    "will i get the result i want?",
    "what should I be cautious about?",
]

OUT_OF_SCOPE_QUESTIONS = [
    "will it rain tomorrow?",
    "will India win the match?",
    "who won the football match?",
]


@pytest.mark.parametrize("question", CASUAL_MESSAGES)
def test_casual_messages(question):
    assert route_message(question, has_active_reading=False) == CASUAL, question


@pytest.mark.parametrize("question", ASTROLOGY_QUESTIONS)
def test_astrology_questions(question):
    assert route_message(question, has_active_reading=False) == ASTROLOGY, question


@pytest.mark.parametrize("question", PERSONAL_READING_QUESTIONS)
def test_personal_reading_questions(question):
    assert route_message(question, has_active_reading=False) == PERSONAL_READING, question


@pytest.mark.parametrize("question", OUT_OF_SCOPE_QUESTIONS)
def test_out_of_scope_questions(question):
    assert route_message(question, has_active_reading=False) == OUT_OF_SCOPE, question


def test_personal_reading_does_not_need_astrology_vocabulary():
    """Core Ask KAVACH questions must never be refused for lacking chart words."""
    for question in ("Will I be successful?", "Will I make good money?",
                     "What is blocking my career?", "Will this relationship work?",
                     "Should I take this opportunity?", "What should I be cautious about?",
                     "How is this situation likely to turn out?"):
        assert has_astrology_signal(question) is False, question
        assert route_message(question, has_active_reading=False) == PERSONAL_READING, question


def test_bare_subject_words_do_not_trigger_a_reading():
    """A general question about money/career is ordinary chat, not a reading."""
    for subject in ("financial success", "investing", "business profitability",
                    "marketing", "the stock market"):
        route = route_message(f"what is {subject}?", False)
        assert route == CASUAL, subject
        assert is_personal_uncertainty(f"what is {subject}?") is False, subject


def test_weather_and_public_forecasts_are_not_readings():
    assert route_message("Will it rain tomorrow?", False) == OUT_OF_SCOPE
    assert route_message("Will India win the match?", False) == OUT_OF_SCOPE
    # The same future tense about the user's own life IS a reading.
    assert route_message("Will my interview go well tomorrow?", False) == PERSONAL_READING


def test_out_of_scope_detector_is_specific():
    """Only live-data requests no assistant can honestly produce are filtered."""
    assert is_out_of_scope("what is the weather tomorrow?") is True
    assert is_out_of_scope("who won the cricket match?") is True
    assert is_out_of_scope("what does Saturn mean in my chart?") is False
    assert is_out_of_scope("will my business work?") is False
    assert is_out_of_scope("what is blocking my career?") is False
    # Everyday assistant work is answered normally, never refused.
    for task in ("write python code", "write an email", "give me a recipe",
                 "solve this equation", "translate this sentence"):
        assert is_out_of_scope(task) is False, task
        assert route_message(task, False) == CASUAL, task


def test_personal_topic_helper_covers_the_users_own_life():
    assert is_personal_topic("what is blocking my career?") is True
    assert is_personal_topic("my relationship") is True
    assert is_personal_topic("what is financial success?") is False


def test_casual_conversation_survives_an_active_reading():
    assert route_message("thanks", has_active_reading=True) == CASUAL
    assert route_message("how are you?", has_active_reading=True) == CASUAL


def test_personal_follow_ups_reuse_the_active_reading():
    assert route_message("Will I be successful financially?", False) == PERSONAL_READING
    for follow_up in ("What's the biggest obstacle?", "And what should I focus on?", "why?"):
        assert route_message(follow_up, True, {}) == READING_FOLLOWUP, follow_up


def test_reading_does_not_lock_the_conversation():
    assert route_message("Will I be successful financially?", False) == PERSONAL_READING
    assert route_message("What's the biggest obstacle?", True, {}) == READING_FOLLOWUP
    # An ordinary informational question leaves the reading entirely: answered
    # as normal conversation, never with a scope message, never a redraw.
    assert route_message("explain compound interest.", True, {}) == CASUAL
    # Everyday tasks are answered as normal conversation even mid-reading.
    assert route_message("what is gravity?", True, {}) == CASUAL
    assert route_message("write an email", True, {}) == CASUAL
    assert route_message("thanks", True, {}) == CASUAL


def test_explicit_astrology_beats_personal_and_out_of_scope():
    assert route_message("will my dasha be good?", False) == ASTROLOGY
    assert route_message("what does Saturn mean in my chart?", False) == ASTROLOGY
    assert route_message("what does my chart say about my career?", False) == ASTROLOGY


def test_astrology_follow_up_uses_the_last_mode():
    """After an astrology answer, a bare follow-up stays astrology."""
    assert route_message("read my kundli", False) == ASTROLOGY
    assert route_message("why?", False, None, last_mode=ASTROLOGY) == ASTROLOGY
    assert route_message("tell me more", False, None, last_mode=ASTROLOGY) == ASTROLOGY
    # ...but a personal question still opens a reading.
    assert route_message("will my business work?", False, None, last_mode=ASTROLOGY) == PERSONAL_READING


def test_scope_message_is_short_and_offers_normal_conversation():
    """The rare refusal invites anything else rather than pushing astrology."""
    assert "KAVACH" in SCOPE_MESSAGE
    assert len(SCOPE_MESSAGE) < 220
    # It invites ordinary conversation instead of narrowing to astrology.
    assert "anything else" in SCOPE_MESSAGE.lower()
    assert "explanations" in SCOPE_MESSAGE.lower()


def test_empty_message_is_casual():
    assert route_message("", False) == CASUAL
    assert route_message("   ", False) == CASUAL


def test_conversational_fragments_are_answered_not_refused():
    """Bare fragments are never invalid just for lacking astrology keywords."""
    for fragment in ("why?", "okay", "yes", "tell me more", "23.11.2009",
                     "I don't understand", "what about career?", "continue"):
        assert route_message(fragment, has_active_reading=False) == CASUAL, fragment
