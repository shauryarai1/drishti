"""Vimshottari Dasha — isolated deterministic engine (no astrology engine changes).

Convention used here (documented so tests are not self-referential):

* Sidereal Moon longitude at birth decides the Nakshatra and its lord.
* Only the PROPORTIONAL BALANCE of that lord's Mahadasha remains at birth:
  balance = (1 - progress through the nakshatra) * lord's total years.
* Mahadasha order is the standard Vimshottari cycle:
  Ketu 7, Venus 20, Sun 6, Moon 10, Mars 7, Rahu 18, Jupiter 16, Saturn 19,
  Mercury 17  (total 120 years).
* One year is taken as 365.2425 days (mean Gregorian year) - a single,
  explicit convention rather than mixed rounding.
* Antardasha within a Mahadasha is proportional:
  mahadasha_years * antardasha_lord_years / 120, sequenced from the Mahadasha
  lord and continuing cyclically through the same order.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .nakshatra import VIMSHOTTARI_CYCLE, lord_for_name, nakshatra_of

ORDER = VIMSHOTTARI_CYCLE  # single source, shared with the derivation
YEARS: Dict[str, float] = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17,
}
TOTAL_YEARS = sum(YEARS.values())  # 120
YEAR_DAYS = 365.2425
DASHA_LEVELS = ("Mahadasha", "Antardasha", "Pratyantardasha", "Sookshma", "Prana")



def _cycle_from(lord: str) -> List[str]:
    start = ORDER.index(lord)
    return list(ORDER[start:]) + list(ORDER[:start])


def _stamp(moment: datetime) -> str:
    return moment.isoformat()


def _add_years(moment: datetime, years: float) -> datetime:
    return moment + timedelta(days=years * YEAR_DAYS)


def antardashas(maha_lord: str, start: datetime, maha_years: float) -> List[Dict[str, Any]]:
    """Sub-periods of one Mahadasha, contiguous and proportional."""
    period = _add_years(start, maha_years) - start
    total_seconds = period.total_seconds()
    result: List[Dict[str, Any]] = []
    cursor = start
    for lord in _cycle_from(maha_lord):
        share = YEARS[lord] / TOTAL_YEARS
        span = timedelta(seconds=total_seconds * share)
        end = cursor + span
        result.append({"lord": lord, "start": _stamp(cursor), "end": _stamp(end)})
        cursor = end
    if result:
        result[-1]["end"] = _stamp(_add_years(start, maha_years))
    return result


def _parse_stamp(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _subperiods(parent_lord: str, parent_start: str, parent_end: str) -> List[Dict[str, Any]]:
    """Recursively subdivide one period using the existing Vimshottari ratios."""
    start = _parse_stamp(parent_start)
    end = _parse_stamp(parent_end)
    total_seconds = (end - start).total_seconds()
    result: List[Dict[str, Any]] = []
    cursor = start
    cycle = _cycle_from(parent_lord)

    for index, lord in enumerate(cycle):
        child_end = end if index == len(cycle) - 1 else cursor + timedelta(
            seconds=total_seconds * YEARS[lord] / TOTAL_YEARS)
        result.append({
            "lord": lord,
            "start": parent_start if index == 0 else _stamp(cursor),
            "end": parent_end if index == len(cycle) - 1 else _stamp(child_end),
            "years": round((child_end - cursor).total_seconds() / (YEAR_DAYS * 86400), 9),
            "index": index + 1,
            "of": len(cycle),
        })
        cursor = child_end
    return result


def dasha_children(level: int, parent_lord: str, parent_start: str,
                   parent_end: str) -> List[Dict[str, Any]]:
    """Return one on-demand child level below a Vimshottari parent period.

    `level` is the child depth: 1=Antardasha, 2=Pratyantardasha,
    3=Sookshma, 4=Prana. The parent boundary strings are preserved exactly
    for the first/last child so recursive consumers cannot accumulate gaps.
    """
    if level not in range(1, len(DASHA_LEVELS)):
        raise ValueError("Dasha child level must be between 1 and 4")
    if parent_lord not in YEARS:
        raise ValueError("Unknown Vimshottari lord")
    children = _subperiods(parent_lord, parent_start, parent_end)
    child_level = DASHA_LEVELS[level]
    return [{**item, "level": child_level} for item in children]


def _current_period(periods: List[Dict[str, Any]], now: datetime) -> Optional[Dict[str, Any]]:
    stamp = _stamp(now)
    return next((period for period in periods
                 if period["start"] <= stamp < period["end"]), None)


def vimshottari_dasha(moon_longitude: float, birth: datetime,
                      span_years: float = TOTAL_YEARS,
                      now: Optional[datetime] = None) -> Dict[str, Any]:
    """Balance-at-birth Mahadashas plus current Mahadasha and Antardasha."""
    info = nakshatra_of(moon_longitude)
    lord = info["lord"] or lord_for_name(info["name"])
    progress = info["progress"]
    balance_years = (1.0 - progress) * YEARS[lord]

    mahadashas: List[Dict[str, Any]] = []
    cursor = birth
    remaining = span_years
    first = True
    # Continue cyclically so the timeline wraps (Mercury -> Ketu -> ...) whenever
    # the requested span extends past one full Vimshottari cycle.
    lords = _cycle_from(lord)
    step = 0
    while remaining > 1e-9 and step < 200:
        maha_lord = lords[step % len(lords)]
        years = balance_years if first else YEARS[maha_lord]
        years = min(years, remaining)
        end = _add_years(cursor, years)
        mahadashas.append({
            "lord": maha_lord,
            "start": _stamp(cursor),
            "end": _stamp(end),
            "years": round(years, 6),
            "isBalanceAtBirth": first,
        })
        remaining -= years
        cursor = end
        first = False
        step += 1

    now = now or (datetime.now(birth.tzinfo) if birth.tzinfo else datetime.now())
    current = _current_period(mahadashas, now)

    current_antar = None
    antars: List[Dict[str, Any]] = []
    if current:
        start = datetime.fromisoformat(current["start"])
        antars = antardashas(current["lord"], start, current["years"])
        for index, item in enumerate(antars):
            if item["start"] <= _stamp(now) < item["end"]:
                current_antar = {**item, "index": index + 1, "of": len(antars)}
                break

    current_levels: List[Dict[str, Any]] = []
    parent = current
    for level in range(1, len(DASHA_LEVELS)):
        if not parent:
            break
        children = dasha_children(level, parent["lord"], parent["start"], parent["end"])
        current_child = _current_period(children, now)
        if not current_child:
            break
        current_levels.append(current_child)
        parent = current_child

    return {
        "birthNakshatra": info["name"],
        "birthNakshatraLord": lord,
        "progressAtBirth": round(progress, 6),
        "balanceAtBirth": {
            "lord": lord,
            "years": round(balance_years, 6),
            "until": _stamp(_add_years(birth, balance_years)),
        },
        "mahadashas": mahadashas,
        "currentMahadasha": current,
        "antardashas": antars,
        "currentAntardasha": current_antar,
        "currentPratyantardasha": current_levels[1] if len(current_levels) > 1 else None,
        "currentSookshma": current_levels[2] if len(current_levels) > 2 else None,
        "currentPrana": current_levels[3] if len(current_levels) > 3 else None,
        "currentDashaFlow": ([item for item in [
            {"level": "Mahadasha", **current} if current else None,
            {"level": "Antardasha", **current_levels[0]} if len(current_levels) > 0 else None,
            {"level": "Pratyantardasha", **current_levels[1]} if len(current_levels) > 1 else None,
            {"level": "Sookshma", **current_levels[2]} if len(current_levels) > 2 else None,
            {"level": "Prana", **current_levels[3]} if len(current_levels) > 3 else None,
        ] if item is not None] if current else []),
    }
