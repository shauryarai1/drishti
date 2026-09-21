"""Combustion limits (owner-approved working values) and wrap-safe separation."""

from __future__ import annotations

from typing import Dict, Optional

# planet -> (direct limit, retrograde limit or None)
COMBUSTION_LIMITS: Dict[str, tuple] = {
    "Moon": (12.0, None),
    "Mars": (17.0, None),
    "Mercury": (14.0, 12.0),
    "Jupiter": (11.0, None),
    "Venus": (10.0, 8.0),
    "Saturn": (15.0, None),
}

# Rahu/Ketu deliberately excluded from normal combustion.
NODES_EXCLUDED = ("Rahu", "Ketu")


def angular_separation(first: float, second: float) -> float:
    """Shortest arc between two longitudes, safe across 0/360."""
    difference = abs((float(first) - float(second)) % 360.0)
    return min(difference, 360.0 - difference)


def limit_for(planet: str, retrograde: bool = False) -> Optional[float]:
    entry = COMBUSTION_LIMITS.get(planet)
    if not entry:
        return None
    direct, retro = entry
    return retro if (retrograde and retro is not None) else direct


def is_combust(planet: str, planet_longitude: float, sun_longitude: float,
               retrograde: bool = False) -> bool:
    """Combustion is a MODIFIER - a combust planet is not automatically weak."""
    limit = limit_for(planet, retrograde)
    if limit is None:
        return False
    return angular_separation(planet_longitude, sun_longitude) <= limit
