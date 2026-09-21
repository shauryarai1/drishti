"""PRIVATE Navtara engine - deterministic relative counting.

Janma Nakshatra is position 1 and counting continues inclusively through the
27 canonical Nakshatras, wrapping Revati -> Ashwini.

No planets, no aspects, no houses, no AI: classification only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .constants import (
    CAUTION_TARAS,
    NAKSHATRAS,
    NAKSHATRA_COUNT,
    SPECIAL_ROLES,
    TARA_CYCLE,
    TARA_SEQUENCE,
    canonical_nakshatra,
    nakshatra_index,
)
from .meanings import SPECIAL_MEANINGS, TARA_MEANINGS, tara_meaning


@dataclass(frozen=True)
class NavtaraPosition:
    position: int                    # 1..27 from the Janma Nakshatra
    nakshatra: str                   # canonical transit/janma Nakshatra
    tara_number: int                 # 1..9
    tara: str                        # Janma .. AtiMitra
    special_roles: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "position": self.position,
            "nakshatra": self.nakshatra,
            "taraNumber": self.tara_number,
            "tara": self.tara,
            "specialRoles": list(self.special_roles),
        }


@dataclass(frozen=True)
class NavtaraProfile:
    janma_nakshatra: str
    positions: List[NavtaraPosition]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "janmaNakshatra": self.janma_nakshatra,
            "positions": [item.to_dict() for item in self.positions],
        }

    def by_nakshatra(self) -> Dict[str, NavtaraPosition]:
        return {item.nakshatra: item for item in self.positions}

    def by_position(self) -> Dict[int, NavtaraPosition]:
        return {item.position: item for item in self.positions}


def relative_nakshatra_position(janma_nakshatra: str, target_nakshatra: str) -> int:
    """Inclusive forward count from the Janma Nakshatra (1..27)."""
    janma = nakshatra_index(janma_nakshatra)
    target = nakshatra_index(target_nakshatra)
    return ((target - janma) % NAKSHATRA_COUNT) + 1


def get_tara_from_position(position: int) -> str:
    if not 1 <= position <= NAKSHATRA_COUNT:
        raise ValueError(f"position out of range: {position}")
    return TARA_SEQUENCE[(position - 1) % TARA_CYCLE]


def get_tara_number(position: int) -> int:
    return ((position - 1) % TARA_CYCLE) + 1


def get_special_roles(position: int) -> List[str]:
    role = SPECIAL_ROLES.get(position)
    return [role] if role else []


def get_navtara(janma_nakshatra: str, target_nakshatra: str) -> Dict[str, Any]:
    """Full classification for one target Nakshatra, two independent layers."""
    position = relative_nakshatra_position(janma_nakshatra, target_nakshatra)
    tara = get_tara_from_position(position)
    roles = get_special_roles(position)
    return {
        "janmaNakshatra": canonical_nakshatra(janma_nakshatra),
        "targetNakshatra": canonical_nakshatra(target_nakshatra),
        "position": position,
        "taraNumber": get_tara_number(position),
        "tara": tara,
        "isCaution": tara in CAUTION_TARAS,
        "nature": tara_meaning(tara).get("nature"),
        "specialRoles": roles,
    }


def build_navtara_profile(janma_nakshatra: str) -> NavtaraProfile:
    """All 27 relative positions for a native's Janma Nakshatra."""
    janma = canonical_nakshatra(janma_nakshatra)
    start = NAKSHATRAS.index(janma) if janma in NAKSHATRAS else nakshatra_index(janma)
    positions: List[NavtaraPosition] = []
    for step in range(NAKSHATRA_COUNT):
        position = step + 1
        nakshatra = NAKSHATRAS[(start + step) % NAKSHATRA_COUNT]
        positions.append(NavtaraPosition(
            position=position,
            nakshatra=nakshatra,
            tara_number=get_tara_number(position),
            tara=get_tara_from_position(position),
            special_roles=get_special_roles(position),
        ))
    return NavtaraProfile(janma_nakshatra=janma, positions=positions)


def get_janma_nakshatra_from_birth_details(
    date: str, time: str, place: str, latitude: float, longitude: float
) -> Dict[str, Any]:
    """Natal Moon Nakshatra from the EXISTING KAVACH chart calculator."""
    from calculator import BirthData, generate_chart
    from kundli.nakshatra import nakshatra_of

    chart = generate_chart(BirthData(date=date, time=time, place=place or "Unknown",
                                     latitude=latitude, longitude=longitude))
    moon = next(planet for planet in chart.planets if planet.name == "Moon")
    info = nakshatra_of(moon.longitude)
    return {
        "nakshatra": canonical_nakshatra(str(info["name"])),
        "pada": info["pada"],
        "lord": info["lord"],
        "longitude": round(float(moon.longitude), 6),
    }


def get_meanings(tara: str) -> Dict[str, object]:
    return tara_meaning(tara)


def get_special_meanings(role: str) -> Dict[str, object]:
    return SPECIAL_MEANINGS.get(role, {})


def tara_is_caution(tara: str) -> bool:
    return tara in CAUTION_TARAS


def summarise_profile(profile: NavtaraProfile) -> Dict[str, Any]:
    """PRIVATE summary counts - never exposed through a public API."""
    counts: Dict[str, int] = {tara: 0 for tara in TARA_SEQUENCE}
    for item in profile.positions:
        counts[item.tara] += 1
    specials: Dict[str, int] = {}
    for item in profile.positions:
        for role in item.special_roles:
            specials[role] = specials.get(role, 0) + 1
    return {
        "janmaNakshatra": profile.janma_nakshatra,
        "taraCounts": counts,
        "specialPositions": dict(SPECIAL_ROLES),
        "specialCounts": specials,
    }


def classify_transit_nakshatra(janma_nakshatra: str, transit_nakshatra: str) -> Optional[Dict[str, Any]]:
    """Convenience wrapper used by a future premium forecast renderer."""
    return get_navtara(janma_nakshatra, transit_nakshatra)
