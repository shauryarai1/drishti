"""Aggregate PRIVATE Kundli analysis payload from existing chart data."""

from __future__ import annotations

from typing import Any, Dict, List

from .aspects import standard_aspects
from .bnn import chart_connections
from .classifications import (
    dignity_distribution,
    element_distribution,
    modality_distribution,
    moon_chart,
    purushartha_distribution,
    same_sign_conjunctions,
)
from .dispositor import chains_for_all, mala_shree
from .karakas import atmakaraka, badhaka, lagna_summary, maraka, yogakaraka
from .signs import house_lord, house_sign
from .strength import strength_evidence


def _placements(planets: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {planet["planet"]: {"rashi": planet["rashi"], "house": planet["house"],
                               "longitude": planet.get("longitude")}
            for planet in planets}


def build_analysis(chart: Dict[str, Any], sun_longitude: float | None = None) -> Dict[str, Any]:
    """chart = the /api/kundli chart block (ascendant, houses, planets)."""
    planets = chart.get("planets") or []
    placements = _placements(planets)
    lagna_sign = str((chart.get("ascendant") or {}).get("rashi") or "Aries")
    longitudes = {planet: float(data["longitude"]) for planet, data in placements.items()
                  if data.get("longitude") is not None}
    retrograde = [planet["planet"] for planet in planets if planet.get("motion") == "Retrograde"]

    house_by_planet = {planet: int(data["house"]) for planet, data in placements.items() if data.get("house")}
    sun_long = sun_longitude if sun_longitude is not None else longitudes.get("Sun")

    return {
        "lagna": {
            **lagna_summary(lagna_sign),
            "lagneshRashi": placements.get(house_lord(lagna_sign, 1), {}).get("rashi"),
            "lagneshHouse": placements.get(house_lord(lagna_sign, 1), {}).get("house"),
        },
        "atmakaraka": atmakaraka(longitudes),
        "yogakaraka": yogakaraka(lagna_sign),
        "maraka": maraka(lagna_sign),
        "badhaka": badhaka(lagna_sign),
        "houseLords": {house: {"sign": house_sign(lagna_sign, house),
                               "lord": house_lord(lagna_sign, house)} for house in range(1, 13)},
        "dignity": dignity_distribution(placements),
        "conjunctions": same_sign_conjunctions(placements, longitudes, orb=None),
        "bnnConnections": chart_connections(placements, retrograde),
        "standardAspects": standard_aspects(house_by_planet),
        "strength": strength_evidence(placements, retrograde,
                                      {"Sun": sun_long} if sun_long is not None else None,
                                      longitudes),
        "dispositorChains": chains_for_all(placements),
        "malaShree": mala_shree(placements),
        "modalities": modality_distribution(placements),
        "elements": element_distribution(placements),
        "purushartha": purushartha_distribution(placements),
        "moonChart": moon_chart(placements),
        "bhavaChalit": None,
        "bhavaChalitStatus": "DEFERRED_NO_APPROVED_CUSP_METHOD",
    }
