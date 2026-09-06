"""
Whole-sign house assignment for Vedic D1 Rashi chart.

House 1 = Lagna sign.
Houses 2..12 = next sequential signs.
"""
from __future__ import annotations

from engine.rashi import longitude_to_rashi


def lagna_sign_index(ascendant_longitude: float) -> int:
    _, sign_number, _ = longitude_to_rashi(ascendant_longitude)
    return sign_number  # 1..12


def assign_house(planet_sign_number: int, lagna_sign_number: int) -> int:
    return ((planet_sign_number - lagna_sign_number) % 12) + 1
