from typing import Tuple

from config import RASHI_NAMES, RASHI_SYMBOLS


def longitude_to_rashi(longitude: float) -> Tuple[str, str, float]:
    if longitude is None or longitude < 0 or longitude >= 360:
        raise ValueError("Longitude must be in [0, 360)")

    index = int(longitude // 30) % 12
    degree_in_sign = longitude % 30

    return RASHI_NAMES[index], RASHI_SYMBOLS[index], degree_in_sign