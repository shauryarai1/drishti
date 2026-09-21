"""Transit Moon Nakshatra periods - time-aware, using KAVACH astronomy only.

A Nakshatra spans 13 degrees 20 minutes of sidereal longitude. Transitions are
found by scanning at a fixed step and then bisecting to a few seconds, so a
local civil day can legitimately hold more than one period.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from kundli.nakshatra import NAKSHATRA_SPAN, nakshatra_of
from panchang import astronomy

SCAN_STEP = timedelta(minutes=10)
BISECTION_STEPS = 14  # ~10 min / 2^14 -> well under a second


def moon_longitude_at(moment: datetime) -> float:
    """Sidereal Moon longitude via the production astronomy path (Lahiri)."""
    return astronomy.moon_longitude(astronomy.to_jd(moment))


def moon_nakshatra_at(moment: datetime) -> str:
    return str(nakshatra_of(moon_longitude_at(moment))["name"])


def _crossed(start_value: float, end_value: float) -> bool:
    return int(start_value // NAKSHATRA_SPAN) != int(end_value // NAKSHATRA_SPAN)


def find_next_transition(start: datetime, limit: datetime) -> Optional[datetime]:
    """First Nakshatra boundary the Moon crosses in [start, limit]."""
    cursor = start
    previous = moon_longitude_at(cursor)
    while cursor < limit:
        nxt = min(cursor + SCAN_STEP, limit)
        current = moon_longitude_at(nxt)
        if _crossed(previous, current):
            low, high = cursor, nxt
            for _ in range(BISECTION_STEPS):
                mid = low + (high - low) / 2
                if _crossed(previous := moon_longitude_at(low), moon_longitude_at(mid)):
                    high = mid
                else:
                    low = mid
            return high
        previous = current
        cursor = nxt
    return None


def moon_periods(start: datetime, end: datetime) -> List[Tuple[datetime, datetime]]:
    """Contiguous [start, end) slices, each with a single Moon Nakshatra."""
    periods: List[Tuple[datetime, datetime]] = []
    cursor = start
    while cursor < end:
        transition = find_next_transition(cursor, end)
        boundary = transition if transition and transition < end else end
        periods.append((cursor, boundary))
        cursor = boundary
    return periods
