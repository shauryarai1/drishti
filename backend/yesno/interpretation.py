"""Deterministic interpretation templates for KAVACH YES / NO.

No language model is involved. The verdict is already decided by
`yesno.relationships`; this module only verbalises it from the two planets, their
relationship and their planetary themes.

The wording never claims certainty and never overrides the verdict: Saturn can
add delay without turning YES into NO, Mars can add speed without creating a YES,
and Rahu or Ketu never by themselves produce a NO.
"""

from __future__ import annotations

import re
from typing import Mapping, Sequence, Tuple

from .planets import themes_for
from .relationships import ENEMY, EVEN, FRIEND, NEUTRAL, NO, YES

CERTAINTY_DISCLAIMER = "This is astrological guidance, not a guarantee of any outcome."

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

_RELATIONSHIP_LINES: Mapping[str, Tuple[str, ...]] = {
    FRIEND: (
        "Because {hour} and {minute} support one another, the two influences reinforce "
        "the same direction.",
        "{hour} and {minute} work together here, so the qualities they bring point the "
        "same way.",
    ),
    ENEMY: (
        "{hour} and {minute} are working against each other, which is where the "
        "resistance comes from.",
        "The two influences pull in different directions, so they do not carry the "
        "outcome forward easily.",
    ),
    NEUTRAL: (
        "Neither planet strongly supports nor strongly blocks the other, so the timing "
        "alone does not decide this.",
        "{hour} and {minute} neither strongly support nor strongly oppose each other.",
    ),
}

_CLOSINGS: Mapping[str, Tuple[str, ...]] = {
    YES: (
        "It is a supportive indication, not a guarantee - treat it as guidance and let "
        "your own judgement decide the next step.",
        "The tilt is favourable, though the outcome still depends on what you do with it.",
    ),
    NO: (
        "This is not permanent: conditions change, and this describes the current tilt "
        "rather than a fixed outcome.",
        "The indication is against it for now, but timing shifts and nothing here is final.",
    ),
    EVEN: (
        "With a balanced indication, the outcome is likely to depend more on your own "
        "next steps than on the timing.",
        "Treat this as a genuinely open question rather than a prediction either way.",
    ),
}


def _join(items: Sequence[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


def _clean_question(question: str, limit: int = 140) -> str:
    """A safe, short echo of the user's question (no markup, no control chars)."""
    text = re.sub(r"[`*_<>|#\[\]]+", " ", question or "")
    text = re.sub(r"\s+", " ", text).strip().strip('"').strip("'")
    text = text.rstrip("?").strip()
    if len(text) > limit:
        text = text[: limit - 1].rstrip() + "\u2026"
    return text


def _themes(planet: str) -> str:
    return _join(list(themes_for(planet, limit=3)))


def _same_planet_line(planet: str) -> str:
    return (
        f"Because both the hour and the minute reduce to {planet}, the same quality is "
        f"doubled: {_themes(planet)}. That strengthens the planet's own character but "
        "gives it no partner to support or oppose it, which is why the indication stays "
        "balanced."
    )


def _nuances(verdict: str, hour_planet: str, minute_planet: str) -> list:
    planets = (hour_planet, minute_planet)
    lines: list = []
    if "Saturn" in planets:
        lines.append({
            YES: "Saturn adds patience, responsibility and delay, so what develops is more "
                 "likely to become established than to arrive immediately.",
            NO: "Saturn's delay and weight are part of the friction here, so this is not the "
                "moment for forcing a result.",
            EVEN: "Saturn adds patience and a slower tempo, which keeps things measured "
                  "rather than quick.",
        }[verdict])
    if "Mars" in planets:
        lines.append({
            YES: "Mars adds drive and urgency, so progress can come quickly, though it still "
                 "needs support to hold.",
            NO: "Mars adds urgency and friction, which can make the matter feel more "
                "confrontational than it needs to.",
            EVEN: "Mars adds speed and pressure, which can push the situation either way.",
        }[verdict])
    if "Rahu" in planets:
        lines.append("Rahu amplifies and unsettles, so the situation may feel more intense or "
                     "unconventional than it first appears.")
    if "Ketu" in planets:
        lines.append("Ketu turns the matter inward or away from the material side, so what "
                     "matters here may not be the obvious outcome.")
    return lines


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

    index = (int(hour_number) + int(minute_number)) % 3
    topic = _clean_question(question)

    opener = _OPENERS[verdict][index]
    if topic:
        opener = f'"{topic}" - {opener}'

    if hour_planet == minute_planet:
        # The doubling sentence already explains the balance, so no separate
        # relationship sentence is added for a planet paired with itself.
        combination = _same_planet_line(hour_planet)
        relationship_line = ""
    else:
        combination = f"{hour_planet} brings {_themes(hour_planet)}; {minute_planet} brings {_themes(minute_planet)}."
        relationship_line = _RELATIONSHIP_LINES[relationship][index % len(_RELATIONSHIP_LINES[relationship])]
        relationship_line = relationship_line.format(hour=hour_planet, minute=minute_planet)

    parts = [opener, combination, relationship_line]
    parts.extend(_nuances(verdict, hour_planet, minute_planet))
    parts.append(_CLOSINGS[verdict][index % 2])
    parts.append(CERTAINTY_DISCLAIMER)
    return " ".join(part for part in parts if part)
