"""Nadi.

Source: deck 1, slides 9-12. The complete 27-nakshatra Vaata / Pitta / Kapha
classification is encoded exactly. The deck assigns no points and makes claims
about progeny/hereditary factors which this feature must never surface, so the
result is limited to traditional compatibility terminology.
"""

from __future__ import annotations

from typing import Dict

from .models import FactorResult, PersonFacts

VAATA = "Vaata"
PITTA = "Pitta"
KAPHA = "Kapha"

NADI_BY_NAKSHATRA: Dict[str, str] = {
    VAATA: "Vaata", PITTA: "Pitta", KAPHA: "Kapha",
}
NADI_BY_NAKSHATRA = {
    # Vaata (9)
    "Ashwini": VAATA, "Ardra": VAATA, "Punarvasu": VAATA,
    "Uttara Phalguni": VAATA, "Hasta": VAATA, "Jyeshtha": VAATA,
    "Mula": VAATA, "Shatabhisha": VAATA, "Purva Bhadrapada": VAATA,
    # Pitta (9)
    "Bharani": PITTA, "Mrigashira": PITTA, "Pushya": PITTA,
    "Purva Phalguni": PITTA, "Chitra": PITTA, "Anuradha": PITTA,
    "Purva Ashadha": PITTA, "Dhanishta": PITTA, "Uttara Bhadrapada": PITTA,
    # Kapha (9)
    "Krittika": KAPHA, "Rohini": KAPHA, "Ashlesha": KAPHA, "Magha": KAPHA,
    "Swati": KAPHA, "Vishakha": KAPHA, "Uttara Ashadha": KAPHA,
    "Shravana": KAPHA, "Revati": KAPHA,
}


def nadi_of(nakshatra: str) -> str:
    return NADI_BY_NAKSHATRA[nakshatra]


def evaluate(bride: PersonFacts, groom: PersonFacts) -> FactorResult:
    bride_nadi = nadi_of(bride.moon_nakshatra)
    groom_nadi = nadi_of(groom.moon_nakshatra)
    different = bride_nadi != groom_nadi

    return FactorResult(
        key="nadi",
        label="Traditional Nadi match",
        subtitle="Nadi",
        status="Supportive" if different else "Needs attention",
        summary=(
            "The two Moon nakshatras fall in different Nadi categories, which "
            "is traditionally considered supportive."
            if different
            else
            "Both Moon nakshatras fall in the same Nadi category, which is "
            "traditionally treated as a compatibility factor that deserves "
            "additional consideration."
        ),
        facts={
            "brideNakshatra": bride.moon_nakshatra,
            "brideNadi": bride_nadi,
            "groomNakshatra": groom.moon_nakshatra,
            "groomNadi": groom_nadi,
        },
    )
