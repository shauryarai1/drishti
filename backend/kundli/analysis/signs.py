"""Sign-level technical tables (KAVACH Kundli analysis)."""

from __future__ import annotations

from typing import Dict, List, Tuple

from jyotish.planets import RULERSHIP

RASHIS: Tuple[str, ...] = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

MOVABLE = ("Aries", "Cancer", "Libra", "Capricorn")
FIXED = ("Taurus", "Leo", "Scorpio", "Aquarius")
DUAL = ("Gemini", "Virgo", "Sagittarius", "Pisces")

FIRE = ("Aries", "Leo", "Sagittarius")
EARTH = ("Taurus", "Virgo", "Capricorn")
AIR = ("Gemini", "Libra", "Aquarius")
WATER = ("Cancer", "Scorpio", "Pisces")

# house groups
PURUSHARTHA: Dict[str, Tuple[int, ...]] = {
    "Dharma": (1, 5, 9),
    "Artha": (2, 6, 10),
    "Kama": (3, 7, 11),
    "Moksha": (4, 8, 12),
}

SIGN_LORD: Dict[str, str] = {
    sign: lord for lord, signs in RULERSHIP.items() for sign in signs
}

ELEMENTS: Dict[str, Tuple[str, ...]] = {"Fire": FIRE, "Earth": EARTH, "Air": AIR, "Water": WATER}
MODALITIES: Dict[str, Tuple[str, ...]] = {"Movable": MOVABLE, "Fixed": FIXED, "Dual": DUAL}

MOVABLE_BADHAKA_HOUSE = 11
FIXED_BADHAKA_HOUSE = 9
DUAL_BADHAKA_HOUSE = 7


def sign_index(sign: str) -> int:
    return RASHIS.index(sign)


def house_sign(lagna_sign: str, house: int) -> str:
    return RASHIS[(sign_index(lagna_sign) + house - 1) % 12]


def sign_distance(reference_sign: str, target_sign: str) -> int:
    """Inclusive forward distance 1..12 (1 = same sign)."""
    return ((sign_index(target_sign) - sign_index(reference_sign)) % 12) + 1


def house_lord(lagna_sign: str, house: int) -> str:
    return SIGN_LORD[house_sign(lagna_sign, house)]


def group_members(group: Tuple[str, ...], placements: Dict[str, Dict[str, str]]) -> List[str]:
    return [planet for planet, data in placements.items() if data.get("rashi") in group]


def planets_by_house(placements: Dict[str, Dict[str, str]], house: int) -> List[str]:
    return [planet for planet, data in placements.items() if data.get("house") == house]
