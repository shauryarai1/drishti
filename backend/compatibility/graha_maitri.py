"""Graha Maitri / Rashiadhipathi (mental & emotional alignment).

Source: deck 2, slides 2-4. The COMPLETE natural planetary friendship table is
encoded exactly as supplied. This table belongs ONLY to the marriage
compatibility methodology - it is NOT the proprietary KAVACH BNN registry, and
`backend/kundli/analysis/relationships.py` is not touched.

Source-supported scoring: mutual friends = the full 5 sanctioned points,
mutual neutral = 3 (explicit in the deck), mutual enemies = 0 (explicit in the
deck). Mixed cases are qualitative only, because the deck gives no value.
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

from .models import FactorResult, PersonFacts

FRIEND = "friend"
ENEMY = "enemy"
NEUTRAL = "neutral"

# Natural planetary friendship (Sun..Saturn) exactly as supplied. Rahu/Ketu are
# not part of this table.
NATURAL_FRIENDSHIP: Dict[str, Dict[str, Tuple[str, ...]]] = {
    "Sun": {"friends": ("Moon", "Mars", "Jupiter"), "enemies": ("Venus", "Saturn"), "neutral": ("Mercury",)},
    "Moon": {"friends": ("Sun", "Mercury"), "enemies": (), "neutral": ("Venus", "Mars", "Jupiter", "Saturn")},
    "Mercury": {"friends": ("Sun", "Venus"), "enemies": ("Moon",), "neutral": ("Mars", "Jupiter", "Saturn")},
    "Mars": {"friends": ("Sun", "Moon", "Jupiter"), "enemies": ("Mercury",), "neutral": ("Venus", "Saturn")},
    "Jupiter": {"friends": ("Sun", "Moon", "Mars"), "enemies": ("Mercury", "Venus"), "neutral": ("Saturn",)},
    "Venus": {"friends": ("Mercury", "Saturn"), "enemies": ("Sun", "Moon"), "neutral": ("Mars", "Jupiter")},
    "Saturn": {"friends": ("Mercury", "Venus"), "enemies": ("Sun", "Moon", "Mars"), "neutral": ("Jupiter",)},
}

_LABEL = {FRIEND: "friends", ENEMY: "enemies", NEUTRAL: "neutral"}


def relation(source: str, target: str) -> str:
    """How `source` views `target` in this compatibility table."""
    row = NATURAL_FRIENDSHIP.get(source)
    if not row or source == target:
        return NEUTRAL
    if target in row["friends"]:
        return FRIEND
    if target in row["enemies"]:
        return ENEMY
    return NEUTRAL


def are_friends(first: str, second: str) -> bool:
    """One-directional friendship suffices for the Rashi mitigation rule."""
    return relation(first, second) == FRIEND or relation(second, first) == FRIEND


def evaluate(bride: PersonFacts, groom: PersonFacts) -> FactorResult:
    bride_view = relation(bride.moon_ruler, groom.moon_ruler)
    groom_view = relation(groom.moon_ruler, bride.moon_ruler)

    points: Optional[int]
    if bride_view == FRIEND and groom_view == FRIEND:
        status, points = "Strong alignment", 5
        summary = "Both Moon-sign rulers regard each other as friends, which the source treats as strongly supportive."
    elif bride_view == NEUTRAL and groom_view == NEUTRAL:
        status, points = "Supportive", 3
        summary = "Both Moon-sign rulers are neutral to each other; the source allows a supportive reading in this case."
    elif bride_view == ENEMY and groom_view == ENEMY:
        status, points = "Needs attention", 0
        summary = "Both Moon-sign rulers regard each other as enemies, which the source treats as a factor needing attention."
    elif ENEMY in (bride_view, groom_view):
        status, points = "Needs attention", None
        summary = "One Moon-sign ruler regards the other as an enemy, which the source treats as a factor needing attention."
    else:
        status, points = "Supportive", None
        summary = "The traditional agreement is met, although the source notes it falls short of a full match."

    return FactorResult(
        key="graha_maitri",
        label="Mental & emotional alignment",
        subtitle="Graha Maitri",
        status=status,
        summary=summary,
        facts={
            "brideMoonRuler": bride.moon_ruler,
            "groomMoonRuler": groom.moon_ruler,
            "brideViewOfGroom": _LABEL[bride_view],
            "groomViewOfBride": _LABEL[groom_view],
        },
        points_awarded=points,
    )
