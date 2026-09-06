"""
Ayanamsa configuration and lookup.

Uses Lahiri / Chitrapaksha ayanamsa.
"""
from __future__ import annotations

import swisseph as swe

AYANAMSA_SYSTEM = "lahiri"

_sid_mode_set = False

def init_sidereal() -> None:
    global _sid_mode_set
    if not _sid_mode_set:
        swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
        _sid_mode_set = True

def value(jd: float) -> float:
    init_sidereal()
    return float(swe.get_ayanamsa(jd))
