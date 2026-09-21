"""Life Summary engine: Panchang lord -> curated category reading.

Extremely simple by design:
    birth Panchang -> five limb lords -> curated lookup -> five sections.
No D1 house, no Graha-in-Bhava, no dignity, no keyword composition.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from jyotish.lords import resolve_five_lords

from .knowledge import LIFE_SUMMARY_INTERPRETATIONS
from .paragraphs import paragraph_for
from .prose import render

LIFE_SUMMARY_SECTIONS: List[Tuple[str, str, str]] = [
    ("personality", "Personality & Vitality", "vaar"),
    ("relationships", "Relationships & Prosperity", "tithi"),
    ("professional", "Career & Decisions", "karana"),
    ("subconscious", "Subconscious Mind & Habits", "nakshatra"),
    ("problems", "Challenges & Support", "yoga"),
]

PAST_LIFE_NOTE = (
    "According to this astrological tradition this is also read as past-habit "
    "tendencies; that is a traditional framing rather than an established fact."
)

READING_ERROR_MESSAGE = (
    "We could not calculate this reading right now. Please check the birth date, "
    "time and place, then try again."
)

PROVENANCE: Dict[str, str] = {
    "source_type": "standard_jyotish",
    "basis": "panchang_lord_nature",
}


def lookup(category: str, planet: str | None) -> Dict[str, Any]:
    table = LIFE_SUMMARY_INTERPRETATIONS.get(category, {})
    return table.get(planet or "") or {
        "summary": None, "strengths": [], "watch_for": [], "guidance": None,
    }


def section_body(category: str, planet: str | None, entry: Dict[str, Any]) -> str | None:
    """Finished curated prose where available; structured weaving otherwise."""
    body = paragraph_for(category, planet) or render(category, planet, entry)
    return body or None


def _birth_data(birth_date, birth_time, latitude, longitude, timezone_name, place) -> Dict[str, Any]:
    # Imported lazily to avoid a package-level circular import.
    from prediction.panchang_natal.engine import compute_panchang_natal_significators

    result = compute_panchang_natal_significators(
        birth_date=birth_date,
        birth_time=birth_time,
        latitude=latitude,
        longitude=longitude,
        timezone=timezone_name,
        place=place,
    )
    return result, resolve_five_lords(result.get("birth_panchang") or {})


def build_life_summary(
    birth_date: str,
    birth_time: str,
    latitude: float,
    longitude: float,
    timezone_name: str = "Asia/Kolkata",
    place: str = "",
) -> Dict[str, Any]:
    try:
        result, lords = _birth_data(
            birth_date, birth_time, latitude, longitude, timezone_name, place
        )
    except Exception:
        return {
            "status": "error",
            "engine": "life_summary",
            "calculated": False,
            "message": READING_ERROR_MESSAGE,
            "sections": [],
            "available_sections": 0,
            "total_sections": len(LIFE_SUMMARY_SECTIONS),
        }

    sections: List[Dict[str, Any]] = []
    for key, title, channel in LIFE_SUMMARY_SECTIONS:
        planet = lords.get(channel)
        entry = lookup(key, planet)
        body = section_body(key, planet, entry)
        sections.append(
            {
                "key": key,
                "title": title,
                "status": "available" if body else "unavailable",
                "body": body,
                "strengths": entry.get("strengths", []),
                "watch_for": entry.get("watch_for", []),
                "guidance": [entry["guidance"]] if entry.get("guidance") else [],
            }
        )

    return {
        "status": "ok",
        "engine": "life_summary",
        "calculated": True,
        "available_sections": sum(1 for s in sections if s["status"] == "available"),
        "total_sections": len(sections),
        "sections": sections,
        "note": (
            "Each section interprets the natural characteristics of the planet "
            "selected by the birth Panchang limb for that category."
        ),
        "_internal_engine_status": result.get("status"),
    }


def build_channel_interpretations(
    birth_date: str,
    birth_time: str,
    latitude: float,
    longitude: float,
    timezone_name: str = "Asia/Kolkata",
    place: str = "",
) -> Dict[str, Any]:
    """Audit view for the developer page. Not used to compose public text."""
    result, lords = _birth_data(
        birth_date, birth_time, latitude, longitude, timezone_name, place
    )

    placements: Dict[str, Dict[str, Any]] = {}
    for channel in (result.get("channels") or {}).values():
        placement = channel.get("natal_placement") or {}
        if placement.get("planet") and placement.get("house"):
            placements[placement["planet"]] = {
                "house": placement.get("house"),
                "rashi": placement.get("rashi"),
            }

    channels: Dict[str, Any] = {}
    for key, title, channel in LIFE_SUMMARY_SECTIONS:
        planet = lords.get(channel)
        entry = lookup(key, planet)
        placement = placements.get(planet or "", {})
        channels[channel] = {
            "channel": channel,
            "title": title,
            "planet": planet,
            "available": bool(entry.get("summary")),
            "public_text": section_body(key, planet, entry),
            "channel_interpretation": entry.get("summary"),
            "base_interpretation": entry.get("strengths", []),
            "strengths": entry.get("strengths", []),
            "watch_for": entry.get("watch_for", []),
            "guidance": [entry["guidance"]] if entry.get("guidance") else [],
            "assessment": "panchang_lord",
            "planet_house": placement.get("house"),
            "planet_rashi": placement.get("rashi"),
            "dignity": "not_used_in_life_summary",
            "uses_house_placement": False,
            "interpretation_basis": "panchang_lord_nature",
            "provenance": dict(PROVENANCE),
        }

    return {
        "engine_status": result.get("status"),
        "birth_panchang": result.get("birth_panchang"),
        "reference": result.get("birth_panchang", {}).get("reference"),
        "lords": lords,
        "placements": placements,
        "channels": channels,
        "system": "A",
        "moment": "birth_moment",
        "interpretation_basis": "panchang_lord_nature",
    }
