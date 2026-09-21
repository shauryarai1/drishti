"""KAVACH Daily Prediction engine.

DAILY MOON is the Lahiri sidereal Moon rashi AT LOCAL SUNRISE for the selected
Panchang day, and it stays fixed for that day even if the live Moon changes
rashi later.

Natal Moon sign becomes house 1; the remaining signs follow sequentially; the
DAILY MOON rashi identifies the active house for each Moon sign.

Deterministic only: no AI, no Ascendant, no proprietary Mars logic.
"""

from __future__ import annotations

from datetime import date as date_type, datetime
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from calculator import BirthData, _sign_from_longitude, generate_chart
from panchang import PanchangRequest, astronomy, compute_panchang

from .config import HOUSE_PATTERNS, colour_for, status

RASHIS = ("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
          "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")


def rashi_number(rashi: str) -> int:
    """1 = Aries ... 12 = Pisces."""
    return RASHIS.index(rashi) + 1


def _moon_longitude(moment: datetime) -> float:
    """Sidereal Moon longitude via the production astronomy path (Lahiri)."""
    return astronomy.moon_longitude(astronomy.to_jd(moment))


def _rashi_of(longitude: float) -> str:
    sign, _index, _degree = _sign_from_longitude(longitude)
    return sign


def get_natal_moon_sign(payload: Dict[str, Any]) -> str:
    chart = generate_chart(BirthData(
        date=str(payload["date"]), time=str(payload["time"]),
        place=payload.get("place") or "Unknown",
        latitude=float(payload["latitude"]), longitude=float(payload["longitude"]),
    ))
    moon = next(planet for planet in chart.planets if planet.name == "Moon")
    return moon.sign


def get_sunrise(payload: Dict[str, Any], on_date: date_type) -> datetime:
    """Local sunrise from the PRODUCTION Panchang engine (no new astronomy)."""
    panchang = compute_panchang(PanchangRequest(
        on_date=on_date,
        latitude=float(payload["latitude"]),
        longitude=float(payload["longitude"]),
        timezone_name=payload.get("timezone") or "Asia/Kolkata",
        label=payload.get("place") or "",
    ))
    return datetime.fromisoformat(panchang["sun_moon"]["sunrise"])


def get_daily_moon_rashi(payload: Dict[str, Any], on_date: Optional[date_type] = None) -> Dict[str, Any]:
    """Daily Moon rashi = Moon rashi at local sunrise, fixed for that day."""
    timezone_name = payload.get("timezone") or "Asia/Kolkata"
    tz = ZoneInfo(timezone_name)
    selected = on_date or datetime.now(tz).date()
    sunrise = get_sunrise(payload, selected)
    longitude = _moon_longitude(sunrise)
    return {
        "date": selected.isoformat(),
        "sunrise": sunrise.isoformat(),
        "sunriseLocal": sunrise.strftime("%H:%M"),
        "longitude": round(longitude, 6),
        "rashi": _rashi_of(longitude),
    }


def get_current_moon_rashi(payload: Dict[str, Any], at: Optional[str] = None) -> Dict[str, Any]:
    """Live/current Moon rashi - reported separately, never used for the cards."""
    timezone_name = payload.get("timezone") or "Asia/Kolkata"
    tz = ZoneInfo(timezone_name)
    now = datetime.fromisoformat(at).astimezone(tz) if at else datetime.now(tz)
    longitude = _moon_longitude(now)
    return {"rashi": _rashi_of(longitude), "longitude": round(longitude, 6), "asOf": now.isoformat()}


def get_current_transit_moon_sign(moment: datetime) -> str:
    """Live Moon rashi at a given instant (kept for compatibility/auditing)."""
    return _rashi_of(_moon_longitude(moment))


def calculate_active_house(natal_moon: str, daily_moon: str) -> int:
    """House of the DAILY Moon rashi in the chart built from the natal Moon."""
    return ((rashi_number(daily_moon) - rashi_number(natal_moon) + 12) % 12) + 1


def get_best_colour(natal_moon_sign: Optional[str], daily_moon_rashi: Optional[str]) -> Optional[str]:
    """Personalised daily colour awaiting the approved KAVACH matrix.

    Takes BOTH dimensions (natal Moon + Daily Moon) so a personalised daily
    colour can change day to day and differ between people.
    """
    return colour_for(natal_moon_sign, daily_moon_rashi)


def get_daily_house_pattern(active_house: int) -> Dict[str, Any]:
    entry = HOUSE_PATTERNS.get(active_house) or HOUSE_PATTERNS[1]
    return {"activeHouse": active_house, "theme": entry["theme"], "pattern": entry["pattern"]}


def get_daily_category_status(active_house: int) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for category in ("love", "health", "career"):
        level, reason = status(active_house, category)
        result[category] = {"status": level, "reason": reason}
    return result


def build_daily_prediction(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Today's pattern for all 12 Moon signs, based on the sunrise Daily Moon."""
    timezone_name = payload.get("timezone") or "Asia/Kolkata"
    selected = date_type.fromisoformat(payload["date"]) if payload.get("date") else None

    daily = get_daily_moon_rashi(payload, selected)
    current = get_current_moon_rashi(payload, payload.get("at") or None)
    daily_moon = daily["rashi"]

    natal_moon: Optional[str] = payload.get("natal_moon") or None
    if not natal_moon and payload.get("birth_date") and payload.get("birth_time"):
        natal_moon = get_natal_moon_sign({
            "date": payload["birth_date"], "time": payload["birth_time"],
            "place": payload.get("birth_place", ""),
            "latitude": payload["latitude"], "longitude": payload["longitude"],
        })

    cards: List[Dict[str, Any]] = []
    for sign in RASHIS:
        active_house = calculate_active_house(sign, daily_moon)
        pattern = get_daily_house_pattern(active_house)
        cards.append({
            "sign": sign,
            "activeHouse": active_house,
            "title": pattern["theme"],
            "pattern": pattern["pattern"],
            "categories": get_daily_category_status(active_house),
            "bestColour": get_best_colour(sign, daily_moon),
            "isPersonal": sign == natal_moon,
        })

    return {
        "status": "ok",
        "asOf": {"timestamp": current["asOf"], "timezone": timezone_name},
        "dailyMoon": daily,
        "currentMoon": current,
        "natalMoon": natal_moon,
        "signs": cards,
        "basis": "daily_moon_rashi_at_local_sunrise_with_natal_moon_as_house_1",
    }
