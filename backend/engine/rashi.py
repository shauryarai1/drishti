"""
Rashi and nakshatra utilities.

All calculations use sidereal longitude in degrees [0, 360).
"""
from __future__ import annotations

from config import NAKSHATRA_NAMES, RASHI_NAMES, RASHI_SYMBOLS

NAKSHATRA_LENGTH = 360.0 / 27
PADA_LENGTH = NAKSHATRA_LENGTH / 4


def longitude_to_rashi(longitude: float):
    longitude = float(longitude) % 360.0
    sign_index = int(longitude // 30)  # 0-based
    degree = longitude - sign_index * 30
    return RASHI_NAMES[sign_index], sign_index + 1, degree


def longitude_to_nakshatra(longitude: float):
    longitude = float(longitude) % 360.0
    index = int(longitude // NAKSHATRA_LENGTH)
    pada = int((longitude % NAKSHATRA_LENGTH) // PADA_LENGTH) + 1
    return NAKSHATRA_NAMES[index], pada
