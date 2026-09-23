"""KAVACH Daily Prediction engine.

DAILY MOON is the Lahiri sidereal Moon rashi AT LOCAL SUNRISE for the selected
Panchang day, and it stays fixed for that day even if the live Moon changes
rashi later.

The transit Moon rashi is house 1 and the twelve signs follow the zodiac in
order from it, so each card's house counts FORWARD from the transit Moon (Moon
in Capricorn: Capricorn H1, Aquarius H2, Pisces H3, ... Sagittarius H12).

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
    return datetime.fromisoformat(_panchang_for_day(payload, on_date)["sun_moon"]["sunrise"])


def _panchang_for_day(payload: Dict[str, Any], on_date: date_type) -> Dict[str, Any]:
    """The single authoritative Panchang calculation for the selected day/location.

    Sunrise, sunset, the Moon rashi and the Hora schedule all come from this one
    calculation, so Daily Prediction can never disagree with the Panchang page.
    """
    return compute_panchang(PanchangRequest(
        on_date=on_date,
        latitude=float(payload["latitude"]),
        longitude=float(payload["longitude"]),
        timezone_name=payload.get("timezone") or "Asia/Kolkata",
        label=payload.get("place") or "",
    ))


def get_daily_moon_rashi(payload: Dict[str, Any], on_date: Optional[date_type] = None) -> Dict[str, Any]:
    """Daily Moon rashi = the authoritative Panchang Moon rashi at local sunrise.

    Taken directly from the same Panchang payload that supplies the sunrise, so
    the 12 daily cards are anchored to the identical value the Panchang page uses.
    """
    timezone_name = payload.get("timezone") or "Asia/Kolkata"
    tz = ZoneInfo(timezone_name)
    # The DAILY DAY boundary is local midnight. An explicitly requested date is
    # authoritative: the caller's calendar date must never be replaced by the
    # server clock, and sunrise/Moonrise must never move the day boundary.
    requested = payload.get("date")
    if on_date is not None:
        selected = on_date
    elif requested:
        selected = date_type.fromisoformat(str(requested))
    else:
        selected = datetime.now(tz).date()
    panchang = _panchang_for_day(payload, selected)
    sunrise = datetime.fromisoformat(panchang["sun_moon"]["sunrise"])

    moon_block = (panchang.get("sun_moon_rashi") or {}).get("moon") or {}
    index = moon_block.get("index")
    if isinstance(index, int) and 0 <= index < len(RASHIS):
        rashi = RASHIS[index]  # authoritative: same index the Panchang page reports
        longitude = float(moon_block.get("longitude") or _moon_longitude(sunrise))
    else:  # defensive only: the engine always provides the index
        longitude = _moon_longitude(sunrise)
        rashi = _rashi_of(longitude)

    return {
        "date": selected.isoformat(),
        "sunrise": sunrise.isoformat(),
        "sunriseLocal": sunrise.strftime("%H:%M"),
        "longitude": round(longitude, 6),
        "rashi": rashi,
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
    """House of this sign counted FORWARD through the zodiac from the transit Moon.

    The transit (daily) Moon rashi is house 1 and the remaining signs follow the
    zodiac in order: Moon in Capricorn gives Capricorn H1, Aquarius H2, Pisces H3,
    Aries H4, ... Sagittarius H12. Parameter names are kept for compatibility;
    `daily_moon` is the transit anchor.
    """
    return ((rashi_number(natal_moon) - rashi_number(daily_moon) + 12) % 12) + 1


def get_best_colour(natal_moon_sign: Optional[str], daily_moon_rashi: Optional[str]) -> Optional[str]:
    """Personalised daily colour awaiting the approved KAVACH matrix.

    Takes BOTH dimensions (natal Moon + Daily Moon) so a personalised daily
    colour can change day to day and differ between people.
    """
    return colour_for(natal_moon_sign, daily_moon_rashi)


def get_daily_house_pattern(active_house: int) -> Dict[str, Any]:
    entry = HOUSE_PATTERNS.get(active_house) or HOUSE_PATTERNS[1]
    return {"activeHouse": active_house, "theme": entry["theme"], "pattern": entry["pattern"]}


def get_daily_category_status(active_house: int, nakshatra: str = "") -> Dict[str, Any]:
    from nakshatra_knowledge.modes import compose_category

    result: Dict[str, Any] = {}
    for category in ("love", "health", "career"):
        level, reason = status(active_house, category)
        result[category] = {"status": level, "reason": compose_category(reason, nakshatra)}
    return result


def build_daily_prediction(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Today's pattern for all 12 Moon signs, based on the sunrise Daily Moon."""
    timezone_name = payload.get("timezone") or "Asia/Kolkata"
    selected = date_type.fromisoformat(payload["date"]) if payload.get("date") else None

    daily = get_daily_moon_rashi(payload, selected)
    current = get_current_moon_rashi(payload, payload.get("at") or None)
    daily_moon = daily["rashi"]

    # ADDITIVE Nakshatra layer (owner-approved): the transit Nakshatra at the
    # same sunrise anchor supplies HOW the day expresses, while the existing
    # active-house calculation supplies WHERE. The house methodology is
    # untouched; this only adds interpretation. The transit Nakshatra comes from
    # the existing sunrise Moon longitude via the shared nakshatra helper, so no
    # new astronomy is introduced.
    from kundli.nakshatra import nakshatra_of
    from nakshatra_knowledge.modes import compose_guidance, navtara_tone, transit_mode_line
    transit_nakshatra = ""
    try:
        transit_nakshatra = str(nakshatra_of(_moon_longitude(datetime.fromisoformat(daily["sunrise"])))["name"])
    except Exception:  # a Nakshatra failure must never break the Daily reading
        transit_nakshatra = ""

    # Personal tone only when a REAL Janma Nakshatra is supplied. `natal_moon`
    # is a Moon Rashi and is never treated as a Nakshatra.
    navtara_tara = ""
    natal_nakshatra = str(payload.get("natal_nakshatra") or "").strip()
    if natal_nakshatra and transit_nakshatra:
        try:
            from navtara.engine import classify_transit_nakshatra

            classified = classify_transit_nakshatra(natal_nakshatra, transit_nakshatra)
            navtara_tara = str((classified or {}).get("tara") or "") if classified else ""
        except Exception:
            navtara_tara = ""

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
            # House context (WHERE) modified by today's Nakshatra mode (HOW).
            "nakshatraGuidance": (
                compose_guidance(str(pattern["theme"]), transit_nakshatra, navtara_tara or None)
                if transit_nakshatra else ""
            ),
            "pattern": pattern["pattern"],
            "categories": get_daily_category_status(active_house, transit_nakshatra),
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
        "basis": "daily_moon_rashi_at_local_sunrise_with_transit_moon_as_house_1",
        # Layer 2: today's transit Nakshatra and, when a real Janma Nakshatra is
        # available, the personal Navtara tone (presentation only).
        "nakshatra": {
            "name": transit_nakshatra,
            "mode": transit_mode_line(transit_nakshatra) if transit_nakshatra else "",
            "navtara": navtara_tara,
            "navtaraTone": dict(navtara_tone(navtara_tara) or {}) if navtara_tara else {},
        },
    }
