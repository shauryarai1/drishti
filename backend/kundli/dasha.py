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


def vimshottari_dasha(moon_longitude: float, birth: datetime,
                      span_years: float = TOTAL_YEARS) -> Dict[str, Any]:
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

    now = datetime.now(birth.tzinfo) if birth.tzinfo else datetime.now()
    current = next((item for item in mahadashas
                    if item["start"] <= _stamp(now) < item["end"]), None)

    current_antar = None
    antars: List[Dict[str, Any]] = []
    if current:
        start = datetime.fromisoformat(current["start"])
        antars = antardashas(current["lord"], start, current["years"])
        for index, item in enumerate(antars):
            if item["start"] <= _stamp(now) < item["end"]:
                current_antar = {**item, "index": index + 1, "of": len(antars)}
                break

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
    }
