"""Planet significations, classical rulership and dignity.

Conservative, editable standard-Jyotish tables. Rahu/Ketu receive NO classical
sign ownership and NO invented exaltation/debilitation.
No friend/enemy scoring. No numerical scoring.
"""

from __future__ import annotations

from typing import Dict, Optional

from .provenance import STANDARD_JYOTISH_PROVENANCE

PLANET_SIGNIFICATIONS: Dict[str, str] = {
    "Sun": "identity, vitality, authority, confidence, recognition, leadership, responsibility",
    "Moon": "mind, emotions, receptivity, comfort, adaptability, emotional response",
    "Mars": "energy, initiative, courage, action, competition, assertiveness",
    "Mercury": "intellect, communication, analysis, learning, calculation, adaptability",
    "Jupiter": "knowledge, judgment, guidance, growth, principles, wisdom",
    "Venus": "relationships, harmony, comfort, attraction, creativity, refinement",
    "Saturn": "discipline, responsibility, persistence, delay, structure, endurance",
    "Rahu": "intensification, unconventionality, ambition, restlessness, unfamiliar territory",
    "Ketu": "detachment, inward focus, separation from conventional concerns, analysis, introspection",
}


# Short composed phrases used to build readable sentences.
PLANET_CORE: Dict[str, str] = {
    "Sun": "identity and vitality",
    "Moon": "mind and emotional response",
    "Mars": "initiative and courage",
    "Mercury": "intellect and communication",
    "Jupiter": "knowledge and judgment",
    "Venus": "relationships and harmony",
    "Saturn": "discipline and structure",
    "Rahu": "intensification and restlessness",
    "Ketu": "detachment and introspection",
}

CLASSICAL_PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
NODES = ("Rahu", "Ketu")

RULERSHIP: Dict[str, list] = {
    "Sun": ["Leo"],
    "Moon": ["Cancer"],
    "Mars": ["Aries", "Scorpio"],
    "Mercury": ["Gemini", "Virgo"],
    "Jupiter": ["Sagittarius", "Pisces"],
    "Venus": ["Taurus", "Libra"],
    "Saturn": ["Capricorn", "Aquarius"],
}

EXALTATION: Dict[str, str] = {
    "Sun": "Aries", "Moon": "Taurus", "Mars": "Capricorn", "Mercury": "Virgo",
    "Jupiter": "Cancer", "Venus": "Pisces", "Saturn": "Libra",
}

DEBILITATION: Dict[str, str] = {
    "Sun": "Libra", "Moon": "Scorpio", "Mars": "Cancer", "Mercury": "Pisces",
    "Jupiter": "Capricorn", "Venus": "Virgo", "Saturn": "Aries",
}

RASHI_ALIASES: Dict[str, str] = {
    "Mesha": "Aries", "Vrishabha": "Taurus", "Mithuna": "Gemini", "Karka": "Cancer",
    "Simha": "Leo", "Kanya": "Virgo", "Tula": "Libra", "Vrishchika": "Scorpio",
    "Dhanu": "Sagittarius", "Makara": "Capricorn", "Kumbha": "Aquarius", "Meena": "Pisces",
    "Aries": "Aries", "Taurus": "Taurus", "Gemini": "Gemini", "Cancer": "Cancer",
    "Leo": "Leo", "Virgo": "Virgo", "Libra": "Libra", "Scorpio": "Scorpio",
    "Sagittarius": "Sagittarius", "Capricorn": "Capricorn", "Aquarius": "Aquarius", "Pisces": "Pisces",
}

DIGNITY_NOT_ASSIGNED = "not_assigned"
DIGNITY_OWN = "own_sign"
DIGNITY_EXALTED = "exalted"
DIGNITY_DEBILITATED = "debilitated"
DIGNITY_NEUTRAL = "neutral"


def normalize_rashi(rashi: Optional[str]) -> Optional[str]:
    if not rashi:
        return None
    return RASHI_ALIASES.get(rashi.strip())


def dignity(planet: Optional[str], rashi: Optional[str]) -> str:
    """Own sign first, then exaltation/debilitation. Nodes are not assigned."""
    if not planet or not rashi:
        return DIGNITY_NEUTRAL
    if planet in NODES:
        return DIGNITY_NOT_ASSIGNED
    sign = normalize_rashi(rashi)
    if not sign:
        return DIGNITY_NEUTRAL
    if sign in RULERSHIP.get(planet, []):
        return DIGNITY_OWN
    if EXALTATION.get(planet) == sign:
        return DIGNITY_EXALTED
    if DEBILITATION.get(planet) == sign:
        return DIGNITY_DEBILITATED
    return DIGNITY_NEUTRAL


def planet_signification(planet: Optional[str]) -> Optional[str]:
    if not planet:
        return None
    return PLANET_SIGNIFICATIONS.get(planet)


def owns_sign(planet: str, rashi: str) -> bool:
    sign = normalize_rashi(rashi)
    return bool(sign and sign in RULERSHIP.get(planet, []))

PROVENANCE = STANDARD_JYOTISH_PROVENANCE
