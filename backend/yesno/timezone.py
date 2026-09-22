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

from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo


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
