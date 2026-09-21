"""Shared Nakshatra derivation for KAVACH chart tools.

ONE pure path: sidereal longitude -> Nakshatra -> Pada -> Nakshatra lord.

Reuses the project's existing tables (panchang.constants.NAKSHATRA_NAMES and the
approved NAKSHATRA_LORDS mapping). The approved table follows the standard
Vimshottari cycle exactly, so the nakshatra ordinal is an authoritative fallback
whenever a name spelling is unfamiliar (e.g. Ashwini/Ashvini).
"""

from __future__ import annotations

from typing import Dict

from kavach_core.mappings import NAKSHATRA_LORDS
from panchang.constants import NAKSHATRA_NAMES

NAKSHATRA_SPAN = 360.0 / 27.0  # 13 degrees 20 minutes
PADA_SPAN = NAKSHATRA_SPAN / 4.0

# Standard Vimshottari lord cycle, in nakshatra order (1..27).
VIMSHOTTARI_CYCLE = ("Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu",
                     "Jupiter", "Saturn", "Mercury")


def _normalise(name: str) -> str:
    return "".join(character for character in (name or "").lower() if character.isalpha())


_LORD_BY_NAME: Dict[str, str] = {
    _normalise(name): lord for lord, names in NAKSHATRA_LORDS.items() for name in names
}


def lord_for_name(name: str) -> str:
    """Approved lord for a nakshatra name, spelling-agnostic ('' if unknown)."""
    return _LORD_BY_NAME.get(_normalise(name), "")


def nakshatra_of(longitude: float) -> Dict[str, object]:
    """Return nakshatra, pada, lord and progress for a sidereal longitude."""
    value = float(longitude) % 360.0
    index = int(value // NAKSHATRA_SPAN) % 27
    within = value - index * NAKSHATRA_SPAN
    name = NAKSHATRA_NAMES[index]
    return {
        "index": index + 1,
        "name": name,
        "pada": int(within // PADA_SPAN) + 1,
        "lord": lord_for_name(name) or VIMSHOTTARI_CYCLE[index % 9],
        "progress": round(within / NAKSHATRA_SPAN, 8),
    }
