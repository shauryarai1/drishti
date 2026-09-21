"""Planetary Hora (planetary hours).

Daylight and night are each divided into 12 equal Horas based on the ACTUAL
calculated sunrise, sunset and next sunrise — never fixed 60-minute blocks.

The planetary sequence is fixed:
    Sun -> Venus -> Mercury -> Moon -> Saturn -> Jupiter -> Mars -> repeat
and the first Hora after sunrise belongs to the lord of the weekday.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List

from .constants import HORA_NATURE, HORA_SEQUENCE, WEEKDAY_LORD


def _sequence_from(lord: str, count: int) -> List[str]:
    start = HORA_SEQUENCE.index(lord)
    return [HORA_SEQUENCE[(start + i) % len(HORA_SEQUENCE)] for i in range(count)]


def _build(
    start: datetime,
    end: datetime,
    lord: str,
    part: str,
    sequence_offset: int,
    reference: datetime | None,
) -> List[Dict[str, object]]:
    unit = (end - start) / 12
    planets = _sequence_from(lord, 12)
    # Build the 13 boundaries once so rows chain exactly and the final row ends
    # precisely at `end` (avoids floating-point drift).
    boundaries = [start + unit * index for index in range(12)] + [end]
    rows: List[Dict[str, object]] = []
    for index, planet in enumerate(planets):
        row_start = boundaries[index]
        row_end = boundaries[index + 1]
        rows.append(
            {
                "planet": planet,
                "nature": HORA_NATURE[planet],
                "part": part,
                "sequence_number": sequence_offset + index + 1,
                "start": row_start,
                "end": row_end,
                "is_current": bool(reference and row_start <= reference < row_end),
            }
        )
    return rows


def compute_horas(
    sunrise: datetime,
    sunset: datetime,
    next_sunrise: datetime,
    weekday: int,
    reference: datetime | None = None,
) -> Dict[str, object]:
    """Return day + night Horas and (optionally) the currently active Hora."""
    lord = WEEKDAY_LORD[weekday]

    day_rows = _build(sunrise, sunset, lord, "day", 0, reference)
    # The night continues the sequence from where the day ended (12 steps on).
    night_lord = HORA_SEQUENCE[(HORA_SEQUENCE.index(lord) + 12) % len(HORA_SEQUENCE)]
    night_rows = _build(sunset, next_sunrise, night_lord, "night", 12, reference)

    all_rows = day_rows + night_rows
    current = next((row for row in all_rows if row["is_current"]), None)
    upcoming = next(
        (row for row in all_rows if reference and row["start"] > reference), None
    )

    return {
        "weekday_lord": lord,
        "day": day_rows,
        "night": night_rows,
        "current": current,
        "next": upcoming,
        "day_hora_minutes": round((sunset - sunrise).total_seconds() / 60.0 / 12.0, 4),
        "night_hora_minutes": round((next_sunrise - sunset).total_seconds() / 60.0 / 12.0, 4),
    }
