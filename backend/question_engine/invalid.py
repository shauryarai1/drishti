"""Message validity: greeting, nonsense, or a real question.

Nonsense ("sa", "ads", "sda", "asdads", "....") never triggers a reading, and
never becomes a follow-up merely because conversation history exists.
"""

from __future__ import annotations

import re
from typing import List

from .topics import TOPICS

GREETINGS = {
    "hi", "hey", "hello", "namaste", "namaskar", "yo", "good morning",
    "good afternoon", "good evening", "thanks", "thank you", "thankyou", "ok", "okay",
}

GREETING_MESSAGE = (
    "Hello, I am KAVACH. Ask me about work, home, relationships, money, a decision "
    "you are facing, or how the coming period looks, and I will read the moment you send it."
)

INVALID_MESSAGE = (
    "That does not look like a question I can read. Ask me something you would like "
    "guidance about, for example work, money, relationships, home or the coming period."
)

_TOPIC_WORDS = {keyword for config in TOPICS.values() for keyword in config["keywords"]}
_COMMON_WORDS = {
    "what", "when", "how", "will", "should", "is", "are", "my", "i", "a", "an", "the",
    "about", "for", "of", "it", "this", "that", "there", "be", "can", "could", "go",
    "does", "do", "any", "in", "on", "at", "to", "me", "have", "has", "get", "good",
    "watch", "careful", "happen", "going", "look", "looking", "make", "earning", "earn",
    "decision", "interview", "relationship", "relationships", "moment", "time", "period",
}
_KNOWN = _TOPIC_WORDS | _COMMON_WORDS


def normalize(question: str) -> str:
    return re.sub(r"[^a-z\s]", " ", (question or "").lower()).strip()


def classify_message(question: str) -> str:
    """Returns 'greeting', 'invalid' or 'valid'."""
    normalized = normalize(question)
    if not normalized:
        return "invalid"
    if normalized in GREETINGS:
        return "greeting"
    words: List[str] = normalized.split()
    if any(word in _KNOWN for word in words):
        return "valid"
    if len(words) == 1 and len(words[0]) <= 8:
        return "invalid"
    if len(words) <= 2 and all(len(word) <= 6 for word in words):
        return "invalid"
    return "valid"


def is_invalid_text(question: str) -> bool:
    return classify_message(question) == "invalid"
