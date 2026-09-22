"""Local-time resolution for KAVACH YES / NO.

The engine must run on the exact LOCAL time of the question in the user's own
timezone, never on server UTC treated as local time.

The authoritative timezone source is the existing KAVACH architecture
(`calculator.timezone_for`, the single place the app asks "what zone is this
point in?"). It is imported lazily and used read-only; nothing in this module
modifies it. The caller's explicit timezone is used only as a fallback, and if
neither is available a ValueError is raised rather than silently assuming a
default zone (India is never assumed).
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from zoneinfo import ZoneInfo

# A real-world UTC offset never exceeds +14:00 / -12:00; anything outside this
# range is treated as malformed rather than used as a clock.
MAX_OFFSET_MINUTES = 14 * 60


def resolve_timezone(latitude: Optional[float] = None, longitude: Optional[float] = None,
                     fallback: str = "") -> Optional[str]:
    """Authoritative IANA zone for the coordinates, else the explicit fallback."""
    name: Optional[str] = None
    if latitude is not None and longitude is not None:
        try:
            from calculator import timezone_for

            name = timezone_for(float(latitude), float(longitude))
        except Exception:
            name = None
    return name or (fallback or None)


def local_datetime_for(instant: datetime, timezone_name: str) -> datetime:
    """Convert a timezone-aware instant into the given local timezone."""
    if not isinstance(instant, datetime):
        raise ValueError("instant must be a datetime")
    if instant.tzinfo is None:
        raise ValueError("instant must be timezone-aware; use resolve_local_datetime for naive input")
    if not timezone_name:
        raise ValueError("timezone_name is required")
    return instant.astimezone(ZoneInfo(timezone_name))


def resolve_local_datetime(instant: datetime, latitude: Optional[float] = None,
                           longitude: Optional[float] = None,
                           timezone_name: str = "") -> datetime:
    """The local datetime the engine must use for this question.

    Prefers the authoritative zone for the coordinates, then the caller's
    explicit timezone. Raises when no zone can be established.
    """
    zone = resolve_timezone(latitude, longitude, timezone_name)
    if not zone:
        raise ValueError("A timezone or coordinates are required to resolve the local time")
    if instant.tzinfo is None:
        # Already a local wall-clock time; attach the resolved zone without shifting.
        return instant.replace(tzinfo=ZoneInfo(zone))
    return instant.astimezone(ZoneInfo(zone))


def zone_offset_minutes(instant: datetime, timezone_name: str) -> Optional[int]:
    """The IANA zone's actual UTC offset for this instant, in minutes."""
    if not timezone_name:
        return None
    try:
        offset = instant.astimezone(ZoneInfo(timezone_name)).utcoffset()
    except Exception:
        return None
    if offset is None:
        return None
    return int(offset.total_seconds() // 60)


def _valid_offset(value: Optional[int]) -> Optional[int]:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    if -MAX_OFFSET_MINUTES <= value <= MAX_OFFSET_MINUTES:
        return value
    return None


def resolve_local_time(instant: datetime, timezone_name: str = "",
                       utc_offset_minutes: Optional[int] = None,
                       ) -> Tuple[datetime, Dict[str, object]]:
    """Resolve the user's local wall clock, cross-checking the two time sources.

    The browser's IANA zone remains the primary source. The browser-reported UTC
    offset (minutes east of UTC) is used to validate it, and as the fallback when
    the two disagree, so the engine still evaluates the user's device clock
    instead of a clearly inconsistent zone.

    Returns (local_datetime, diagnostics). Diagnostics are privacy-safe: they
    describe the time resolution only.
    """
    submitted = _valid_offset(utc_offset_minutes)
    zone_offset = zone_offset_minutes(instant, timezone_name) if timezone_name else None

    if zone_offset is not None and (submitted is None or submitted == zone_offset):
        return instant.astimezone(ZoneInfo(timezone_name)), {
            "source": "iana+offset" if submitted is not None else "iana",
            "matched": submitted is not None,
            "zone_offset_minutes": zone_offset,
            "submitted_offset_minutes": submitted,
        }

    # Disagreement, an unknown zone, or a malformed offset: use the device clock.
    if submitted is not None:
        wall_clock = (instant.astimezone(ZoneInfo("UTC")) + timedelta(minutes=submitted)).replace(tzinfo=None)
        return wall_clock, {
            "source": "offset_fallback",
            "matched": False,
            "zone_offset_minutes": zone_offset,
            "submitted_offset_minutes": submitted,
        }

    if zone_offset is not None:
        # No offset supplied (older client): keep the existing behaviour exactly.
        return instant.astimezone(ZoneInfo(timezone_name)), {
            "source": "iana",
            "matched": False,
            "zone_offset_minutes": zone_offset,
            "submitted_offset_minutes": None,
        }

    raise ValueError("A timezone or coordinates are required to resolve the local time")
