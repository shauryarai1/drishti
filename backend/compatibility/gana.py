"""Gana (temperament).

Source: deck 1, slides 6-8. The deck gives the complete 27-nakshatra Gana
classification, but NO point matrix, so this factor is qualitative only.

The source's directional preference is preserved: the same Gana is ideal, and a
bride of a "better" temperament than the groom is acceptable while the reverse
is traditionally treated as needing attention. The deck's demeaning personality
descriptions are deliberately NOT reproduced.
"""

from __future__ import annotations

from typing import Dict

from .models import FactorResult, PersonFacts

DEVA = "Deva"
MANUSHYA = "Manushya"
RAKSHASA = "Rakshasa"

GANA_BY_NAKSHATRA: Dict[str, str] = {
    # Deva (9)
    "Ashwini": DEVA, "Mrigashira": DEVA, "Punarvasu": DEVA, "Pushya": DEVA,
    "Hasta": DEVA, "Swati": DEVA, "Anuradha": DEVA, "Shravana": DEVA, "Revati": DEVA,
    # Manushya (9)
    "Bharani": MANUSHYA, "Rohini": MANUSHYA, "Ardra": MANUSHYA,
    "Purva Phalguni": MANUSHYA, "Uttara Phalguni": MANUSHYA,
    "Purva Ashadha": MANUSHYA, "Uttara Ashadha": MANUSHYA,
    "Purva Bhadrapada": MANUSHYA, "Uttara Bhadrapada": MANUSHYA,
    # Rakshasa (9)
    "Krittika": RAKSHASA, "Ashlesha": RAKSHASA, "Magha": RAKSHASA, "Chitra": RAKSHASA,
    "Vishakha": RAKSHASA, "Jyeshtha": RAKSHASA, "Mula": RAKSHASA,
    "Dhanishta": RAKSHASA, "Shatabhisha": RAKSHASA,
}

_RANK = {DEVA: 3, MANUSHYA: 2, RAKSHASA: 1}


def gana_of(nakshatra: str) -> str:
    return GANA_BY_NAKSHATRA[nakshatra]


def evaluate(bride: PersonFacts, groom: PersonFacts) -> FactorResult:
    bride_gana = gana_of(bride.moon_nakshatra)
    groom_gana = gana_of(groom.moon_nakshatra)

    if bride_gana == groom_gana:
        status = "Strong alignment"
        summary = (
            "Both charts share the same traditional temperament category, which "
            "the source treats as the most comfortable arrangement."
        )
    elif _RANK[bride_gana] > _RANK[groom_gana]:
        status = "Supportive"
        summary = (
            "The temperaments differ, but the traditional reading treats this "
            "direction as workable."
        )
    else:
        status = "Needs attention"
        summary = (
            "The temperaments differ in the direction the source treats as "
            "deserving additional consideration."
        )

    return FactorResult(
        key="gana",
        label="Temperament",
        subtitle="Gana",
        status=status,
        summary=summary,
        facts={
            "brideNakshatra": bride.moon_nakshatra,
            "brideGana": bride_gana,
            "groomNakshatra": groom.moon_nakshatra,
            "groomGana": groom_gana,
        },
    )
