"""Ask KAVACH product identity.

Deterministic answers for straightforward "who/what are you" questions, so a
simple identity question never costs a provider call, and so the answer always
comes from the KAVACH PRODUCT identity rather than the underlying provider.

The infrastructure model (Groq/Gemini and their model names) is an
implementation detail. It is never advertised through a normal Ask reply. This
module states the product truth; it never lies about internal facts, it simply
answers at the product level rather than exposing plumbing.
"""

from __future__ import annotations

import re

PRODUCT_NAME = "Ask KAVACH"

# Identity is stated as a general AI assistant that ALSO carries KAVACH's
# astrology capability - never as an astrology-only bot.
IDENTITY_REPLY = (
    "I'm Ask KAVACH, your AI assistant inside KAVACH. I can chat with you "
    "normally, help with questions and everyday tasks, and when you want "
    "astrology guidance, I can also work with your calculated Kundli."
)

MODEL_REPLY = (
    "I'm Ask KAVACH, the AI assistant inside KAVACH. The models behind me are "
    "an implementation detail - what matters is that you get a helpful answer, "
    "with KAVACH's astrology available whenever you want it."
)

CREATOR_REPLY = (
    "I'm part of KAVACH, built to be your AI assistant inside KAVACH - alongside "
    "KAVACH's astrology and Kundli capabilities."
)

PURPOSE_REPLY = (
    "I'm Ask KAVACH - your AI assistant inside KAVACH. I can help with everyday "
    "questions, explanations, ideas, writing, decisions and reasoning, and when "
    "you want astrology guidance I can also read your calculated Kundli and "
    "explain what it shows."
)

# The provider names must never appear in a public Ask reply.
_PROVIDER_TOKENS = (
    "openai", "chatgpt", "gpt", "groq", "gemini", "llama", "nvidia",
    "anthropic", "claude", "gemma", "meta ai", "generator", "language model",
)

# Product pronouns: a question about the assistant itself, not about the world.
_SUBJECT_PATTERN = re.compile(
    r"\b(you are|you're|youre|are you|who are you|who're you|what are you"
    r"|what's your|whats your|what is your|who built|who made|who created"
    r"|who developed|your purpose|your name|what model|which model|what llm"
    r"|which llm|what ai|which ai|are you an? ai|your identity)"
)

_TOPIC_PATTERN = re.compile(
    r"\b(kavach|assistant|chatbot|chat bot|bot|ai|name|identity|purpose"
    r"|model|llm|built|made|created|developed|backend|version)\b"
)

# Questions that mention a provider and therefore deserve the identity answer.
_PROVIDER_QUESTION = re.compile(
    r"\b(chatgpt|openai|gpt|groq|gemini|llama|claude|gemma|nvidia)\b", re.I)

# Greetings about wellbeing are conversation, never identity questions.
_GREETING_PATTERN = re.compile(
    r"\b(how are you|how're you|how r you|how are things|how's it going"
    r"|hows it going|what's up|whats up|how do you feel|good morning"
    r"|good evening|good night|hello|hi there|hey there)\b"
)

_MODEL_WORDS = ("model", "llm", "ai model", "which model", "what model", "version")
_CREATOR_WORDS = ("who made", "who built", "who created", "who developed",
                  "made you", "built you", "created you", "developed you",
                  "your creator", "your maker", "who is behind")
_PURPOSE_WORDS = ("your purpose", "what do you do", "what can you do",
                  "why do you exist", "what are you for")


def is_identity_question(question: str) -> bool:
    """True for a straightforward question about what/who Ask KAVACH is."""
    text = (question or "").lower().strip()
    if not text or len(text.split()) > 14:
        return False
    # "How are you?" is a greeting about wellbeing, not an identity question.
    if _GREETING_PATTERN.search(text):
        return False
    # A question naming an infrastructure provider always gets the product answer.
    if _PROVIDER_QUESTION.search(text):
        return True
    # "What are you?" / "Who are you?" asks for identity; "how" does not.
    if re.search(r"\b(who|what)\s+(are|is|r|s)\s+you\b", text):
        return True
    # A bare capability question ("what can you do", "what do you offer"),
    # never "what can you tell me about <topic>".
    if re.search(r"\bwhat\s+(?:can|do|does)\s+you\s+(?:do|offer|provide|help\s+with)\b", text):
        return True
    return bool(_SUBJECT_PATTERN.search(text) and _TOPIC_PATTERN.search(text))


def identity_reply(question: str) -> str:
    """Deterministic product-level answer, or "" when not an identity question."""
    if not is_identity_question(question):
        return ""
    text = (question or "").lower()
    if any(word in text for word in _CREATOR_WORDS) or "built" in text and "you" in text:
        return CREATOR_REPLY
    if any(word in text for word in _MODEL_WORDS):
        return MODEL_REPLY
    if any(word in text for word in _PURPOSE_WORDS):
        return PURPOSE_REPLY
    return IDENTITY_REPLY


def mentions_provider(text: str) -> bool:
    """True when a reply leaks an underlying provider/model name."""
    low = (text or "").lower()
    return any(token in low for token in _PROVIDER_TOKENS)
