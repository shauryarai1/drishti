"""Compositional interpretation: planet + house + channel domain + dignity.

No 108 hardcoded predictions and no fortune-cookie text. Deterministic language
is generated from the semantic tables. Output is conditional, never an event.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .channels import CHANNEL_DEFINITIONS, CHANNEL_FRAMES, PAST_LIFE_NOTE, channel_areas, channel_title
from .houses import HOUSE_CORE, condition_notes, house_conditions, house_meaning, watch_for
from .planets import (
    DIGNITY_DEBILITATED,
    DIGNITY_EXALTED,
    DIGNITY_NOT_ASSIGNED,
    DIGNITY_OWN,
    PLANET_CORE,
    dignity as compute_dignity,
    planet_signification,
)
from .provenance import STANDARD_JYOTISH_PROVENANCE

# Qualitative, public-safe dignity wording (the dignity term itself stays internal).
_PUBLIC_DIGNITY: Dict[str, str] = {
    DIGNITY_OWN: "This influence tends to express itself directly here.",
    DIGNITY_EXALTED: "This influence tends to express itself with particular ease here.",
    DIGNITY_DEBILITATED: "These qualities may need more deliberate development and management here.",
}
_INTERNAL_DIGNITY: Dict[str, str] = {
    DIGNITY_OWN: "The planet occupies its own sign, which supports direct expression.",
    DIGNITY_EXALTED: "The planet is exalted, which supports ease of expression.",
    DIGNITY_DEBILITATED: "The planet is debilitated, so these qualities may require conscious management.",
}


def _strength_notes(house: Optional[int], dignity: str) -> List[str]:
    notes: List[str] = []
    if dignity == DIGNITY_OWN:
        notes.append("This influence tends to express itself directly and supportively.")
    elif dignity == DIGNITY_EXALTED:
        notes.append("This influence tends to express itself with particular ease.")
    conditions = house_conditions(house)
    if "upachaya" in conditions:
        notes.append("This area develops gradually through sustained effort.")
    if "kendra" in conditions or "trikona" in conditions:
        notes.append("This is comparatively supportive structural context.")
    return notes


def interpret_channel(
    channel: str,
    selected_planet: Optional[str],
    planet_house: Optional[int],
    planet_rashi: Optional[str],
    dignity: Optional[str] = None,
) -> Dict[str, Any]:
    """Interpret one Panchang channel. Returns structured, conditional language."""
    resolved = dignity or compute_dignity(selected_planet, planet_rashi)
    planet_text = PLANET_CORE.get(selected_planet or "") or planet_signification(selected_planet)
    house_text = HOUSE_CORE.get(planet_house or 0) or house_meaning(planet_house)

    frame = CHANNEL_FRAMES.get(channel)
    summary: Optional[str] = None

    if frame and planet_text and house_text:
        summary = frame.format(planet=planet_text, house=house_text)
    elif frame:
        summary = (
            f"{channel_title(channel)} could not be fully composed because the selected "
            "planet or its placement was not available in the chart."
        )

    public_summary = summary

    if summary:
        internal_extra = _INTERNAL_DIGNITY.get(resolved)
        if internal_extra:
            summary = f"{summary} {internal_extra}"
        public_extra = _PUBLIC_DIGNITY.get(resolved)
        if public_extra and public_summary:
            public_summary = f"{public_summary} {public_extra}"

    watch = watch_for(planet_house)
    if resolved == DIGNITY_DEBILITATED:
        watch = watch + ["qualities that need patient, deliberate development"]

    guidance: List[str] = []
    definition_guidance = CHANNEL_DEFINITIONS.get(channel, {}).get("guidance")
    if definition_guidance:
        guidance.append(str(definition_guidance))
    guidance.extend(condition_notes(planet_house))
    if channel == "nakshatra":
        guidance.append(PAST_LIFE_NOTE)

    return {
        "channel": channel,
        "title": channel_title(channel),
        "domain": channel_title(channel),
        "areas": channel_areas(channel),
        "selected_planet": selected_planet,
        "planet_house": planet_house,
        "planet_rashi": planet_rashi,
        "dignity": resolved,
        "summary": summary,
        "public_summary": public_summary,
        "strengths": _strength_notes(planet_house, resolved),
        "watch_for": watch,
        "guidance": guidance or [],
        "provenance": dict(STANDARD_JYOTISH_PROVENANCE),
        "lifespan_or_medical_use": "excluded",
    }


def interpret_five_channels(
    lords: Dict[str, Optional[str]],
    placements: Dict[str, Optional[Dict[str, Any]]],
) -> Dict[str, Any]:
    """Interpret all five channels from five selected planets and D1 placements."""
    result: Dict[str, Any] = {}
    for channel in ("vaar", "tithi", "karana", "nakshatra", "yoga"):
        planet = lords.get(channel)
        placement = placements.get(planet) if planet else None
        result[channel] = interpret_channel(
            channel=channel,
            selected_planet=planet,
            planet_house=(placement or {}).get("house"),
            planet_rashi=(placement or {}).get("rashi"),
        )
    return result
