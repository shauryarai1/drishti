"""Number -> planet registry and planetary themes for KAVACH YES / NO.

The single, immutable source of the number/planet mapping for this feature.
Nothing else in the package may redefine it.

    1 = Sun      4 = Rahu     7 = Ketu
    2 = Moon     5 = Mercury  8 = Saturn
    3 = Jupiter  6 = Venus    9 = Mars
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Mapping, Tuple

# Centralized immutable registry (read-only mapping).
NUMBER_TO_PLANET: Mapping[int, str] = MappingProxyType({
    1: "Sun",
    2: "Moon",
    3: "Jupiter",
    4: "Rahu",
    5: "Mercury",
    6: "Venus",
    7: "Ketu",
    8: "Saturn",
    9: "Mars",
})

PLANET_NUMBERS: Mapping[str, int] = MappingProxyType(
    {planet: number for number, planet in NUMBER_TO_PLANET.items()}
)

# Concise interpretation primitives. These describe planetary character only;
# they never decide the FRIEND / ENEMY / NEUTRAL verdict.
PLANET_THEMES: Mapping[str, Tuple[str, ...]] = MappingProxyType({
    "Sun": ("authority", "confidence", "recognition", "leadership", "visibility"),
    "Moon": ("emotions", "comfort", "receptivity", "the mind", "changeability"),
    "Jupiter": ("growth", "wisdom", "expansion", "guidance", "opportunity"),
    "Rahu": ("ambition", "unconventional movement", "intensity", "amplification", "uncertainty"),
    "Mercury": ("communication", "intellect", "calculation", "adaptability", "trade"),
    "Venus": ("comfort", "attraction", "harmony", "value", "pleasure", "relationships"),
    "Ketu": ("detachment", "separation", "inward focus", "a non-material direction"),
    "Saturn": ("delay", "discipline", "responsibility", "patience", "stability", "endurance"),
    "Mars": ("action", "courage", "competition", "drive", "urgency"),
})


def planet_for_number(number: int) -> str:
    """Planet for a reduced number 1-9. Raises for anything outside the registry."""
    try:
        return NUMBER_TO_PLANET[int(number)]
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"{number!r} is not a planetary number (expected 1-9)") from exc


def themes_for(planet: str, limit: int = 3) -> Tuple[str, ...]:
    """First `limit` interpretation primitives for a planet."""
    return tuple(PLANET_THEMES.get(planet, ()))[:limit]
