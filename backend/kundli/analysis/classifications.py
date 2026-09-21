"""Supporting technical classifications: modality, elements, purushartha,
same-sign conjunctions, dignity and the Moon chart transform."""

from __future__ import annotations

from typing import Any, Dict, List

from jyotish.planets import dignity as dignity_of

from .signs import (
    DUAL,
    ELEMENTS,
    FIXED,
    MOVABLE,
    MODALITIES,
    PURUSHARTHA,
    RASHIS,
    group_members,
)


def modality_distribution(placements: Dict[str, Dict[str, Any]]) -> Dict[str, List[str]]:
    return {name: group_members(group, placements) for name, group in MODALITIES.items()}


def element_distribution(placements: Dict[str, Dict[str, Any]]) -> Dict[str, List[str]]:
    return {name: group_members(group, placements) for name, group in ELEMENTS.items()}


def purushartha_distribution(placements: Dict[str, Dict[str, Any]]) -> Dict[str, List[str]]:
    result: Dict[str, List[str]] = {}
    for name, houses in PURUSHARTHA.items():
        result[name] = sorted(planet for planet, data in placements.items()
                              if data.get("house") in houses)
    return result


def dignity_distribution(placements: Dict[str, Dict[str, Any]]) -> Dict[str, List[str]]:
    buckets: Dict[str, List[str]] = {"exalted": [], "own_sign": [], "debilitated": [], "other": []}
    for planet, data in placements.items():
        level = dignity_of(planet, str(data.get("rashi")))
        key = level if level in ("exalted", "own_sign", "debilitated") else "other"
        buckets[key].append(planet)
    return buckets


def same_sign_conjunctions(placements: Dict[str, Dict[str, Any]],
                           longitudes: Dict[str, float] | None = None,
                           orb: float | None = None) -> List[Dict[str, Any]]:
    """Same-sign conjunction (default). Orb-based pairs are labelled separately."""
    by_sign: Dict[str, List[str]] = {}
    for planet, data in placements.items():
        by_sign.setdefault(str(data.get("rashi")), []).append(planet)

    rows: List[Dict[str, Any]] = []
    for rashi, planets in by_sign.items():
        if len(planets) < 2:
            continue
        for index in range(len(planets)):
            for other in range(index + 1, len(planets)):
                entry: Dict[str, Any] = {
                    "type": "same_sign",
                    "planets": [planets[index], planets[other]],
                    "rashi": rashi,
                }
                if longitudes is not None:
                    first = longitudes.get(planets[index])
                    second = longitudes.get(planets[other])
                    if first is not None and second is not None:
                        separation = abs(first - second)
                        separation = min(separation, 360 - separation)
                        entry["separation"] = round(separation, 4)
                        if orb is not None:
                            entry["withinOrb"] = separation <= orb
                rows.append(entry)
    return rows


def moon_chart(placements: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Moon's rashi becomes house 1; planets keep their natal rashi/longitude."""
    moon = placements.get("Moon")
    if not moon:
        return {"lagnaSign": None, "placements": {}}
    moon_sign = str(moon["rashi"])
    start = RASHIS.index(moon_sign)
    transformed: Dict[str, Dict[str, Any]] = {}
    for planet, data in placements.items():
        sign = str(data["rashi"])
        house = ((RASHIS.index(sign) - start) % 12) + 1
        transformed[planet] = {**data, "house": house}
    return {"lagnaSign": moon_sign, "placements": transformed}
