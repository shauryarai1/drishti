"""Daily composition: HOUSE THEME (WHERE) x transit NAKSHATRA (HOW) x category.

Produces ONE integrated interpretation per field. It is never a house sentence
followed by an appended Nakshatra sentence: the transit Nakshatra modifies how
the house theme expresses.

Deterministic templates only - no LLM, no new astrology rules, and no 12x27
hand-written table. The house content comes from the existing HOUSE_PATTERNS and
the Nakshatra content from the existing approved profiles.
"""

from __future__ import annotations

from typing import Sequence

from nakshatra_knowledge.profiles import profile_for

from .config import HOUSE_PATTERNS, status


def _join(items: Sequence[str]) -> str:
    values = [str(item) for item in items if str(item).strip()]
    if not values:
        return ""
    if len(values) == 1:
        return values[0]
    return ", ".join(values[:-1]) + " and " + values[-1]


def _theme(active_house: int) -> str:
    entry = HOUSE_PATTERNS.get(active_house) or HOUSE_PATTERNS[1]
    return str(entry["theme"])


def compose_daily_pattern(active_house: int, nakshatra: str) -> str:
    """ONE integrated Today's Pattern: the active house read THROUGH the Nakshatra."""
    profile = profile_for(nakshatra)
    mode = _join(profile["mode"])
    focus = _join(profile["focus"])
    caution = _join(profile["caution"])
    return (
        f"{_theme(active_house)} are the day's active area. "
        f"With the Moon in {nakshatra}, this area expresses through {mode}: "
        f"{focus} are favoured, and {caution} is what to watch. "
        f"Let today's choices here follow that tone rather than habit."
    )


def compose_daily_category(active_house: int, nakshatra: str, category: str) -> str:
    """ONE integrated category reading: house meaning modified by the Nakshatra.

    Each category draws on a DIFFERENT facet of the Nakshatra profile, so the
    three are never the same appended clause.
    """
    _level, reason = status(active_house, category)
    profile = profile_for(nakshatra)
    mode = _join(profile["mode"])
    focus = _join(profile["focus"])
    caution = _join(profile["caution"])
    constructive = _join(profile["constructive"])
    challenging = _join(profile["challenging"])

    if category == "love":
        return (
            f"{reason} The {nakshatra} Moon brings {mode} into closeness today, "
            f"and {caution} is best set aside."
        )
    if category == "health":
        return (
            f"{reason} Under the {nakshatra} Moon, {constructive} support your energy, "
            f"and it is worth not letting {challenging} drain it."
        )
    return (
        f"{reason} With the Moon in {nakshatra}, {focus} are the practical route "
        f"forward at work, and {constructive} help it land."
    )
