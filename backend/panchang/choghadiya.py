"""Choghadiya (day and night) calculation.

Day is split into 8 equal segments from sunrise to sunset and night into 8
equal segments from sunset to the next sunrise. Segment lengths therefore
follow the real day/night duration instead of fixed 90-minute slots.
"""

from __future__ import annotations

from datetime import datetime
from typing import List

from .constants import CHOGHADIYA_CLASS, CHOGHADIYA_CYCLE, CHOGHADIYA_DAY_START


def _segments(start: datetime, end: datetime, first_index: int) -> List[dict]:
    unit = (end - start) / 8
    out: List[dict] = []
    for i in range(8):
        name = CHOGHADIYA_CYCLE[(first_index + i) % 7]
        out.append(
            {
                "name": name,
                "classification": CHOGHADIYA_CLASS[name],
                "start": start + unit * i,
                "end": start + unit * (i + 1),
            }
        )
    return out


def day_choghadiya(sunrise: datetime, sunset: datetime, weekday: int) -> List[dict]:
    return _segments(sunrise, sunset, CHOGHADIYA_DAY_START[weekday])


def night_choghadiya(sunset: datetime, next_sunrise: datetime, weekday: int) -> List[dict]:
    # Common panchang convention: the night sequence continues from the 5th
    # segment of the day. Flagged for reference validation.
    first = (CHOGHADIYA_DAY_START[weekday] + 4) % 7
    return _segments(sunset, next_sunrise, first)
