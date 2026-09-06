from typing import Tuple

from config import NAKSHATRA_NAMES

NAKSHATRA_SPAN = 360.0 / 27.0


def longitude_to_nakshatra(longitude: float) -> Tuple[str, int]:
    if longitude is None or longitude < 0 or longitude >= 360:
        raise ValueError("Longitude must be in [0, 360)")

    index = int(longitude // NAKSHATRA_SPAN)
    pada = int((longitude % NAKSHATRA_SPAN) / (NAKSHATRA_SPAN / 4.0)) + 1

    return NAKSHATRA_NAMES[index], pada