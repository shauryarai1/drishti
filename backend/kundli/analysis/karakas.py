"""Karaka classification: Atmakaraka, Yogakaraka, Maraka, Badhaka.

Atmakaraka uses the OWNER-APPROVED 7-planet system (Rahu/Ketu excluded).
No death/lifespan/fatal interpretation is produced anywhere here.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .signs import (
    DUAL,
    DUAL_BADHAKA_HOUSE,
    FIXED,
    FIXED_BADHAKA_HOUSE,
    MOVABLE,
    MOVABLE_BADHAKA_HOUSE,
    RASHIS,
    house_lord,
    house_sign,
    sign_index,
)

AK_PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")

# Owner-approved classic primaries only; other lagnas have no forced Yogakaraka.
YOGAKARAKA_BY_LAGNA: Dict[str, str] = {
    "Taurus": "Saturn",
    "Cancer": "Mars",
    "Leo": "Mars",
    "Libra": "Saturn",
    "Capricorn": "Venus",
    "Aquarius": "Venus",
}

MARAKA_HOUSES = (2, 7)


def degree_in_sign(longitude: float) -> float:
    return float(longitude) % 30.0


def atmakaraka(longitudes: Dict[str, float]) -> Dict[str, Any]:
    """Highest degree-within-sign among the seven eligible planets."""
    eligible = {planet: degree_in_sign(longitudes[planet])
                for planet in AK_PLANETS if planet in longitudes}
    if not eligible:
        return {"atmakaraka": None, "degrees": {}, "excluded": ["Rahu", "Ketu"]}
    winner = max(eligible, key=lambda planet: (eligible[planet], -AK_PLANETS.index(planet)))
    return {
        "atmakaraka": winner,
        "degreeInSign": round(eligible[winner], 4),
        "degrees": {planet: round(value, 4) for planet, value in eligible.items()},
        "excluded": ["Rahu", "Ketu"],
        "ranking": sorted(eligible, key=lambda planet: eligible[planet], reverse=True),
    }


def yogakaraka(lagna_sign: str) -> Optional[str]:
    return YOGAKARAKA_BY_LAGNA.get(lagna_sign)


def maraka(lagna_sign: str) -> Dict[str, Any]:
    """Technical classification only (lords of H2 and H7)."""
    lords = {house: house_lord(lagna_sign, house) for house in MARAKA_HOUSES}
    return {
        "houses": list(MARAKA_HOUSES),
        "signs": {house: house_sign(lagna_sign, house) for house in MARAKA_HOUSES},
        "lords": lords,
        "primaryMarakaLords": sorted(set(lords.values())),
        "note": "technical classification only; not a lifespan or fatality statement",
    }


def badhaka(lagna_sign: str) -> Dict[str, Any]:
    if lagna_sign in MOVABLE:
        house, kind = MOVABLE_BADHAKA_HOUSE, "movable"
    elif lagna_sign in FIXED:
        house, kind = FIXED_BADHAKA_HOUSE, "fixed"
    elif lagna_sign in DUAL:
        house, kind = DUAL_BADHAKA_HOUSE, "dual"
    else:
        return {"house": None, "sign": None, "lord": None, "modality": None}
    sign = house_sign(lagna_sign, house)
    return {
        "modality": kind,
        "house": house,
        "sign": sign,
        "lord": house_lord(lagna_sign, house),
    }


def lagna_summary(lagna_sign: str) -> Dict[str, Any]:
    return {
        "lagnaSign": lagna_sign,
        "lagnaNumber": sign_index(lagna_sign) + 1,
        "lagnesh": house_lord(lagna_sign, 1),
    }
