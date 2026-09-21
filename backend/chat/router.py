"""Message router for Ask KAVACH.

Three outcomes only:

    NORMAL_CHAT       - ordinary conversation or factual/help questions.
    NEW_READING       - the user wants KAVACH's insight into their own situation.
    READING_FOLLOWUP  - continues the reading already active.

NEW_READING is not limited to future-tense questions. A reading is created when
the user asks for personal insight about their own uncertain situation: outlook,
decision, "why is this happening to me", blockage or direction.

Conservative by design: when nothing clearly asks for personal interpretation,
the message is NORMAL_CHAT. Normal conversation never depends on Tarot.
"""

from __future__ import annotations

NORMAL_CHAT = "NORMAL_CHAT"
NEW_READING = "NEW_READING"
READING_FOLLOWUP = "READING_FOLLOWUP"

# Short continuations that refer to what was just said.
FOLLOW_UP_MARKERS = (
    "why", "are you sure", "sure?", "explain", "what does that mean", "what do you mean",
    "tell me more", "go on", "more detail", "and then", "what if", "but why",
    "what should i do", "what should i change", "so what should i", "so what do i",
    "how so", "really?", "meaning", "then what", "will it improve", "will things improve",
)

# Structural forms that ask KAVACH to interpret the user's own situation.
PERSONAL_INTERPRETATION = (
    "why am i", "why are my", "why is my", "why do i", "why does my", "why does this",
    "why is this", "why isn't my", "why isnt my", "why aren't my", "why arent my",
    "why do i keep", "why does this keep", "why is this happening",
    "what is blocking", "what's blocking", "what is stopping", "what's stopping",
    "what is holding me", "what is going wrong", "what's going wrong",
    "what is wrong with my", "what is happening with my", "what's happening with my",
    "what should i focus", "what should i do about", "what can i expect",
    "what does kavach say", "give me a reading",
)

# Wording that asks for an outlook or a situational decision.
READING_SIGNALS = (
    "reading", "kavach say", "predict", "prediction", "horoscope", "forecast",
    "how will", "will i", "will my", "will this", "will it", "will we",
    "will they", "will she", "will he", "will things",
    "should i", "should we", "should my",
    "what does my future", "future of", "outlook", "going to happen",
    "work out", "turn out", "good time to", "right time to",
)

# Concrete subjects used only to recognise a *change* of subject during a
# follow-up, so short extensions stay on the same reading.
SUBJECT_NOUNS = (
    "exam", "interview", "relationship", "marriage", "partner", "girl", "girlfriend",
    "money", "job", "career", "business", "client", "study", "home", "property", "health",
)


# Standalone factual questions must break out of an active reading.
STANDALONE_FACTUAL = (
    "what is", "what are", "what's", "explain", "define", "tell me about",
    "how do i", "how can i", "how does", "who is", "where is", "when is",
)

# Plain acknowledgements are conversation, not reading follow-ups.
CHIT_CHAT = ("hi", "hello", "hey", "thanks", "thank", "thx", "bye", "ok", "okay",
             "cool", "nice", "great", "got", "hmm", "good", "night", "morning")


def route_message(message: str, has_active_reading: bool,
                  active_reading: dict | None = None) -> str:
    """Return NORMAL_CHAT, NEW_READING or READING_FOLLOWUP."""
    text = (message or "").lower().strip()
    if not text:
        return NORMAL_CHAT

    import re as _re

    tokens = _re.findall(r"[a-z']+", text)
    personal = (any(pattern in text for pattern in PERSONAL_INTERPRETATION)
                or ("why" in tokens and len(tokens) > 6))
    standalone_factual = (any(signal in text for signal in STANDALONE_FACTUAL)
                          and not personal and len(tokens) > 2)
    has_marker = any(marker in text for marker in FOLLOW_UP_MARKERS)
    chit_chat = (not has_marker) and any(token in CHIT_CHAT for token in tokens) and len(tokens) <= 3

    # A. continue the reading already on the table (context wins over wording),
    #    unless this is a standalone factual question or plain acknowledgement
    if has_active_reading and not standalone_factual and not chit_chat:
        if not any(noun in text for noun in SUBJECT_NOUNS) and (has_marker or len(tokens) <= 8):
            return READING_FOLLOWUP

    # B. personal interpretation of the user's own situation
    if personal:
        return NEW_READING

    # C. clear outlook or situational decision
    if any(signal in text for signal in READING_SIGNALS):
        return NEW_READING

    # D. everything else is ordinary conversation
    return NORMAL_CHAT
