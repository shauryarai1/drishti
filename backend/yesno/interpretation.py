"""Deterministic interpretation templates for KAVACH YES / NO.

The engine decides the verdict from the two planets and their directional BNN
relationship. This layer translates that into ordinary language and NEVER names
its source: no planet names, no reduced numbers, no FRIEND / ENEMY / NEUTRAL and
no mention of how the time was reduced. The calculation mechanics are private and
must not appear in any public output.

No language model is involved, and the wording never overrides the verdict.
"""

from __future__ import annotations

import re
from types import MappingProxyType
from typing import Mapping, Tuple

from .relationships import ENEMY, EVEN, FRIEND, NEUTRAL, NO, YES

CERTAINTY_DISCLAIMER = "This is astrological guidance, not a guarantee of any outcome."

# Natural-language voice for each planet's character. INTERNAL ONLY: the phrases
# never name the planet they came from, and they are the only planetary material
# allowed to reach the public interpretation.
PLANET_VOICE: Mapping[str, str] = MappingProxyType({
    "Sun": "there is a pull toward taking the lead and being seen for it",
    "Moon": "feelings and comfort carry more weight than usual",
    "Jupiter": "there is a helpful opening for growth and support",
    "Rahu": "there may be stronger-than-usual uncertainty or unexpected developments",
    "Mercury": "clear communication and attention to detail will matter",
    "Venus": "there is a supportive tendency toward agreement, comfort or a favourable resolution",
    "Ketu": "the matter may turn inward, or what matters most may not be the obvious outcome",
    "Saturn": "there may be some delay, and patience and consistency will matter",
    "Mars": "the situation may move quickly and could call for decisive action",
})

_OPENERS: Mapping[str, Tuple[str, ...]] = {
    YES: (
        "The indication is positive.",
        "The combination points toward a favourable outcome.",
        "This leans toward yes.",
    ),
    NO: (
        "The indication currently leans against the outcome you are asking about.",
        "The combination points more toward resistance.",
        "This leans toward no for now.",
    ),
    EVEN: (
        "The indication is mixed.",
        "The result is not strongly tilted either way.",
        "The combination suggests an uncertain, balanced outcome.",
    ),
}

# How the two tendencies relate - the relationship status is never named.
_INTERACTIONS: Mapping[str, str] = {
    FRIEND: "The two tendencies support each other, so the indication points in a "
            "favourable direction - though the result will still depend on what you do with it.",
    ENEMY: "The two tendencies work against each other, which is where the resistance comes "
           "from; this describes the current tilt rather than a fixed outcome.",
    NEUTRAL: "Neither tendency strongly outweighs the other, so the outcome is likely to "
             "depend more on your own next steps than on the timing.",
}


def _capitalise(text: str) -> str:
    return text[:1].upper() + text[1:] if text else text


def _clean_question(question: str, limit: int = 140) -> str:
    """A safe, short echo of the user's question (no markup, no control chars)."""
    text = re.sub(r"[`*_<>|#\[\]]+", " ", question or "")
    text = re.sub(r"\s+", " ", text).strip().strip('"').strip("'")
    text = text.rstrip("?").strip()
    if len(text) > limit:
        text = text[: limit - 1].rstrip() + "\u2026"
    return text


def _combination(hour_planet: str, minute_planet: str) -> str:
    """Weave both planetary voices without naming either of them."""
    hour_voice = PLANET_VOICE.get(hour_planet, "")
    minute_voice = PLANET_VOICE.get(minute_planet, "")
    if not hour_voice and not minute_voice:
        return ""
    if hour_planet == minute_planet:
        return (
            f"The same quality shows up on both sides - {hour_voice} - which strengthens it "
            "but leaves nothing to balance it against."
        )
    if not minute_voice:
        return f"{_capitalise(hour_voice)}."
    return f"{_capitalise(hour_voice)}, while {minute_voice}."


def build_interpretation(
    question: str,
    verdict: str,
    hour_planet: str,
    minute_planet: str,
    relationship: str,
    hour_number: int,
    minute_number: int,
) -> str:
    """A short, deterministic explanation of an already-decided verdict."""
    if verdict not in _OPENERS:
        raise ValueError(f"Unknown verdict {verdict!r}")

    # The reduced numbers only pick which neutral phrasing variant is used; they
    # are never written into the text.
    index = (int(hour_number) + int(minute_number)) % 3
    topic = _clean_question(question)

    opener = _OPENERS[verdict][index]
    if topic:
        opener = f'"{topic}" - {opener}'

    parts = [
        opener,
        _combination(hour_planet, minute_planet),
        _INTERACTIONS.get(relationship, ""),
        CERTAINTY_DISCLAIMER,
    ]
    return " ".join(part for part in parts if part)
