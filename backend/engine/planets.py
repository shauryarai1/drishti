"""
Swiss Ephemeris wrapper for sidereal planetary positions.

Returns sidereal longitudes in degrees [0, 360).
"""
from __future__ import annotations

import swisseph as swe

from config import PLANETS
from engine.ayanamsa import init_sidereal

init_sidereal()

_PLANET_INDEX = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mercury": swe.MERCURY,
    "Venus": swe.VENUS,
    "Mars": swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN,
    "Rahu": swe.MEAN_NODE,
    "Ketu": None,
}


def _normalize_longitude(value: float) -> float:
    return float(value) % 360.0


def calc_planet(jd: float, name: str) -> float:
    if name == "Ketu":
        rahu = swe.calc_ut(jd, swe.MEAN_NODE, swe.FLG_SIDEREAL)
        rahu_long = rahu[0]
        if isinstance(rahu_long, tuple):
            rahu_long = rahu_long[0]
        return _normalize_longitude(float(rahu_long) + 180.0)

    idx = _PLANET_INDEX[name]
    result = swe.calc_ut(jd, idx, swe.FLG_SIDEREAL)
    longitude = result[0]
    if isinstance(longitude, tuple):
        longitude = longitude[0]
    return _normalize_longitude(float(longitude))


def calc_all(jd: float) -> dict[str, float]:
    return {name: calc_planet(jd, name) for name in PLANETS}
