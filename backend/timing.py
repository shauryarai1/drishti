"""Swiss Ephemeris caution-window calculation for DRISHTI."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Callable, Iterable, Sequence

import swisseph as swe

from config import RASHI_NAMES, AYANAMSA


CAUTION_HORIZON_YEARS = 10
CAUTION_LOOKBACK_DAYS = 1825
CAUTION_SCAN_STEP_DAYS = 1
CAUTION_BODIES = ("Saturn", "Rahu", "Ketu")
_BODY_INDEX = {"Saturn": swe.SATURN, "Rahu": swe.MEAN_NODE, "Ketu": swe.MEAN_NODE}

if AYANAMSA == "lahiri":
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
else:
    raise ValueError(f"Unsupported ayanamsa: {AYANAMSA}")


@dataclass(frozen=True)
class CautionWindow:
    start_date: date
    end_date: date
    level: str
    area: str
    title: str
    guidance: str
    triggers: tuple[tuple[str, str], ...]


def _julian_day(moment: datetime) -> float:
    return swe.julday(
        moment.year,
        moment.month,
        moment.day,
        moment.hour + moment.minute / 60 + moment.second / 3600,
        swe.GREG_CAL,
    )


def _transit_sign_index(body: str, moment: datetime) -> int:
    result = swe.calc_ut(_julian_day(moment), _BODY_INDEX[body], swe.FLG_SIDEREAL)
    longitude = float(result[0][0] if isinstance(result[0], tuple) else result[0])
    if body == "Ketu":
        longitude = (longitude + 180) % 360
    return int(longitude // 30) % 12


def _boundary(
    body: str,
    left: datetime,
    right: datetime,
    previous_sign: int,
    position_fn: Callable[[str, datetime], int],
) -> datetime:
    """Refine a target/non-target transition to sub-day precision."""
    for _ in range(42):
        middle = left + (right - left) / 2
        sign = position_fn(body, middle)
        if sign == previous_sign:
            left = middle
        else:
            right = middle
    return right


def _body_windows(
    body: str,
    start: datetime,
    end: datetime,
    target_indices: set[int],
    position_fn: Callable[[str, datetime], int],
) -> list[tuple[datetime, datetime, int]]:
    windows: list[tuple[datetime, datetime, int]] = []
    cursor = start
    previous_sign = position_fn(body, cursor)
    entered_at = cursor if previous_sign in target_indices else None
    entered_sign = previous_sign if entered_at is not None else None

    while cursor < end:
        next_cursor = min(cursor + timedelta(days=CAUTION_SCAN_STEP_DAYS), end)
        current_sign = position_fn(body, next_cursor)
        if current_sign != previous_sign:
            transition = _boundary(body, cursor, next_cursor, previous_sign, position_fn)
            if entered_at is not None and entered_sign is not None:
                windows.append((entered_at, transition, entered_sign))
            if current_sign in target_indices:
                entered_at = transition
                entered_sign = current_sign
            else:
                entered_at = None
                entered_sign = None
        previous_sign = current_sign
        cursor = next_cursor

    if entered_at is not None and entered_sign is not None:
        windows.append((entered_at, end, entered_sign))
    return windows


def _merge_windows(windows: Iterable[CautionWindow]) -> list[CautionWindow]:
    ordered = sorted(windows, key=lambda item: (item.start_date, item.end_date))
    merged: list[CautionWindow] = []
    for window in ordered:
        if not merged or window.start_date > merged[-1].end_date + timedelta(days=1):
            merged.append(window)
            continue
        previous = merged[-1]
        triggers = tuple(dict.fromkeys(previous.triggers + window.triggers))
        level = "high" if len(triggers) > 1 else previous.level
        merged[-1] = CautionWindow(
            start_date=previous.start_date,
            end_date=max(previous.end_date, window.end_date),
            level=level,
            area=previous.area if previous.area == window.area else "Several highlighted areas",
            title=previous.title if previous.area == window.area else "Several areas need greater care",
            guidance=previous.guidance if previous.area == window.area else "Move more deliberately and pay attention to the highlighted areas of your reading. Avoid unnecessary escalation and give important decisions more time.",
            triggers=triggers,
        )
    return merged


def calculate_caution_windows(
    target_rashis: Sequence[str],
    guidance: dict[str, dict[str, str]],
    start_date: date | None = None,
    horizon_years: int = CAUTION_HORIZON_YEARS,
    position_fn: Callable[[str, datetime], int] | None = None,
) -> dict[str, object]:
    """Calculate public caution windows from real sidereal transit positions."""
    today = start_date or date.today()
    horizon_end = today.replace(year=today.year + horizon_years)
    scan_start = datetime.combine(today - timedelta(days=CAUTION_LOOKBACK_DAYS), datetime.min.time(), tzinfo=timezone.utc)
    scan_end = datetime.combine(horizon_end + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
    target_indices = {RASHI_NAMES.index(name) for name in target_rashis}
    position = position_fn or _transit_sign_index
    windows: list[CautionWindow] = []

    for body in CAUTION_BODIES:
        body_windows = _body_windows(body, scan_start, scan_end, target_indices, position)
        for entered, exited, target_index in body_windows:
            target = RASHI_NAMES[target_index]
            area_data = guidance[target]
            windows.append(CautionWindow(
                start_date=entered.date(),
                end_date=exited.date(),
                level="high" if body == "Saturn" else "moderate",
                area=area_data["area"],
                title=f"Greater care with {area_data['area'].lower()}",
                guidance=area_data["danger"],
                triggers=((body, target),),
            ))

    merged = _merge_windows(windows)
    visible = [window for window in merged if window.end_date >= today and window.start_date <= horizon_end]
    current = next((window for window in visible if window.start_date <= today <= window.end_date), None)
    upcoming = [window for window in visible if window.start_date > today]

    def public(window: CautionWindow) -> dict[str, object]:
        return {
            "start_date": window.start_date.isoformat(),
            "end_date": window.end_date.isoformat(),
            "level": window.level,
            "area": window.area,
            "title": window.title,
            "guidance": window.guidance,
        }

    return {"current": public(current) if current else None, "upcoming": [public(item) for item in upcoming]}
