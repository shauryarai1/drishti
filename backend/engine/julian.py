"""
Julian date computation for Swiss Ephemeris.
"""
from datetime import datetime, timezone

import swisseph as swe

swe.set_ephe_path("")

def from_utc(dt: datetime) -> float:
    if dt.tzinfo is None:
        raise ValueError("datetime must be timezone-aware")
    utc_dt = dt.astimezone(timezone.utc)
    return swe.julday(
        utc_dt.year,
        utc_dt.month,
        utc_dt.day,
        utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0,
        swe.GREG_CAL,
    )
