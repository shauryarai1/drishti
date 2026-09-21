"""Lord selectors with spelling normalization at the engine boundary."""

from __future__ import annotations

from typing import Dict, Optional

from .mappings import (
    KARANA_LORDS,
    NAKSHATRA_LORDS,
    TITHI_LORDS,
    VAAR_LORDS,
    YOGA_LORDS,
)

# Spelling variants seen in real Panchang sources -> canonical KAVACH spelling.
KARANA_ALIASES: Dict[str, str] = {
    "garaja": "Garaja", "gara": "Garaja", "garaga": "Garaja",
    "vanija": "Vanija", "vanij": "Vanija",
    "vishti": "Vishti", "bhadra": "Vishti", "visti": "Vishti",
    "shakuni": "Shakuni", "sakuni": "Shakuni",
    "chatushpada": "Chatushpada", "catushpada": "Chatushpada", "chatuspada": "Chatushpada",
    "naga": "Naga", "nag": "Naga",
    "kimstughna": "Kimstughna", "kintughna": "Kimstughna", "kimstugna": "Kimstughna",
    "bava": "Bava", "balava": "Balava", "kaulava": "Kaulava", "taitila": "Taitila",
}

NAKSHATRA_ALIASES: Dict[str, str] = {
    "ashvini": "Ashvini", "ashwini": "Ashvini",
    "bharani": "Bharani", "krittika": "Krittika", "krttika": "Krittika",
    "rohini": "Rohini", "mrigashira": "Mrigashira", "mrigasira": "Mrigashira",
    "ardra": "Ardra", "punarvasu": "Punarvasu", "pushya": "Pushya",
    "ashlesha": "Ashlesha", "aslesha": "Ashlesha", "magha": "Magha",
    "purva phalguni": "Purva Phalguni", "uttara phalguni": "Uttara Phalguni",
    "hasta": "Hasta", "chitra": "Chitra", "swati": "Swati",
    "vishakha": "Vishakha", "visakha": "Vishakha", "anuradha": "Anuradha",
    "jyeshtha": "Jyeshtha", "jyestha": "Jyeshtha", "mula": "Mula",
    "purva ashadha": "Purva Ashadha", "uttara ashadha": "Uttara Ashadha",
    "shravana": "Shravana", "sravana": "Shravana",
    "dhanishta": "Dhanishta", "dhanistha": "Dhanishta",
    "shatabhisha": "Shatabhisha", "satabhisha": "Shatabhisha",
    "purva bhadrapada": "Purva Bhadrapada", "purvabhadrapada": "Purva Bhadrapada",
    "uttara bhadrapada": "Uttara Bhadrapada", "uttarabhadrapada": "Uttara Bhadrapada",
    "revati": "Revati",
}

YOGA_ALIASES: Dict[str, str] = {
    "vishkambha": "Vishkumbha", "vishkumbha": "Vishkumbha", "viskambha": "Vishkumbha",
    "priti": "Priti", "preeti": "Priti", "ayushman": "Ayushman", "ayushmana": "Ayushman",
    "saubhagya": "Saubhagya", "shobhana": "Shobhana", "sobhana": "Shobhana",
    "atiganda": "Atiganda", "sukarma": "Sukarma", "sukarman": "Sukarma",
    "dhriti": "Dhriti", "shoola": "Shoola", "sula": "Shoola", "ganda": "Ganda",
    "vriddhi": "Vriddhi", "dhruva": "Dhruva", "vyaghata": "Vyaghata",
    "harshana": "Harshana", "harsana": "Harshana", "vajra": "Vajra",
    "siddhi": "Siddhi", "vyatipata": "Vyatipata", "variyana": "Variyana",
    "variyan": "Variyana", "parigha": "Parigha", "shiva": "Shiva", "siddha": "Siddha",
    "sadhya": "Sadhya", "shubha": "Shubha", "shukla": "Shukla",
    "brahma": "Brahma", "indra": "Indra", "vaidhriti": "Vaidhriti",
}


def _key(value: str) -> str:
    return " ".join((value or "").strip().lower().split())


def normalize(family: str, value: str) -> str:
    lowered = _key(value)
    if family == "karana":
        return KARANA_ALIASES.get(lowered, value)
    if family == "nakshatra":
        return NAKSHATRA_ALIASES.get(lowered, value)
    if family == "yoga":
        return YOGA_ALIASES.get(lowered, value)
    return value


def vara_lord(weekday_index: int) -> str:
    return VAAR_LORDS[weekday_index]


def tithi_lord(tithi_index: int) -> str:
    number = (tithi_index % 15) + 1
    return TITHI_LORDS[number]


def karana_lord(name: str) -> Optional[str]:
    return KARANA_LORDS.get(normalize("karana", name))


def nakshatra_lord(name: str) -> Optional[str]:
    canonical = normalize("nakshatra", name)
    for lord, names in NAKSHATRA_LORDS.items():  # type: ignore[union-attr]
        if canonical in names:  # type: ignore[operator]
            return lord
    return None


def yoga_lord(index: int, name: str | None = None) -> Optional[str]:
    if 0 <= index < 27:
        return YOGA_LORDS.get(index + 1)
    if name:
        canonical = normalize("yoga", name)
        from .mappings import YOGA_LORDS as BY_INDEX  # local import to avoid cycles
        order = [
            "Vishkumbha","Priti","Ayushman","Saubhagya","Shobhana","Atiganda","Sukarma",
            "Dhriti","Shoola","Ganda","Vriddhi","Dhruva","Vyaghata","Harshana","Vajra",
            "Siddhi","Vyatipata","Variyana","Parigha","Shiva","Siddha","Sadhya","Shubha",
            "Shukla","Brahma","Indra","Vaidhriti",
        ]
        if canonical in order:
            return BY_INDEX[order.index(canonical) + 1]
    return None
