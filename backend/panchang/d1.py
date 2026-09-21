"""Sunrise D1 (Rashi) chart and planetary positions.

Everything here is computed for the EXACT local sunrise of the selected
Panchang day — not midnight, not noon, not the current time — using the same
Lahiri/Chitrapaksha sidereal conventions as the rest of the engine.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List

import swisseph as swe

from . import astronomy as astro
from .constants import (
    CLASSICAL_GRAHAS,
    NAKSHATRA_LORDS,
    NAKSHATRA_NAMES,
    OUTER_GRAHAS,
    PLANET_SYMBOLS,
    RASHI_ENGLISH,
    RASHI_NAMES,
)

NAKSHATRA_SIZE = 360.0 / 27.0
PADA_SIZE = NAKSHATRA_SIZE / 4

_BODY = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mars": swe.MARS,
    "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS,
    "Saturn": swe.SATURN,
    "Rahu": swe.MEAN_NODE,
    "Uranus": swe.URANUS,
    "Neptune": swe.NEPTUNE,
    "Pluto": swe.PLUTO,
}


def _sidereal(jd: float, body: int):
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    # FLG_SPEED is required: without it Swiss Ephemeris returns speed 0.0 and the
    # retrograde flag below would always be False. It does not alter longitude.
    values = swe.calc_ut(jd, body, swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED)[0]
    longitude = float(values[0][0] if isinstance(values[0], tuple) else values[0]) % 360.0
    speed = float(values[3][0] if isinstance(values[3], tuple) else values[3])
    return longitude, speed


def _ascendant(jd: float, latitude: float, longitude: float) -> float:
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    cusps, ascmc = swe.houses(jd, latitude, longitude, b"P")
    tropical = float(ascmc[0][0] if isinstance(ascmc[0], tuple) else ascmc[0])
    ayanamsa = float(swe.get_ayanamsa_ut(jd))
    return (tropical - ayanamsa) % 360.0


def _describe(longitude: float) -> Dict[str, object]:
    sign_index = int(longitude // 30.0) % 12
    degree_in_sign = longitude - sign_index * 30.0
    nak_index = int(longitude // NAKSHATRA_SIZE) % 27
    pada = int((longitude % NAKSHATRA_SIZE) // PADA_SIZE) + 1
    return {
        "sign_index": sign_index,
        "sign": RASHI_NAMES[sign_index],
        "sign_english": RASHI_ENGLISH[sign_index],
        "degree_in_sign": round(degree_in_sign, 4),
        "nakshatra": NAKSHATRA_NAMES[nak_index],
        "nakshatra_index": nak_index,
        "nakshatra_lord": NAKSHATRA_LORDS[nak_index],
        "pada": pada,
    }


def compute_d1(sunrise: datetime, latitude: float, longitude: float) -> Dict[str, object]:
    jd = astro.to_jd(sunrise)

    lagna_longitude = _ascendant(jd, latitude, longitude)
    lagna_sign = int(lagna_longitude // 30.0) % 12

    def house_of(sign_index: int) -> int:
        # Whole-sign houses counted from the actual sunrise Lagna.
        return ((sign_index - lagna_sign) % 12) + 1

    positions: List[Dict[str, object]] = []
    for name in CLASSICAL_GRAHAS + OUTER_GRAHAS:
        if name == "Ketu":
            rahu_longitude, _ = _sidereal(jd, swe.MEAN_NODE)
            body_longitude = (rahu_longitude + 180.0) % 360.0
            retrograde = True
        else:
            body_longitude, speed = _sidereal(jd, _BODY[name])
            retrograde = speed < 0
        described = _describe(body_longitude)
        described.update(
            {
                "planet": name,
                "symbol": PLANET_SYMBOLS[name],
                "longitude": round(body_longitude, 6),
                "house": house_of(described["sign_index"]),
                "retrograde": bool(retrograde),
                "classical": name in CLASSICAL_GRAHAS,
            }
        )
        positions.append(described)

    lagna = _describe(lagna_longitude)
    lagna.update(
        {
            "planet": "Lagna",
            "symbol": "Asc",
            "longitude": round(lagna_longitude, 6),
            "house": 1,
            "retrograde": False,
            "classical": True,
        }
    )

    return {
        "instant": sunrise.isoformat(),
        "lagna": lagna,
        "positions": positions,
        "houses": [
            {
                "house": index + 1,
                "sign_index": (lagna_sign + index) % 12,
                "sign": RASHI_NAMES[(lagna_sign + index) % 12],
                "sign_english": RASHI_ENGLISH[(lagna_sign + index) % 12],
                "planets": [
                    p["planet"] for p in positions if p["house"] == index + 1
                ],
            }
            for index in range(12)
        ],
    }
