"""Swiss Ephemeris helpers: sidereal longitudes, rise/set times, exact crossings.

Independent of KAVACH. Uses Lahiri (Chitrapaksha) ayanamsa.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Callable, Optional

import swisseph as swe

# Lahiri / Chitrapaksha sidereal mode
swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)

_SIDEREAL = swe.FLG_SWIEPH | swe.FLG_SIDEREAL

SUN = swe.SUN
MOON = swe.MOON


# ---------------------------------------------------------------------------
# Julian day helpers
# ---------------------------------------------------------------------------
def to_jd(moment: datetime) -> float:
    """Timezone-aware datetime -> Julian Day (UT)."""
    if moment.tzinfo is None:
        raise ValueError("datetime must be timezone-aware")
    utc = moment.astimezone(timezone.utc)
    return swe.julday(
        utc.year, utc.month, utc.day,
        utc.hour + utc.minute / 60.0 + utc.second / 3600.0 + utc.microsecond / 3.6e9,
        swe.GREG_CAL,
    )


def from_jd(jd: float) -> datetime:
    """Julian Day (UT) -> timezone-aware UTC datetime."""
    year, month, day, hour = swe.revjul(jd)
    # swisseph may report 24:00:00 for the end of a day
    if hour >= 24.0:
        year, month, day, hour = swe.revjul(jd + 1e-9)
        hour = min(hour, 23.999999)
    hour_int = int(hour)
    minute_float = (hour - hour_int) * 60.0
    minute_int = int(minute_float)
    second_float = (minute_float - minute_int) * 60.0
    # Round to the nearest second to avoid 59.999 -> 60 artefacts
    second_int = int(round(second_float))
    micro = 0
    if second_int >= 60:
        second_int -= 60
        minute_int += 1
    if minute_int >= 60:
        minute_int -= 60
        hour_int += 1
    if hour_int >= 24:
        hour_int -= 24
        micro = 0
        base = datetime(year, month, day, hour_int, minute_int, second_int, micro, tzinfo=timezone.utc)
        return base + timedelta(days=1)
    return datetime(year, month, day, hour_int, minute_int, second_int, micro, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Longitudes
# ---------------------------------------------------------------------------
def _lon(jd: float, body: int) -> float:
    # Set explicitly on every call: the sidereal mode is global library state
    # and must never depend on import order or another caller resetting it.
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    result = swe.calc_ut(jd, body, _SIDEREAL)
    values = result[0]
    lon = values[0]
    if isinstance(lon, tuple):
        lon = lon[0]
    return float(lon) % 360.0


def sun_longitude(jd: float) -> float:
    return _lon(jd, SUN)


def sun_longitude_tropical(jd: float) -> float:
    """Apparent tropical Sun longitude (for the Drik Ritu/Ayana convention)."""
    values = swe.calc_ut(jd, SUN, swe.FLG_SWIEPH)[0]
    return float(values[0][0] if isinstance(values[0], tuple) else values[0]) % 360.0


def moon_longitude(jd: float) -> float:
    return _lon(jd, MOON)


def moon_sun_elongation(jd: float) -> float:
    """(Moon - Sun) sidereal longitude difference, 0..360. Drives Tithi/Karana."""
    return (moon_longitude(jd) - sun_longitude(jd)) % 360.0


def sun_moon_sum(jd: float) -> float:
    """(Sun + Moon) sidereal sum, 0..360. Drives Yoga."""
    return (sun_longitude(jd) + moon_longitude(jd)) % 360.0


# ---------------------------------------------------------------------------
# Exact crossings (numerical solver, not hourly sampling)
# ---------------------------------------------------------------------------
def crossing_time(
    angle_fn: Callable[[float], float],
    target: float,
    jd_from: float,
    jd_limit: float,
    max_iterations: int = 60,
) -> Optional[float]:
    """Find the first JD at/after `jd_from` where `angle_fn` crosses `target`.

    `angle_fn` must return a longitude-like angle in degrees that advances
    monotonically (mod 360). Returns None if no crossing happens before
    `jd_limit`.
    """

    def signed_delta(jd: float) -> float:
        delta = (angle_fn(jd) - target) % 360.0
        return delta - 360.0 if delta > 180.0 else delta

    step = 0.05  # ~72 minutes; a Tithi/Karana can never last longer than this

    lo = jd_from
    # If we start just after a crossing, advance until the angle wraps back
    # around so a valid bracket exists (needed for "next new moon" searches).
    while signed_delta(lo) >= 0 and lo < jd_limit:
        lo += step
    if lo >= jd_limit:
        return None

    hi = lo + step
    while hi <= jd_limit:
        if signed_delta(hi) >= 0:
            break
        lo = hi
        hi = lo + step
    else:
        return None

    for _ in range(max_iterations):
        mid = (lo + hi) / 2.0
        if signed_delta(mid) < 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


# ---------------------------------------------------------------------------
# Rise / set
# ---------------------------------------------------------------------------
def rise_or_set(
    start: datetime,
    latitude: float,
    longitude: float,
    body: int = SUN,
    rising: bool = True,
    altitude: float = 0.0,
) -> Optional[datetime]:
    """Next rise/set of `body` at/after `start` (UT), using Swiss Ephemeris."""
    jd_start = to_jd(start)
    rsmi = swe.CALC_RISE if rising else swe.CALC_SET
    try:
        result = swe.rise_trans(
            jd_start, body, rsmi, (longitude, latitude, altitude), 0.0, 0.0
        )
    except swe.Error:
        return None
    status, times = result
    if status != 0 or not times or times[0] == 0:
        return None
    return from_jd(times[0])


def next_rise_after(
    after: datetime,
    latitude: float,
    longitude: float,
    body: int = SUN,
    rising: bool = True,
) -> Optional[datetime]:
    """Strictly-next rise/set after `after`."""
    return rise_or_set(
        after + timedelta(seconds=90), latitude, longitude, body=body, rising=rising
    )
