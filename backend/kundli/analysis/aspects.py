"""Standard Graha Drishti (owner-specified). Separate from BNN connections.

Sun/Moon/Mercury/Venus: 7
Mars: 4, 7, 8
Jupiter: 5, 7, 9
Saturn: 3, 7, 10

No separate standard Rahu/Ketu aspect rule is implemented.
"""

from __future__ import annotations

from typing import Any, Dict, List

DRISHTI: Dict[str, tuple] = {
    "Sun": (7,),
    "Moon": (7,),
    "Mercury": (7,),
    "Venus": (7,),
    "Mars": (4, 7, 8),
    "Jupiter": (5, 7, 9),
    "Saturn": (3, 7, 10),
}


def target_houses(source_house: int, offsets: tuple) -> List[int]:
    return [((source_house - 1 + offset - 1) % 12) + 1 for offset in offsets]


def standard_aspects(house_by_planet: Dict[str, int]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for planet, house in house_by_planet.items():
        offsets = DRISHTI.get(planet)
        if not offsets:
            continue
        rows.append({
            "planet": planet,
            "fromHouse": house,
            "aspects": target_houses(house, offsets),
            "offsets": list(offsets),
        })
    return rows
