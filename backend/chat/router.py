"""Message router for Ask KAVACH.

Ask KAVACH behaves like a capable conversational assistant: ANSWER BY DEFAULT,
filter only when there is a real reason to filter. The router decides which
internal capability/context is needed - it never replaces a valid answer with
a scope message just because classification confidence is low. Modes:

    CASUAL           normal conversation: greetings, follow-ups, short
                     fragments and ordinary informational questions, answered
                     naturally by the assistant with the recent conversation.
    ASTROLOGY        explicit astrology / Kundli vocabulary. It keeps the topic
                      in conversational chat; dedicated personal calculations
                      are recommended through controlled KAVACH tool actions.
    PERSONAL_READING the user's OWN uncertain situation, future or decision
                     (the hidden KAVACH/Tarot reading), plus the user's own
                     life topics (career, money, relationships, studies...).
    OUT_OF_SCOPE     only genuinely unrelated requests (coding, writing, maths,
                     science, sport, weather...). Answered with a short KAVACH
                     scope message, never substantively.

    READING_FOLLOWUP continues the reading already active.

The distinction that matters most: a personal question does NOT need astrology
vocabulary ("will I be successful?", "what is blocking my career?"), while a
general-knowledge question about the same subject ("what is financial
success?") is ordinary conversation rather than a reading. Conversational
fragments ("why?", "okay", "yes", a bare date, "tell me more") are never
inherently invalid: they fall through to CASUAL and are resolved by the
assistant using the recent conversation.
"""

from __future__ import annotations

CASUAL = "CASUAL"
ASTROLOGY = "ASTROLOGY"
PERSONAL_READING = "PERSONAL_READING"
READING_FOLLOWUP = "READING_FOLLOWUP"
OUT_OF_SCOPE = "OUT_OF_SCOPE"

# Rare: live data nobody can honestly produce from here. Everything else,
# including everyday questions and tasks, is answered normally.
SCOPE_MESSAGE = (
    "I can't pull live real-world data like that here, but ask me anything else "
    "- explanations, writing, ideas, everyday questions, or your KAVACH Kundli."
)

# Explicit astrology vocabulary: the only thing that selects the astrology path.
ASTROLOGY_SIGNALS = (
    "kundli", "birth chart", "chart", "planet", "planets", "rashi", "nakshatra",
    "dasha", "transit", "astrology", "astrological", "astrologer", "saturn",
    "jupiter", "mars", "rahu", "ketu", "moon sign", "horoscope", "panchang",
    "hora", "navtara", "zodiac", "graha", "lagna", "ascendant", "dosha",
    "my reading", "kavach say", "read my chart", "read my kundli", "give me a reading",
    "career period",
)

# First-person predictive / decision wording: the user asking about their own
# uncertain situation.
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

# Markers that are already about the user's own future even without a pronoun.
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

# The user's own life topics: explicitly in scope for Ask KAVACH even without
# predictive wording, because they are about the person's own path.
PERSONAL_TOPIC_MARKERS = (
    "my career", "my job", "my work", "my money", "my finances", "my business",
    "my relationship", "my marriage", "my partner", "my studies", "my education",
    "my future", "my life", "my situation", "my decision", "my project",
    "my exam", "my interview", "my health", "my family", "my child", "my path",
    "my growth", "about me", "for me", "guide me", "help me decide",
    "i feel stuck", "i'm stuck", "im stuck", "i feel lost", "i am confused",
    "i'm confused", "im confused", "what do you think about me",
    "i'm sad", "i am sad", "i feel sad", "i'm worried", "i am worried",
    "i'm anxious", "i am anxious", "i'm stressed", "i am stressed",
    "i feel low", "i'm unhappy", "i am unhappy", "i'm scared", "i am scared",
    "i'm afraid", "i am afraid",
    # Personal-situation phrasing: clearly about the user's own life.
    "isn't growing", "is not growing", "not growing", "isn't improving",
    "is not improving", "not improving", "haven't heard back", "hasn't heard back",
    "not heard back", "no response from", "difficult at work", "hard at work",
    "struggling at work", "trouble at work", "not working out", "going wrong",
    "keeps failing", "keep failing", "things have been difficult", "things are difficult",
    "things have been hard", "things are hard", "i'm losing", "i am losing",
)

# Life-domain nouns: with a first-person pronoun these mark the user's own life
# (in scope), while a general question about the same subject stays out of scope.
PERSONAL_DOMAIN_NOUNS = (
    "business", "career", "job", "work", "money", "finances", "finance", "marks",
    "grades", "studies", "study", "exam", "exams", "clients", "customers",
    "relationship", "marriage", "partner", "health", "family", "interview",
    "project", "promotion", "salary", "income", "savings", "investment",
    "investments", "debt", "loan", "startup", "venture", "degree", "college",
    "visa", "contract", "deal", "offer", "opportunity",
)

# Only requests no assistant should entertain for this product: live
# real-world data nobody can honestly produce here, and sports results.
# Everyday assistant work - explaining, writing, translating, reasoning,
# maths, homework help - is NOT out of scope: Ask KAVACH answers it normally.
OUT_OF_SCOPE_SIGNALS = (
    "weather", "forecast", "rain tomorrow", "temperature tomorrow", "humidity",
    "who won", "win the match", "match score", "football match", "cricket match",
    "tournament", "stock price", "bitcoin price",
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

# Standalone general/factual questions break out of an active reading.
STANDALONE_FACTUAL = (
    "what is", "what are", "what's", "explain", "define", "tell me about",
    "how do i", "how can i", "how does", "how do", "who is", "where is", "when is",
    "help me", "give me", "write", "translate", "summarise", "summarize",
)

# Plain acknowledgements and greetings are conversation, not reading follow-ups.
CHIT_CHAT = ("hi", "hello", "hey", "thanks", "thank", "thx", "bye", "ok", "okay",
             "cool", "nice", "great", "got", "hmm", "good", "night", "morning")
GREETINGS = ("how are you", "how's it going", "how are things", "what's up", "whats up")


def _tokens(text: str) -> list:
    import re as _re

    return _re.findall(r"[a-z']+", text)


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
    return any(token in PERSONAL_PRONOUNS for token in _tokens(text))


def is_personal_topic(message: str) -> bool:
    """True for the user's own life topics (career, money, relationships...)."""
    text = (message or "").lower()
    if any(marker in text for marker in PERSONAL_TOPIC_MARKERS):
        return True
    tokens = _tokens(text)
    if not any(token in PERSONAL_PRONOUNS for token in tokens):
        return False
    return any(token in PERSONAL_DOMAIN_NOUNS for token in tokens)


def is_out_of_scope(message: str) -> bool:
    """True for unrelated knowledge, coding, writing, maths, science, sport."""
    text = (message or "").lower()
    return any(signal in text for signal in OUT_OF_SCOPE_SIGNALS)


def route_message(message: str, has_active_reading: bool = False,
                  active_reading: dict | None = None,
                  last_mode: str | None = None) -> str:
    """Return CASUAL, ASTROLOGY, PERSONAL_READING, READING_FOLLOWUP or OUT_OF_SCOPE."""
    text = (message or "").lower().strip()
    if not text:
        return CASUAL

    tokens = _tokens(text)
    astrology = has_astrology_signal(text)
    personal = is_personal_uncertainty(text) or is_personal_topic(text)
    out_of_scope = is_out_of_scope(text)
    standalone = any(signal in text for signal in STANDALONE_FACTUAL) and len(tokens) > 1
    has_marker = any(marker in text for marker in FOLLOW_UP_MARKERS)
    strong_marker = any(marker in text for marker in STRONG_FOLLOW_UP_MARKERS)
    chit_chat = ((not has_marker)
                 and (any(token in CHIT_CHAT for token in tokens) and len(tokens) <= 3
                      or any(greeting in text for greeting in GREETINGS)))

    # 1. Lightweight conversation.
    if chit_chat:
        return CASUAL

    # 2. Explicit astrology always wins: it selects the chart context.
    if astrology:
        return ASTROLOGY

    # 3. Genuinely unrelated requests are refused before anything else.
    #    Only the explicit unrelated-domain signals qualify - a message that
    #    merely lacks astrology keywords is NOT out of scope.
    if out_of_scope:
        return OUT_OF_SCOPE

    # 4. Continue an astrology conversation on short continuations, but a
    #    personal question still opens its own reading.
    if (last_mode == ASTROLOGY and not personal
            and (has_marker or len(tokens) <= 8) and not standalone):
        return ASTROLOGY

    # 5. Continue the reading already on the table for short continuations
    #    ("What's the biggest obstacle?"), but never trap a general question.
    if has_active_reading:
        if not any(noun in text for noun in SUBJECT_NOUNS):
            breaks_out = standalone and not strong_marker
            if (has_marker or personal or len(tokens) <= 8) and not breaks_out:
                return READING_FOLLOWUP

    # 6. The user's own uncertainty, decision or life topic -> hidden reading.
    if personal:
        return PERSONAL_READING

    # 7. Answer by default: ordinary questions, follow-ups, corrections and
    #    bare fragments are normal conversation. The assistant resolves them
    #    with the recent conversation instead of a scope message.
    return CASUAL
