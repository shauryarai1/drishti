"""Message router for Ask KAVACH.

Three outcomes only:

    NORMAL_CHAT       - ordinary conversation, factual help, general questions.
    NEW_READING       - the user explicitly wants astrology / KAVACH insight.
    READING_FOLLOWUP  - continues the astrology reading already active.

GENERAL CHAT IS THE DEFAULT. Astrology context is attached only when the user
actually asks for astrology - an explicit chart/planet/reading word, or a clear
continuation of the reading already on the table. A merely future-oriented
question such as "will my project work?" is ordinary conversation and is
answered normally, never as a reading.
"""

from __future__ import annotations

NORMAL_CHAT = "NORMAL_CHAT"
NEW_READING = "NEW_READING"
READING_FOLLOWUP = "READING_FOLLOWUP"

# Explicit astrology vocabulary: the only thing that starts an astrology reading.
# Deliberately narrow - situational or future-oriented phrasing is NOT a signal.
ASTROLOGY_SIGNALS = (
    "kundli", "birth chart", "chart", "planet", "planets", "rashi", "nakshatra",
    "dasha", "transit", "astrology", "astrological", "astrologer", "saturn",
    "jupiter", "mars", "rahu", "ketu", "moon sign", "horoscope", "panchang",
    "hora", "navtara", "zodiac", "graha", "lagna", "ascendant", "dosha",
    "my reading", "kavach say", "read my chart", "read my kundli", "give me a reading",
    "career period",
)

# Short continuations that refer to what was just said.
FOLLOW_UP_MARKERS = (
    "why", "are you sure", "sure?", "explain", "what does that mean", "what do you mean",
    "tell me more", "go on", "more detail", "and then", "what if", "but why",
    "what should i do", "what should i change", "so what should i", "so what do i",
    "how so", "really?", "meaning", "then what", "what about that", "what about",
    "will it improve", "will things improve",
)

# Concrete subjects used only to recognise a *change* of subject during a
# follow-up, so short extensions stay on the same reading.
SUBJECT_NOUNS = (
    "exam", "interview", "relationship", "marriage", "partner", "girl", "girlfriend",
    "money", "job", "career", "business", "client", "study", "home", "property", "health",
)

# Standalone general/factual questions always break out of an astrology reading.
STANDALONE_FACTUAL = (
    "what is", "what are", "what's", "explain", "define", "tell me about",
    "how do i", "how can i", "how does", "how do", "who is", "where is", "when is",
    "help me", "give me", "write", "translate", "summarise", "summarize",
)

# Plain acknowledgements are conversation, not reading follow-ups.
CHIT_CHAT = ("hi", "hello", "hey", "thanks", "thank", "thx", "bye", "ok", "okay",
             "cool", "nice", "great", "got", "hmm", "good", "night", "morning")


def has_astrology_signal(message: str) -> bool:
    """True only for an explicit astrology word (never mere future tense)."""
    text = (message or "").lower()
    return any(signal in text for signal in ASTROLOGY_SIGNALS)


def route_message(message: str, has_active_reading: bool,
                  active_reading: dict | None = None) -> str:
    """Return NORMAL_CHAT, NEW_READING or READING_FOLLOWUP."""
    text = (message or "").lower().strip()
    if not text:
        return NORMAL_CHAT

    import re as _re

    tokens = _re.findall(r"[a-z']+", text)
    astrology = has_astrology_signal(text)
    standalone = any(signal in text for signal in STANDALONE_FACTUAL) and len(tokens) > 1
    has_marker = any(marker in text for marker in FOLLOW_UP_MARKERS)
    chit_chat = (not has_marker) and any(token in CHIT_CHAT for token in tokens) and len(tokens) <= 3

    # A. Continue the reading already on the table for short continuations
    #    ("what about Jupiter?"), but never trap a general question in it.
    if has_active_reading and not chit_chat:
        if not any(noun in text for noun in SUBJECT_NOUNS):
            if has_marker or astrology or len(tokens) <= 2:
                if not (standalone and not astrology):
                    return READING_FOLLOWUP

    # B. Explicit astrology question -> attach KAVACH's astrology context.
    if astrology:
        return NEW_READING

    # C. Everything else is ordinary conversation.
    return NORMAL_CHAT
