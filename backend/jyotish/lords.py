"""Five-lord resolution for a Panchang moment.

Uses the astrologer's APPROVED tables (single authoritative source: the
System A mappings module, which is the KAVACH rulebook). The same tables drive
System A (birth moment) and System B (question moment).
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from panchang.constants import NAKSHATRA_NAMES, YOGA_NAMES
from kavach_core.mappings import (
    KARANA_LORDS,
    NAKSHATRA_LORDS,
    TITHI_LORDS,
    VAAR_LORDS,
    YOGA_LORDS,
)
from kavach_core.mappings import MAPPING_PROVENANCE  # noqa: F401

CHANNELS = ("vaar", "tithi", "karana", "nakshatra", "yoga")

_NAKSHATRA_BY_NAME = {
    name: lord for lord, names in NAKSHATRA_LORDS.items() for name in names
}

_KARANA_ALIASES = {
    "Gara": "Garaja", "Vanijaya": "Vanija", "Bhadra": "Bhadra",
    "Vishti": "Vishti", "Chatushpada": "Chatushpada", "Naga": "Naga",
}


def _karana_lord(name: Optional[str]) -> Optional[str]:
    if not name:
        return None
    if name in KARANA_LORDS:
        return KARANA_LORDS[name]
    alias = _KARANA_ALIASES.get(name)
    if alias and alias in KARANA_LORDS:
        return KARANA_LORDS[alias]
    prefix = name[:3].lower()
    for key, lord in KARANA_LORDS.items():
        if key[:3].lower() == prefix:
            return lord
    return None


def _nakshatra_lord(name: Optional[str]) -> Optional[str]:
    if not name:
        return None
    return _NAKSHATRA_BY_NAME.get(name)


YOGA_NAME_LORDS: Dict[str, str] = {
    "Vishkumbha": "Ketu", "Priti": "Venus", "Ayushman": "Sun", "Saubhagya": "Moon",
    "Shobhana": "Mars", "Atiganda": "Rahu", "Sukarma": "Jupiter", "Dhriti": "Saturn",
    "Shoola": "Mercury", "Ganda": "Ketu", "Vriddhi": "Venus", "Dhruva": "Sun",
    "Vyaghata": "Moon", "Harshana": "Mars", "Vajra": "Rahu", "Siddhi": "Jupiter",
    "Vyatipata": "Saturn", "Variyan": "Mercury", "Parigha": "Ketu", "Shiva": "Venus",
    "Siddha": "Sun", "Sadhya": "Moon", "Shubha": "Mars", "Shukla": "Rahu",
    "Brahma": "Jupiter", "Indra": "Saturn", "Vaidhriti": "Mercury",
}


def _yoga_lord(index: Optional[int], name: Optional[str]) -> Optional[str]:
    # Name is authoritative: the astrologer's table is keyed to the classic order.
    if name and name in YOGA_NAME_LORDS:
        return YOGA_NAME_LORDS[name]
    if index is not None:
        if 1 <= index <= 27:
            return YOGA_LORDS.get(index)
        wrapped = (index - 1) % 27 + 1 if index > 27 else ((index - 1) % 27) + 1
        if wrapped in YOGA_LORDS:
            return YOGA_LORDS[wrapped]
    if name and name in YOGA_NAMES:
        return YOGA_LORDS.get(YOGA_NAMES.index(name) + 1)
    return None


def resolve_five_lords(panchang: Dict[str, Any]) -> Dict[str, Optional[str]]:
    """Resolve the five KAVACH channel lords from a moment/birth Panchang dict."""
    vara = panchang.get("vara", {}) or {}
    tithi = panchang.get("tithi", {}) or {}
    if not vara and "weekday_index" in panchang:
        vara = {"index": panchang.get("weekday_index"), "english": panchang.get("weekday")}
    karana = panchang.get("karana", {}) or {}
    nakshatra = panchang.get("nakshatra", {}) or {}
    yoga = panchang.get("yoga", {}) or {}

    weekday_index = vara.get("index")
    if weekday_index is None and vara.get("english"):
        names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        if vara["english"] in names:
            weekday_index = names.index(vara["english"])

    tithi_index = tithi.get("index")
    number_in_paksha = tithi.get("number_in_paksha")
    if number_in_paksha is None and tithi_index is not None:
        number_in_paksha = (tithi_index % 15) + 1

    return {
        "vaar": VAAR_LORDS.get(weekday_index) if weekday_index is not None else None,
        "tithi": TITHI_LORDS.get(number_in_paksha) if number_in_paksha else None,
        "karana": _karana_lord(karana.get("current") or karana.get("name")),
        "nakshatra": _nakshatra_lord(nakshatra.get("name")),
        "yoga": _yoga_lord(yoga.get("index"), yoga.get("name")),
    }


def provenance_for(channel: str) -> Dict[str, str]:
    return dict(MAPPING_PROVENANCE)
