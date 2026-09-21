"""Panchang natal significator engine.

Selects five significator planets from the native's BIRTH Panchang and locates
each one in the existing natal chart.

It does NOT judge planet condition and produces no predictions yet.
"""

from __future__ import annotations

from datetime import datetime, time
from typing import Any, Dict, Optional
from zoneinfo import ZoneInfo

from calculator import generate_chart
from models import BirthData
from panchang import astronomy as pastro
from panchang.constants import NAKSHATRA_NAMES, TITHI_NAMES, VARA_ENGLISH, YOGA_NAMES
from panchang.engine import (
    KARANA_UNIT,
    NAKSHATRA_UNIT,
    TITHI_UNIT,
    YOGA_UNIT,
    _element_block,
    _karana_sequence,
    karana_name,
)

from . import selectors
from .mappings import LIMB_PURPOSES, MAPPING_PROVENANCE
from .models import PanchangLimb


def _birth_panchang(moment: datetime, latitude: float, longitude: float) -> Dict[str, Any]:
    """Birth-moment Panchang limbs (not sunrise-rounded)."""
    tz = moment.tzinfo
    jd = pastro.to_jd(moment)
    tithi = _element_block(pastro.moon_sun_elongation, TITHI_UNIT, TITHI_NAMES, jd, tz)
    nakshatra = _element_block(pastro.moon_longitude, NAKSHATRA_UNIT, NAKSHATRA_NAMES, jd, tz)
    yoga = _element_block(pastro.sun_moon_sum, YOGA_UNIT, YOGA_NAMES, jd, tz)
    karana_index = int(pastro.moon_sun_elongation(jd) // KARANA_UNIT) % 60
    paksha = "Shukla" if tithi["index"] < 15 else "Krishna"
    return {
        "reference": moment.isoformat(),
        "weekday_index": moment.weekday(),
        "weekday": VARA_ENGLISH[moment.weekday()],
        "tithi": {**tithi, "paksha": paksha, "number_in_paksha": (tithi["index"] % 15) + 1},
        "karana": {"current": karana_name(karana_index), "index": karana_index},
        "nakshatra": nakshatra,
        "yoga": yoga,
    }


def _natal_index(birth: BirthData) -> Dict[str, Dict[str, Any]]:
    """Natal placements from the EXISTING KAVACH chart calculator."""
    chart = generate_chart(birth)
    placements: Dict[str, Dict[str, Any]] = {}
    for planet in (chart.planets or []):
        placements[planet.name] = {
            "rashi": planet.sign,
            "house": planet.house,
            "longitude": planet.longitude,
            "degree_in_sign": planet.degree,
        }
    return placements


def compute_panchang_natal_significators(
    birth_date: str,
    birth_time: str,
    latitude: float,
    longitude: float,
    timezone: str = "Asia/Kolkata",
    place: str = "",
) -> Dict[str, Any]:
    tz = ZoneInfo(timezone)
    hour, minute = (int(part) for part in birth_time.split(":")[:2])
    moment = datetime.combine(
        datetime.fromisoformat(birth_date).date(), time(hour, minute), tzinfo=tz
    )

    birth = BirthData(
        date=birth_date,
        time=birth_time,
        place=place or "Unknown",
        latitude=latitude,
        longitude=longitude,
    )

    panchang = _birth_panchang(moment, latitude, longitude)
    natal = _natal_index(birth)

    def placement(lord: Optional[str]) -> Optional[Dict[str, Any]]:
        if not lord:
            return None
        found = natal.get(lord)
        return {"planet": lord, **found} if found else {"planet": lord, "missing_in_chart": True}

    channels = {
        "vaar": PanchangLimb(
            limb="vaar",
            value=panchang["weekday"],
            lord=selectors.vara_lord(panchang["weekday_index"]),
            purpose=LIMB_PURPOSES["vaar"],
            context={"weekday_index": panchang["weekday_index"]},
        ),
        "tithi": PanchangLimb(
            limb="tithi",
            value=panchang["tithi"]["name"],
            lord=selectors.tithi_lord(panchang["tithi"]["index"]),
            purpose=LIMB_PURPOSES["tithi"],
            context={
                "paksha": panchang["tithi"]["paksha"],
                "number_in_paksha": panchang["tithi"]["number_in_paksha"],
            },
        ),
        "karana": PanchangLimb(
            limb="karana",
            value=panchang["karana"]["current"],
            lord=selectors.karana_lord(panchang["karana"]["current"]) or "",
            purpose=LIMB_PURPOSES["karana"],
            context={},
        ),
        "nakshatra": PanchangLimb(
            limb="nakshatra",
            value=panchang["nakshatra"]["name"],
            lord=selectors.nakshatra_lord(panchang["nakshatra"]["name"]) or "",
            purpose=LIMB_PURPOSES["nakshatra"],
            context={"pada": panchang["nakshatra"].get("pada")},
        ),
        "yoga": PanchangLimb(
            limb="yoga",
            value=panchang["yoga"]["name"],
            lord=selectors.yoga_lord(panchang["yoga"]["index"], panchang["yoga"]["name"]) or "",
            purpose=LIMB_PURPOSES["yoga"],
            context={},
        ),
    }

    for channel in channels.values():
        channel.natal_placement = placement(channel.lord)

    return {
        "engine": "panchang_natal_significators",
        "status": "significators_only_no_interpretation",
        "provenance": MAPPING_PROVENANCE,
        "birth_panchang": panchang,
        "channels": {name: channel.to_dict() for name, channel in channels.items()},
        "notes": [
            "Each limb selects a significator planet for its own life area; the same planet may be selected by several limbs and those channels are kept separate.",
            "Planet condition judging rules are not yet supplied; no interpretation is produced.",
            "Lifespan, death and medical conclusions are excluded.",
        ],
    }
