"""Exact-moment Panchang + chart calculation.

ADDITIVE to the production Panchang package. The Panchang-day / Sunrise D1
behaviour used by /panchang is untouched; this module answers a different
question: "what is the Panchang/ chart state at this precise instant?"

Reuses the existing production astronomy functions and the existing D1 chart
builder — no duplicated Swiss Ephemeris logic.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict
from zoneinfo import ZoneInfo

from . import astronomy as astro
from .constants import NAKSHATRA_LORDS, NAKSHATRA_NAMES, RASHI_NAMES, TITHI_NAMES, VARA_ENGLISH, YOGA_NAMES
from .d1 import compute_d1
from .engine import (
    KARANA_UNIT,
    NAKSHATRA_UNIT,
    TITHI_UNIT,
    YOGA_UNIT,
    _element_block,
    karana_name,
)

NAKSHATRA_SIZE = 360.0 / 27.0
PADA_SIZE = NAKSHATRA_SIZE / 4


def calculate_panchang_moment(
    moment: datetime,
    latitude: float,
    longitude: float,
    timezone_name: str = "Asia/Kolkata",
    label: str = "",
) -> Dict[str, Any]:
    """Panchang + chart state at an exact, timezone-aware moment."""
    if moment.tzinfo is None:
        raise ValueError("moment must be timezone-aware")
    tz = ZoneInfo(timezone_name)
    local = moment.astimezone(tz)
    jd = astro.to_jd(local)

    tithi = _element_block(astro.moon_sun_elongation, TITHI_UNIT, TITHI_NAMES, jd, tz)
    nakshatra = _element_block(astro.moon_longitude, NAKSHATRA_UNIT, NAKSHATRA_NAMES, jd, tz)
    yoga = _element_block(astro.sun_moon_sum, YOGA_UNIT, YOGA_NAMES, jd, tz)
    karana_index = int(astro.moon_sun_elongation(jd) // KARANA_UNIT) % 60

    nakshatra_degree = astro.moon_longitude(jd) % NAKSHATRA_SIZE
    nakshatra["pada"] = int(nakshatra_degree // PADA_SIZE) + 1
    nakshatra["lord"] = NAKSHATRA_LORDS[nakshatra["index"]]

    moon_longitude = astro.moon_longitude(jd)
    moon_rashi_index = int(moon_longitude // 30.0) % 12

    chart = compute_d1(local, latitude, longitude)

    return {
        "engine": "panchang_moment",
        "timestamp": local.isoformat(),
        "timestamp_utc": local.astimezone(ZoneInfo("UTC")).isoformat(),
        "timezone": timezone_name,
        "location": {"label": label, "latitude": latitude, "longitude": longitude},
        "vara": {"index": local.weekday(), "english": VARA_ENGLISH[local.weekday()]},
        "tithi": {
            "name": tithi["name"],
            "index": tithi["index"],
            "number": (tithi["index"] % 15) + 1,
            "paksha": "Shukla" if tithi["index"] < 15 else "Krishna",
            "end": tithi.get("end"),
        },
        "karana": {"name": karana_name(karana_index), "index": karana_index},
        "nakshatra": {
            "name": nakshatra["name"],
            "index": nakshatra["index"],
            "pada": nakshatra["pada"],
            "lord": nakshatra["lord"],
            "end": nakshatra.get("end"),
        },
        "yoga": {"name": yoga["name"], "index": yoga["index"], "end": yoga.get("end")},
        "moon": {
            "rashi": RASHI_NAMES[moon_rashi_index],
            "rashi_index": moon_rashi_index,
            "longitude": round(moon_longitude, 6),
        },
        "chart": {
            "lagna": chart["lagna"],
            "positions": chart["positions"],
            "houses": chart["houses"],
            "reference": "question_moment",
        },
    }
