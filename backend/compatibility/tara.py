"""Dina / Tara Kuta.

Source rule (deck 1, slide 5): count the number of nakshatras of the man's
natal Moon FROM that of the woman (inclusive: Ashwini -> Ashlesha is "9 away"),
divide that count by nine, and the agreement is good when the remainder is
0, 2, 4, 6 or 8.

Direction is preserved: the count runs from the BRIDE's Moon nakshatra to the
GROOM's. The factor is sanctioned 3 points in the source; the good/bad
condition is completely determinable, so the 3/0 value is retained internally
and shown on its own card (never totalled).
"""

from __future__ import annotations

from typing import Sequence

from .models import FactorResult, PersonFacts

FAVOURABLE_REMAINDERS = (0, 2, 4, 6, 8)
POINTS = 3


def tara_count(bride_index: int, groom_index: int, total: int = 27) -> int:
    """Inclusive count of the groom's nakshatra from the bride's (1..total)."""
    return ((groom_index - bride_index) % total) + 1


def evaluate(bride: PersonFacts, groom: PersonFacts, nakshatras: Sequence[str]) -> FactorResult:
    bride_index = list(nakshatras).index(bride.moon_nakshatra)
    groom_index = list(nakshatras).index(groom.moon_nakshatra)
    count = tara_count(bride_index, groom_index)
    remainder = count % 9
    favourable = remainder in FAVOURABLE_REMAINDERS

    return FactorResult(
        key="tara",
        label="Daily rhythm",
        subtitle="Tara Kuta",
        status="Supportive" if favourable else "Needs attention",
        summary=(
            "The traditional daily-rhythm factor is supportive, which is read as "
            "a reasonable day-to-day ease between the two."
            if favourable
            else
            "The traditional daily-rhythm factor is not favourable, so everyday "
            "coordination may deserve more conscious effort."
        ),
        facts={
            "brideMoonNakshatra": bride.moon_nakshatra,
            "groomMoonNakshatra": groom.moon_nakshatra,
            "remainder": remainder,
        },
        points_awarded=POINTS if favourable else 0,
    )
