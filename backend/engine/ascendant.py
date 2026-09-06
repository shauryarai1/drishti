"""
Ascendant calculation in sidereal longitude.

Uses Swiss Ephemeris houses() with Placidus flag only to obtain
the sidereal ascendant point. Placidus cusps are not used for
D1 whole-sign house assignment.
"""
from __future__ import annotations

import swisseph as swe

from engine.ayanamsa import init_sidereal

init_sidereal()


def calc(jd: float, latitude: float, longitude: float) -> float:
    cusps, ascmc = swe.houses(jd, latitude, longitude, b"P")
    asc = ascmc[0]
    if isinstance(asc, tuple):
        asc = asc[0]
    return float(asc) % 360.0
