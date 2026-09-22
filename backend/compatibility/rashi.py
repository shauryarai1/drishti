"""Rashi Kuta (Moon-sign dynamic).

Source: deck 1, slides 13-17. The rule is DIRECTIONAL and is preserved exactly:
the bride's Moon sign is counted from the groom's Moon sign (inclusive).

    position 2..7  -> traditionally supportive (the bride's Moon "follows" his)
    position 1     -> same sign; the source then examines the nakshatra order
    position 8..12 -> the reverse direction, which the source treats as adverse

Mitigation: the adverse disposition is cancelled when the two Moon signs share
a ruler, or when their rulers are friends in the compatibility natural
friendship table (deck 2). The source notes that only two points are awarded in
cancellation cases - that value is shown on this card only and is never totalled.

The source's statements about longevity, wealth, progeny, health and poverty are
deliberately NOT reproduced; the output uses neutral compatibility language.
"""

from __future__ import annotations

from typing import Sequence

from .graha_maitri import are_friends
from .models import FactorResult, PersonFacts

POINTS_ON_CANCELLATION = 2


def position_from(from_index: int, to_index: int, total: int = 12) -> int:
    """Inclusive count of `to` from `from` (1..total)."""
    return ((to_index - from_index) % total) + 1


def evaluate(bride: PersonFacts, groom: PersonFacts, signs: Sequence[str]) -> FactorResult:
    bride_index = list(signs).index(bride.moon_sign)
    groom_index = list(signs).index(groom.moon_sign)

    # The bride's Moon sign counted from the groom's.
    position = position_from(groom_index, bride_index)

    same_ruler = bride.moon_ruler == groom.moon_ruler
    rulers_friendly = are_friends(bride.moon_ruler, groom.moon_ruler)
    cancelled = same_ruler or rulers_friendly

    points = None
    if position == 1:
        status = "Mixed"
        summary = (
            "Both Moons fall in the same sign. The source treats this as a mixed "
            "placement and looks at the nakshatra order for the finer reading."
        )
    elif 2 <= position <= 7:
        status = "Supportive"
        summary = (
            "The bride's Moon sign falls in one of the traditionally supportive "
            "positions relative to the groom's Moon sign."
        )
    elif cancelled:
        status = "Supportive"
        points = POINTS_ON_CANCELLATION
        summary = (
            "The position is one the source treats as adverse, but the traditional "
            "mitigation applies because the two Moon signs are ruled by the same "
            "planet or by rulers who are friends."
        )
    else:
        status = "Needs attention"
        summary = (
            "The Moon signs fall in the reverse direction, which the source "
            "traditionally treats as deserving additional consideration."
        )

    return FactorResult(
        key="rashi",
        label="Moon-sign dynamic",
        subtitle="Rashi Kuta",
        status=status,
        summary=summary,
        facts={
            "brideMoonSign": bride.moon_sign,
            "groomMoonSign": groom.moon_sign,
            "positionFromGroom": position,
            "mitigationApplied": cancelled,
            "sameRuler": same_ruler,
            "rulersAreFriends": rulers_friendly,
        },
        points_awarded=points,
    )
