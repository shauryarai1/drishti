"""Message router for Ask KAVACH.

Three outcomes only:

    NORMAL_CHAT       - general knowledge, help, small talk.
    NEW_READING       - KAVACH's hidden reading for the user's OWN uncertain
                        situation, future or decision (this is what most people
                        mean by "personal prediction").
    READING_FOLLOWUP  - continues the reading already active.

Three conceptual question types:

    A. General knowledge / assistance  -> NORMAL_CHAT, never a reading.
    B. Personal uncertainty / decision -> NEW_READING (hidden Tarot reading).
    C. Explicit astrology / chart      -> NEW_READING (KAVACH astrology context).

The signal for a personal reading is FIRST-PERSON predictive or decision
wording ("will I", "should I", "how will this turn out", "what is blocking me"),
never a bare subject word. "What is financial success?" or "explain investing"
stay general; "will I be successful moneywise?" is a personal reading.
"""

from __future__ import annotations

NORMAL_CHAT = "NORMAL_CHAT"
NEW_READING = "NEW_READING"
READING_FOLLOWUP = "READING_FOLLOWUP"

# Explicit astrology vocabulary: the only thing that selects the astrology/chart
# context. Deliberately narrow - situational or future-oriented phrasing is not.
ASTROLOGY_SIGNALS = (
    "kundli", "birth chart", "chart", "planet", "planets", "rashi", "nakshatra",
    "dasha", "transit", "astrology", "astrological", "astrologer", "saturn",
    "jupiter", "mars", "rahu", "ketu", "moon sign", "horoscope", "panchang",
    "hora", "navtara", "zodiac", "graha", "lagna", "ascendant", "dosha",
    "my reading", "kavach say", "read my chart", "read my kundli", "give me a reading",
    "career period",
)

# First-person predictive / decision wording: the user asking KAVACH about their
# own uncertain situation. Paired with a first-person pronoun so that subject
# words alone ("money", "success", "business") never trigger a reading.
PREDICTIVE_MARKERS = (
    "will i", "will my", "will we", "will our", "will this", "will it", "will they",
    "will things", "will there be",
    "should i", "should we", "should my", "shall i",
    "how will", "when will", "how long will", "how soon",
    "going to happen", "going to work", "gonna happen", "am i going to",
    "turn out", "work out", "play out",
    "what should i", "what should we", "what do i do", "what can i expect",
    "what is blocking", "what's blocking", "blocking me",
    "what should i be careful", "be careful about", "watch out for",
    "why is this happening", "what is likely to happen", "what's likely to happen",
    "is my", "are my", "does my", "do my", "do i have what it takes",
    "what does the future hold", "what is my future", "future of my",
    "how is my", "how is this", "how is it looking", "how does this look",
)

PERSONAL_PRONOUNS = ("i", "i'm", "im", "my", "me", "myself", "we", "our", "ours", "us")

# Markers that are already about the user's own future even without a pronoun
# ("how will this situation turn out?"). Everything else needs a first-person
# pronoun, so bare subject words never trigger a reading.
SELF_IMPLYING_MARKERS = (
    "how will", "when will", "how long will", "how soon",
    "will this", "will it", "will they", "will things", "will there be",
    "turn out", "work out", "play out", "going to happen", "going to work",
    "gonna happen", "am i going to",
    "what is blocking", "what's blocking", "blocking me",
    "why is this happening", "what is likely to happen", "what's likely to happen",
    "what does the future hold", "what is my future", "future of my",
    "how is my", "how is this", "how is it looking", "how does this look",
)

# Short continuations that refer to what was just said.
FOLLOW_UP_MARKERS = (
    "why", "are you sure", "sure?", "explain", "what does that mean", "what do you mean",
    "tell me more", "go on", "more detail", "and then", "what if", "but why",
    "what should i do", "what should i change", "so what should i", "so what do i",
    "how so", "really?", "meaning", "then what", "what about that", "what about",
    "will it improve", "will things improve", "biggest obstacle", "obstacle",
    "what should i focus", "what to focus", "anything else", "and what",
)

# Follow-up markers that clearly refer back to what was just said. These beat a
# standalone factual signal ("what's the biggest obstacle?"), unlike words such
# as "explain" which can also introduce a brand-new general question.
STRONG_FOLLOW_UP_MARKERS = (
    "biggest obstacle", "obstacle", "what should i focus", "what to focus",
    "anything else", "are you sure", "what does that mean", "what do you mean",
    "tell me more", "so what should i", "so what do i", "will it improve",
    "will things improve", "what about that", "what if i", "how so",
)

# Concrete subjects used only to recognise a *change* of subject during a
# follow-up, so a genuinely new situation starts a new reading.
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

# Plain acknowledgements and greetings are conversation, not reading follow-ups.
CHIT_CHAT = ("hi", "hello", "hey", "thanks", "thank", "thx", "bye", "ok", "okay",
             "cool", "nice", "great", "got", "hmm", "good", "night", "morning")
GREETINGS = ("how are you", "how's it going", "how are things", "what's up", "whats up")


def has_astrology_signal(message: str) -> bool:
    """True only for an explicit astrology word (never mere future tense)."""
    text = (message or "").lower()
    return any(signal in text for signal in ASTROLOGY_SIGNALS)


def is_personal_uncertainty(message: str) -> bool:
    """True when the user asks about their OWN uncertain situation or decision."""
    text = (message or "").lower()
    marker = next((m for m in PREDICTIVE_MARKERS if m in text), None)
    if marker is None:
        return False
    if any(m in text for m in SELF_IMPLYING_MARKERS):
        return True
    import re as _re

    tokens = _re.findall(r"[a-z']+", text)
    return any(token in PERSONAL_PRONOUNS for token in tokens)


def route_message(message: str, has_active_reading: bool,
                  active_reading: dict | None = None) -> str:
    """Return NORMAL_CHAT, NEW_READING or READING_FOLLOWUP."""
    text = (message or "").lower().strip()
    if not text:
        return NORMAL_CHAT

    import re as _re

    tokens = _re.findall(r"[a-z']+", text)
    astrology = has_astrology_signal(text)
    personal = is_personal_uncertainty(text)
    standalone = any(signal in text for signal in STANDALONE_FACTUAL) and len(tokens) > 1
    has_marker = any(marker in text for marker in FOLLOW_UP_MARKERS)
    strong_marker = any(marker in text for marker in STRONG_FOLLOW_UP_MARKERS)
    chit_chat = ((not has_marker) and (any(token in CHIT_CHAT for token in tokens) and len(tokens) <= 3
                                      or any(greeting in text for greeting in GREETINGS)))

    # A. Continue the reading already on the table for short continuations
    #    ("What's the biggest obstacle?"), but never trap a general question:
    #    a standalone factual question breaks out unless it explicitly refers
    #    back to the reading ("what should I focus on?").
    if has_active_reading and not chit_chat:
        if not any(noun in text for noun in SUBJECT_NOUNS):
            breaks_out = standalone and not strong_marker
            if (has_marker or astrology or personal or len(tokens) <= 8) and not breaks_out:
                return READING_FOLLOWUP

    # B. Explicit astrology question -> KAVACH astrology/chart context.
    if astrology:
        return NEW_READING

    # C. Personal uncertainty / decision -> the hidden KAVACH reading.
    if personal:
        return NEW_READING

    # D. Everything else is ordinary conversation.
    return NORMAL_CHAT
