"""PRIVATE KAVACH Navtara constants.

Nothing in this package is customer-facing. The 27-Nakshatra order is
canonical here; a normaliser maps the Panchang engine's spellings onto it so
there is only one counting source.
"""

from __future__ import annotations

from typing import Dict, Tuple

# Canonical 27 Nakshatras (position order, wraps Revati -> Ashwini).
NAKSHATRAS: Tuple[str, ...] = (
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
)
NAKSHATRA_COUNT = len(NAKSHATRAS)

# Nine-Tara cycle.
TARA_SEQUENCE: Tuple[str, ...] = (
    "Janma", "Sampat", "Vipat", "Kshema", "Pratyari",
    "Sadhaka", "Vadha", "Mitra", "AtiMitra",
)
TARA_CYCLE = len(TARA_SEQUENCE)

# The three caution Taras - distinct meanings, never identical treatment.
CAUTION_TARAS: Tuple[str, ...] = ("Vipat", "Pratyari", "Vadha")
STRONGEST_CAUTION = "Vadha"

# Separate Special Nakshatra layer (counted from the same Janma Nakshatra).
SPECIAL_ROLES: Dict[int, str] = {
    4: "Jati",
    10: "Karma",
    12: "Desha",
    13: "Abhisheka",
    16: "Sanghatika",
    18: "Samudaya",
    19: "Adhana",
}


def _normalise(name: str) -> str:
    return "".join(character for character in (name or "").lower() if character.isalpha())


# Known spelling variants used elsewhere in the repository.
SPELLING_ALIASES: Dict[str, str] = {
    "ashvini": "Ashwini",
    "purvabhadrapada": "Purva Bhadrapada",
    "uttarabhadrapada": "Uttara Bhadrapada",
    "purvaashadha": "Purva Ashadha",
    "uttaraashadha": "Uttara Ashadha",
}

_CANONICAL_BY_NORMALISED: Dict[str, str] = {_normalise(name): name for name in NAKSHATRAS}
_CANONICAL_BY_NORMALISED.update(SPELLING_ALIASES)


def canonical_nakshatra(name: str) -> str:
    """Map an incoming (possibly differently spelled) Nakshatra onto the canon."""
    return _CANONICAL_BY_NORMALISED.get(_normalise(name), name)


def nakshatra_index(name: str) -> int:
    """0-based canonical index."""
    canonical = canonical_nakshatra(name)
    if canonical not in NAKSHATRAS:
        raise ValueError(f"unknown nakshatra: {name}")
    return NAKSHATRAS.index(canonical)
