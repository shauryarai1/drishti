"""Nakshatra-lord rulership engine for KAVACH Daily Prediction.

This module starts after the production astronomy path has established the
transit Moon Nakshatra.  It never calculates or consults a planet's transit
position: the Nakshatra lord contributes only its owner-approved sign
rulership.
"""

from __future__ import annotations

from typing import Dict, Iterable, Tuple

from jyotish.planets import RULERSHIP
from kundli.analysis.signs import RASHIS, sign_distance
from kundli.nakshatra import lord_for_name

from .config import CAUTION, GOOD, HOUSE_PATTERNS, NEUTRAL, status


class UnsupportedNakshatraLordError(ValueError):
    """Raised when no owner-approved sign rulership exists for a lord."""


_NAKSHATRA_SPELLING_ALIASES = {
    # The repository's canonical spelling is Dhanishta; accept the spelling
    # used in the owner-supplied Daily methodology without duplicating its lord.
    "dhanishtha": "Dhanishta",
}


def nakshatra_lord(nakshatra: str) -> str:
    """Return the repository-approved lord for a named Nakshatra."""
    canonical = _NAKSHATRA_SPELLING_ALIASES.get(nakshatra.strip().lower(), nakshatra)
    lord = lord_for_name(canonical)
    if not lord:
        raise ValueError(f"Unknown Nakshatra: {nakshatra!r}")
    return lord


def ruled_rashis(lord: str) -> Tuple[str, ...]:
    """Return approved ruled signs without inventing ownership for the nodes."""
    signs = tuple(RULERSHIP.get(lord) or ())
    if not signs:
        raise UnsupportedNakshatraLordError(
            f"No owner-approved sign rulership is defined for Nakshatra lord {lord}."
        )
    return signs


def whole_sign_house(native_moon_sign: str, ruled_rashi: str) -> int:
    """Whole-sign house of ``ruled_rashi`` from the native Moon sign."""
    return sign_distance(native_moon_sign, ruled_rashi)


def active_houses(native_moon_sign: str, ruled_signs: Iterable[str]) -> Tuple[int, ...]:
    """Active houses, retaining the authoritative order of the ruled signs."""
    return tuple(whole_sign_house(native_moon_sign, sign) for sign in ruled_signs)


def active_houses_for_nakshatra(native_moon_sign: str, nakshatra: str) -> Tuple[int, ...]:
    """Resolve Nakshatra -> lord -> ruled signs -> whole-sign houses."""
    return active_houses(native_moon_sign, ruled_rashis(nakshatra_lord(nakshatra)))


# Concise actions grounded in the existing owner-approved HOUSE_PATTERNS.  This
# is language data, not a second house-meaning registry or a combination table.
_HOUSE_ACTION = {
    1: "choices that reflect your own priorities",
    2: "clear speech and practical handling of resources",
    3: "direct communication and steady personal effort",
    4: "attention to home, comfort and emotional steadiness",
    5: "creative thinking and time for learning or enjoyment",
    6: "an orderly approach to work, routine and obstacles",
    7: "balanced cooperation in one-to-one relationships",
    8: "patient investigation of shared or unclear matters",
    9: "guidance, perspective and a wider view",
    10: "clear priorities around career and responsibility",
    11: "constructive contact with networks and opportunities",
    12: "rest, reflection and thoughtful handling of expenses",
}


def _theme(house: int) -> str:
    return str(HOUSE_PATTERNS[house]["theme"])


def compose_prediction(houses: Tuple[int, ...]) -> str:
    """Create one deterministic prediction integrating one or two houses."""
    if len(houses) == 1:
        house = houses[0]
        return f"{_theme(house)} comes into focus today. Favour {_HOUSE_ACTION[house]}."
    if len(houses) != 2:
        raise ValueError("Daily rulership must activate one or two houses.")

    first, second = houses
    first_theme = _theme(first)
    second_theme = _theme(second).lower()
    variants = (
        f"{first_theme} and {second_theme} share the spotlight today. "
        f"Favour {_HOUSE_ACTION[first]} alongside {_HOUSE_ACTION[second]}.",
        f"Give attention to {first_theme.lower()} while making room for {second_theme}. "
        f"A balance of {_HOUSE_ACTION[first]} and {_HOUSE_ACTION[second]} may help.",
        f"{first_theme} may connect with {second_theme} today. "
        f"Lean on {_HOUSE_ACTION[first]} without losing sight of {_HOUSE_ACTION[second]}.",
    )
    return variants[(first * 13 + second) % len(variants)]


_STATUS_PRIORITY = {GOOD: 0, NEUTRAL: 1, CAUTION: 2}


def compose_categories(houses: Tuple[int, ...]) -> Dict[str, Dict[str, str]]:
    """Category guidance derived only from the active house or houses."""
    result: Dict[str, Dict[str, str]] = {}
    for category in ("love", "health", "career"):
        entries = [status(house, category) for house in houses]
        level = max((entry[0] for entry in entries), key=_STATUS_PRIORITY.__getitem__)
        if len(houses) == 1:
            reason = entries[0][1]
        else:
            first, second = houses
            if category == "love":
                reason = (
                    f"Relationships may need to balance {_theme(first).lower()} with "
                    f"{_theme(second).lower()}; keep expectations flexible and clear."
                )
            elif category == "health":
                reason = (
                    f"Wellbeing may reflect both {_theme(first).lower()} and "
                    f"{_theme(second).lower()}; choose a sustainable pace."
                )
            else:
                reason = (
                    f"Work decisions may involve {_theme(first).lower()} alongside "
                    f"{_theme(second).lower()}; set one practical priority at a time."
                )
        result[category] = {"status": level, "reason": reason}
    return result
