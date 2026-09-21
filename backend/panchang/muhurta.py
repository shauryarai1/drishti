"""Traditional muhurta / kalam period calculations.

Pure time arithmetic on the local sunrise, sunset and next sunrise.
No ephemeris calls live here.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional

from .constants import (
    DUR_MUHURTA_PART,
    GULIKA_PART,
    RAHU_KALAM_PART,
    YAMAGANDA_PART,
)

Period = dict


def _window(start: datetime, end: datetime, name: str, kind: str, note: str = "") -> Period:
    return {"name": name, "kind": kind, "start": start, "end": end, "note": note}


def _split(start: datetime, end: datetime, parts: int) -> timedelta:
    return (end - start) / parts


def day_part(sunrise: datetime, sunset: datetime, part: int, parts: int = 8) -> tuple:
    """1-indexed equal part of the daytime."""
    unit = _split(sunrise, sunset, parts)
    begin = sunrise + unit * (part - 1)
    return begin, begin + unit


def night_part(sunset: datetime, next_sunrise: datetime, part: int, parts: int = 15) -> tuple:
    """1-indexed equal part of the night (sunset -> next sunrise)."""
    unit = _split(sunset, next_sunrise, parts)
    begin = sunset + unit * (part - 1)
    return begin, begin + unit


def day_muhurta(sunrise: datetime, sunset: datetime, index: int) -> tuple:
    """1-indexed muhurta of the day (day split into 15)."""
    return day_part(sunrise, sunset, index, 15)


def night_muhurta(sunset: datetime, next_sunrise: datetime, index: int) -> tuple:
    """1-indexed muhurta of the night (night split into 15)."""
    return night_part(sunset, next_sunrise, index, 15)


# ---------------------------------------------------------------------------
# Inauspicious (kalam) periods — day split into 8 equal parts
# ---------------------------------------------------------------------------
def rahu_kalam(sunrise: datetime, sunset: datetime, weekday: int) -> Period:
    start, end = day_part(sunrise, sunset, RAHU_KALAM_PART[weekday])
    return _window(start, end, "Rahu Kalam", "inauspicious")


def yamaganda(sunrise: datetime, sunset: datetime, weekday: int) -> Period:
    start, end = day_part(sunrise, sunset, YAMAGANDA_PART[weekday])
    return _window(start, end, "Yamaganda", "inauspicious")


def gulika_kalam(sunrise: datetime, sunset: datetime, weekday: int) -> Period:
    start, end = day_part(sunrise, sunset, GULIKA_PART[weekday])
    return _window(start, end, "Gulika Kalam", "inauspicious")


def dur_muhurta(sunrise: datetime, sunset: datetime, weekday: int) -> Period:
    """Day split into 15 muhurtas; the inauspicious index depends on weekday."""
    start, end = day_muhurta(sunrise, sunset, DUR_MUHURTA_PART[weekday])
    return _window(start, end, "Dur Muhurta", "inauspicious")


# ---------------------------------------------------------------------------
# Auspicious periods
# ---------------------------------------------------------------------------
def abhijit_muhurta(sunrise: datetime, sunset: datetime) -> Period:
    """8th muhurta of the day, centred on local solar noon."""
    start, end = day_muhurta(sunrise, sunset, 8)
    return _window(start, end, "Abhijit Muhurta", "auspicious")


def vijaya_muhurta(sunrise: datetime, sunset: datetime) -> Period:
    """11th muhurta of the day."""
    start, end = day_muhurta(sunrise, sunset, 11)
    return _window(start, end, "Vijaya Muhurta", "auspicious")


def brahma_muhurta(sunset: datetime, next_sunrise: datetime) -> Period:
    """14th muhurta of the night (immediately before the pre-dawn muhurta)."""
    start, end = night_muhurta(sunset, next_sunrise, 14)
    return _window(start, end, "Brahma Muhurta", "auspicious")


def nishita_muhurta(sunset: datetime, next_sunrise: datetime) -> Period:
    """8th muhurta of the night, centred on local midnight."""
    start, end = night_muhurta(sunset, next_sunrise, 8)
    return _window(start, end, "Nishita Muhurta", "auspicious")


def godhuli_muhurta(sunrise: datetime, sunset: datetime, next_sunrise: datetime) -> Period:
    """Godhuli: the twilight immediately after sunset.

    Duration is derived from the night length (sunset -> sunset + night_len/30).
    Empirically matches the reference panchang for Delhi and London; flagged for
    further validation.
    """
    length = (next_sunrise - sunset) / 30.0
    return _window(sunset, sunset + length, "Godhuli Muhurta", "auspicious",
                   note="Duration derived as night/30; verify against reference.")


# ---------------------------------------------------------------------------
# Convenience
# ---------------------------------------------------------------------------
def inauspicious_periods(sunrise: datetime, sunset: datetime, weekday: int) -> List[Period]:
    return [
        rahu_kalam(sunrise, sunset, weekday),
        yamaganda(sunrise, sunset, weekday),
        gulika_kalam(sunrise, sunset, weekday),
        dur_muhurta(sunrise, sunset, weekday),
    ]


def auspicious_periods(
    sunrise: datetime,
    sunset: datetime,
    next_sunrise: datetime,
) -> List[Period]:
    return [
        brahma_muhurta(sunset, next_sunrise),
        abhijit_muhurta(sunrise, sunset),
        vijaya_muhurta(sunrise, sunset),
        godhuli_muhurta(sunrise, sunset, next_sunrise),
        nishita_muhurta(sunset, next_sunrise),
    ]


def solar_noon(sunrise: datetime, sunset: datetime) -> datetime:
    return sunrise + (sunset - sunrise) / 2


def contains(period: Period, moment: Optional[datetime]) -> bool:
    if moment is None:
        return False
    return period["start"] <= moment < period["end"]
