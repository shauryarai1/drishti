"""Vasya Kuta (mutual influence).

Source: deck 2, slides 5-7. The complete 12-sign amenability mapping is encoded
exactly as supplied ("According to Dr. B. V. Raman"). The deck gives no
per-case point table; the factor is sanctioned 2 points and the source's
example treats "no mutual influence" as no agreement, so 2/0 is retained
without being totalled.

Wording stays neutral: this is described as traditional mutual influence, never
as one partner controlling or subjugating the other.
"""

from __future__ import annotations

from typing import Dict, Tuple

from .models import FactorResult, PersonFacts

AMENABLE: Dict[str, Tuple[str, ...]] = {
    "Aries": ("Leo", "Scorpio"),
    "Taurus": ("Cancer", "Libra"),
    "Gemini": ("Virgo",),
    "Cancer": ("Scorpio", "Sagittarius"),
    "Leo": ("Libra",),
    "Virgo": ("Cancer", "Pisces"),
    "Libra": ("Virgo", "Capricorn"),
    "Scorpio": ("Cancer",),
    "Sagittarius": ("Pisces",),
    "Capricorn": ("Aries", "Aquarius"),
    "Aquarius": ("Aries",),
    "Pisces": ("Capricorn",),
}

POINTS = 2


def evaluate(bride: PersonFacts, groom: PersonFacts) -> FactorResult:
    bride_influences = groom.moon_sign in AMENABLE.get(bride.moon_sign, ())
    groom_influences = bride.moon_sign in AMENABLE.get(groom.moon_sign, ())
    aligned = bride_influences or groom_influences

    return FactorResult(
        key="vasya",
        label="Mutual influence",
        subtitle="Vasya Kuta",
        status="Supportive" if aligned else "Mixed",
        summary=(
            "The Moon signs show traditional mutual-influence alignment, which "
            "the source reads as a supportive factor."
            if aligned
            else
            "The Moon signs show no traditional mutual influence in either "
            "direction, so this factor is read as neutral."
        ),
        facts={
            "brideMoonSign": bride.moon_sign,
            "groomMoonSign": groom.moon_sign,
            "brideInfluencesGroom": bride_influences,
            "groomInfluencesBride": groom_influences,
        },
        points_awarded=POINTS if aligned else 0,
    )
