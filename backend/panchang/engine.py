"""Standalone KAVACH Panchang engine.

Independent of the KAVACH application: it takes its own inputs
(date, latitude, longitude, timezone) and returns a complete Panchang.

Conventions
-----------
* Swiss Ephemeris (pyswisseph) with Lahiri / Chitrapaksha sidereal positions.
* The Panchang day runs from sunrise to the next sunrise.
* Tithi / Nakshatra / Yoga / Karana / Rashi transitions are solved
  numerically (bisection on the relevant longitude), never sampled hourly.
"""

from __future__ import annotations

from datetime import date as date_cls
from datetime import datetime, time, timedelta, timezone
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo

from . import astronomy as astro
from .choghadiya import day_choghadiya, night_choghadiya
from .constants import (
    AMANTA_MONTHS,
    CHANDRA_GOOD_HOUSES,
    DISHA_SHOOL,
    DRIK_RITU_BY_SUN_RASHI,
    DUSHTA_PART,
    KALAVELA_PART,
    KANTAKA_PART,
    KARANA_FIXED_FIRST,
    KARANA_FIXED_LAST,
    KARANA_MOVABLE,
    KULIKA_PART,
    NAKSHATRA_LORDS,
    NAKSHATRA_NAMES,
    PAKSHA_NAMES,
    RASHI_ENGLISH,
    RASHI_NAMES,
    RITU_NAMES,
    TARA_GOOD,
    TARA_NAMES,
    TITHI_NAMES,
    VARA_ENGLISH,
    VARA_NAMES,
    YAMAGHANTA_PART,
    YOGA_NAMES,
)
from .d1 import compute_d1
from .hora import compute_horas
from .muhurta import (
    auspicious_periods,
    contains,
    day_muhurta,
    inauspicious_periods,
    solar_noon,
)
from .models import PanchangRequest

TITHI_UNIT = 12.0
NAKSHATRA_UNIT = 360.0 / 27.0  # 13°20'
YOGA_UNIT = 360.0 / 27.0
KARANA_UNIT = 6.0
RASHI_UNIT = 30.0

_UNRESOLVED = "unresolved-circumpolar"


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def karana_name(index: int) -> str:
    if index == 0:
        return KARANA_FIXED_FIRST
    if index >= 57:
        return KARANA_FIXED_LAST[index - 57]
    return KARANA_MOVABLE[(index - 1) % 7]


def _local(dt: Optional[datetime], tz: ZoneInfo) -> Optional[datetime]:
    return dt.astimezone(tz) if dt else None


def _stamp(dt: Optional[datetime], tz: ZoneInfo) -> Optional[str]:
    return dt.astimezone(tz).isoformat() if dt else None


def _clock(dt: Optional[datetime], tz: ZoneInfo) -> Optional[str]:
    return dt.astimezone(tz).strftime("%H:%M") if dt else None


def _previous_crossing(angle_fn, target: float, jd_ref: float) -> Optional[float]:
    """Most recent crossing of `target` at or before jd_ref."""
    cursor = jd_ref - 45.0
    latest: Optional[float] = None
    while cursor < jd_ref:
        found = astro.crossing_time(angle_fn, target, cursor, jd_ref + 0.001)
        if found is None or found > jd_ref:
            break
        latest = found
        cursor = found + 0.05
    return latest


def _next_new_moon(jd_from: float) -> Optional[float]:
    return astro.crossing_time(astro.moon_sun_elongation, 0.0, jd_from, jd_from + 32.0)


def _next_full_moon(jd_from: float) -> Optional[float]:
    return astro.crossing_time(astro.moon_sun_elongation, 180.0, jd_from, jd_from + 32.0)


def _rashi_index(longitude: float) -> int:
    return int(longitude // RASHI_UNIT) % 12


def _element_block(
    angle_fn,
    unit: float,
    names: List[str],
    jd_ref: float,
    tz: ZoneInfo,
    search_days: float = 1.7,
) -> Dict[str, object]:
    """Current element (index + name) with numeric start/end crossings."""
    value = angle_fn(jd_ref)
    index = int(value // unit) % len(names)
    target_start = (index * unit) % 360.0
    target_end = ((index + 1) * unit) % 360.0

    start_jd = _previous_crossing(angle_fn, target_start, jd_ref)
    end_jd = astro.crossing_time(angle_fn, target_end, jd_ref, jd_ref + search_days)

    return {
        "index": index,
        "name": names[index],
        "next_name": names[(index + 1) % len(names)],
        "start": _stamp(astro.from_jd(start_jd), tz) if start_jd else None,
        "end": _stamp(astro.from_jd(end_jd), tz) if end_jd else None,
        "start_local": _clock(astro.from_jd(start_jd), tz) if start_jd else None,
        "end_local": _clock(astro.from_jd(end_jd), tz) if end_jd else None,
    }


def _karana_sequence(jd_sunrise: float, jd_next_sunrise: float, tz: ZoneInfo) -> List[dict]:
    elongation = astro.moon_sun_elongation
    index = int(elongation(jd_sunrise) // KARANA_UNIT) % 60
    start_jd = _previous_crossing(elongation, (index * KARANA_UNIT) % 360.0, jd_sunrise)
    if start_jd is None:
        start_jd = jd_sunrise

    out: List[dict] = []
    cursor = start_jd
    while cursor < jd_next_sunrise:
        next_index = (index + 1) % 60
        end_jd = astro.crossing_time(
            elongation, (next_index * KARANA_UNIT) % 360.0, cursor, cursor + 1.2
        )
        if end_jd is None:
            break
        out.append(
            {
                "name": karana_name(index),
                "is_vishti": karana_name(index) == "Vishti",
                "start": _stamp(astro.from_jd(cursor), tz),
                "end": _stamp(astro.from_jd(end_jd), tz),
                "start_local": _clock(astro.from_jd(cursor), tz),
                "end_local": _clock(astro.from_jd(end_jd), tz),
                "runs_past_sunrise": end_jd > jd_next_sunrise,
            }
        )
        index = next_index
        cursor = end_jd
    return out


def _month_names(jd_ref: float) -> Dict[str, Optional[str]]:
    """Amanta / Purnimanta lunar month names from full-moon solar rashi."""
    new_moon = _previous_crossing(astro.moon_sun_elongation, 0.0, jd_ref)
    if new_moon is None:
        return {"amanta": None, "purnimanta": None}

    full_moon = astro.crossing_time(
        astro.moon_sun_elongation, 180.0, new_moon, new_moon + 20.0
    )
    amanta = None
    if full_moon is not None:
        amanta = AMANTA_MONTHS[_rashi_index(astro.sun_longitude(full_moon))]

    next_full = _next_full_moon(jd_ref)
    purnimanta = None
    if next_full is not None:
        purnimanta = AMANTA_MONTHS[_rashi_index(astro.sun_longitude(next_full))]

    return {"amanta": amanta, "purnimanta": purnimanta}


def _chaitra_pratipada(year: int) -> Optional[float]:
    """Julian day of Chaitra Shukla Pratipada for a Gregorian year."""
    jd = astro.to_jd(datetime(year, 3, 10, tzinfo=timezone.utc))
    limit = astro.to_jd(datetime(year, 5, 5, tzinfo=timezone.utc))
    while jd < limit:
        new_moon = _next_new_moon(jd)
        if new_moon is None or new_moon > limit:
            return None
        if _rashi_index(astro.sun_longitude(new_moon)) == 0:  # Sun in Mesha
            return new_moon
        jd = new_moon + 0.5
    return None


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def _now(tz: ZoneInfo) -> datetime:
    """Current local time at the selected location.

    Single source of "now" for the engine: the current Hora card must follow the
    live local clock, and tests freeze this instead of patching datetime.
    """
    return datetime.now(tz)


def compute_panchang(request: PanchangRequest) -> dict:
    tz = ZoneInfo(request.timezone_name)
    lat, lon = request.latitude, request.longitude

    local_midnight = datetime.combine(request.on_date, time(0, 0), tzinfo=tz)
    sunrise = astro.rise_or_set(local_midnight, lat, lon, body=astro.SUN, rising=True)
    if sunrise is None:
        raise ValueError(
            f"Sunrise could not be computed for {lat}, {lon} on {request.on_date} "
            f"({_UNRESOLVED})."
        )

    sunset = astro.rise_or_set(sunrise, lat, lon, body=astro.SUN, rising=False)
    if sunset is None:
        raise ValueError(f"Sunset could not be computed for {lat}, {lon}.")
    next_sunrise = astro.next_rise_after(sunset, lat, lon, body=astro.SUN, rising=True)
    if next_sunrise is None:
        raise ValueError(f"Next sunrise could not be computed for {lat}, {lon}.")

    moonrise = astro.rise_or_set(local_midnight, lat, lon, body=astro.MOON, rising=True)
    moonset = astro.rise_or_set(local_midnight, lat, lon, body=astro.MOON, rising=False)

    weekday = sunrise.astimezone(tz).weekday()
    jd_sunrise = astro.to_jd(sunrise)
    jd_next_sunrise = astro.to_jd(next_sunrise)
    jd_limit = jd_next_sunrise + 1.7

    # --- Panchanga elements at sunrise -------------------------------------
    tithi = _element_block(astro.moon_sun_elongation, TITHI_UNIT, TITHI_NAMES, jd_sunrise, tz)
    tithi["paksha"] = PAKSHA_NAMES[tithi["index"] // 15]
    tithi["number_in_paksha"] = (tithi["index"] % 15) + 1

    nakshatra = _element_block(astro.moon_longitude, NAKSHATRA_UNIT, NAKSHATRA_NAMES, jd_sunrise, tz)
    degree_in_nakshatra = astro.moon_longitude(jd_sunrise) % NAKSHATRA_UNIT
    pada_size = NAKSHATRA_UNIT / 4
    pada_index = int(degree_in_nakshatra // pada_size)
    nakshatra["pada"] = pada_index + 1
    nakshatra["lord"] = NAKSHATRA_LORDS[nakshatra["index"]]
    pada_end_jd = astro.crossing_time(
        astro.moon_longitude,
        (nakshatra["index"] * NAKSHATRA_UNIT + (pada_index + 1) * pada_size) % 360.0,
        jd_sunrise,
        jd_sunrise + 2.0,
    )
    nakshatra["pada_end"] = _stamp(astro.from_jd(pada_end_jd), tz) if pada_end_jd else None
    nakshatra["pada_end_local"] = _clock(astro.from_jd(pada_end_jd), tz) if pada_end_jd else None

    yoga = _element_block(astro.sun_moon_sum, YOGA_UNIT, YOGA_NAMES, jd_sunrise, tz)
    karana_sequence = _karana_sequence(jd_sunrise, jd_next_sunrise, tz)

    # --- Sun / Moon rashis --------------------------------------------------
    moon_rashi_index = _rashi_index(astro.moon_longitude(jd_sunrise))
    moon_rashi = {
        "index": moon_rashi_index,
        "name": RASHI_NAMES[moon_rashi_index],
        "english": RASHI_ENGLISH[moon_rashi_index],
        "end": _stamp(
            astro.from_jd(
                astro.crossing_time(
                    astro.moon_longitude,
                    ((moon_rashi_index + 1) * RASHI_UNIT) % 360.0,
                    jd_sunrise,
                    jd_sunrise + 30.0,
                )
            )
            if astro.crossing_time(
                astro.moon_longitude,
                ((moon_rashi_index + 1) * RASHI_UNIT) % 360.0,
                jd_sunrise,
                jd_sunrise + 30.0,
            )
            else None,
            tz,
        ),
    }
    moon_rashi["start"] = (
        _stamp(astro.from_jd(_previous_crossing(astro.moon_longitude, moon_rashi_index * RASHI_UNIT, jd_sunrise)), tz)
        if _previous_crossing(astro.moon_longitude, moon_rashi_index * RASHI_UNIT, jd_sunrise)
        else None
    )

    sun_rashi_index = _rashi_index(astro.sun_longitude(jd_sunrise))
    sun_transition = astro.crossing_time(
        astro.sun_longitude, ((sun_rashi_index + 1) * RASHI_UNIT) % 360.0, jd_sunrise, jd_sunrise + 40.0
    )
    sun_rashi = {
        "index": sun_rashi_index,
        "name": RASHI_NAMES[sun_rashi_index],
        "english": RASHI_ENGLISH[sun_rashi_index],
        "sankranti": _stamp(astro.from_jd(sun_transition), tz) if sun_transition else None,
    }

    # --- Periods ------------------------------------------------------------
    inauspicious = inauspicious_periods(sunrise, sunset, weekday)

    # Extended ashubha muhurtas (day split into 15 muhurtas).
    for label, table in (
        ("Dushta Muhurta", DUSHTA_PART),
        ("Kulika", KULIKA_PART),
        ("Kantaka / Mrityu", KANTAKA_PART),
        ("Kalavela / Ardhayaam", KALAVELA_PART),
        ("Yamaghanta", YAMAGHANTA_PART),
    ):
        start, end = day_muhurta(sunrise, sunset, table[weekday])
        inauspicious.append({"name": label, "kind": "inauspicious", "start": start, "end": end})
    auspicious = auspicious_periods(sunrise, sunset, next_sunrise)

    vishti = [k for k in karana_sequence if k["is_vishti"]]
    for name, items in (("Vishti (Bhadra)", vishti),):
        for item in items:
            inauspicious.append(
                {
                    "name": name,
                    "kind": "inauspicious",
                    "start": item["start"],
                    "end": item["end"],
                    "local_start": item["start_local"],
                    "local_end": item["end_local"],
                    "note": "Vishti Karana window",
                }
            )

    # The "current" Hora must track the LIVE local clock of the selected location,
    # never the selected day's sunrise. Only the selected date that is actually
    # today has a current Hora; a past/future day has none.
    now_local = _now(tz)
    if request.at_time:
        reference_moment = datetime.combine(request.on_date, request.at_time, tzinfo=tz)
        reference_is_live = False
    elif request.on_date == now_local.date():
        reference_moment = now_local
        reference_is_live = True
    else:
        reference_moment = None
        reference_is_live = False

    def _current_hora_from_previous_day():
        """The night Hora still running when "now" is after midnight but before sunrise.

        Night Horas cross the calendar boundary, so just-after-midnight the Hora in
        progress belongs to the PREVIOUS Panchang day (its sunset -> today's
        sunrise). Same astronomy, same sequence - no second implementation.
        """
        if not (reference_is_live and reference_moment and reference_moment < sunrise):
            return None
        try:
            from datetime import timedelta

            previous_date = request.on_date - timedelta(days=1)
            previous_midnight = datetime.combine(previous_date, time(0, 0), tzinfo=tz)
            previous_sunrise = astro.rise_or_set(previous_midnight, lat, lon, body=astro.SUN, rising=True)
            if previous_sunrise is None:
                return None
            previous_sunset = astro.rise_or_set(previous_sunrise, lat, lon, body=astro.SUN, rising=False)
            if previous_sunset is None or not (previous_sunset <= reference_moment < sunrise):
                return None
            previous = compute_horas(
                previous_sunrise,
                previous_sunset,
                sunrise,
                previous_sunrise.astimezone(tz).weekday(),
                reference_moment,
            )
            return previous.get("current")
        except Exception:
            return None

    def _as_dt(value):
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            return datetime.fromisoformat(value)
        return astro.from_jd(value)

    def _serialise(periods: List[dict], local_key: str) -> List[dict]:
        out = []
        for period in sorted(periods, key=lambda p: _as_dt(p["start"])):
            start = period["start"]
            end = period["end"]
            start_dt = _as_dt(start)
            end_dt = _as_dt(end)
            out.append(
                {
                    "name": period["name"],
                    "kind": period["kind"],
                    "start": _stamp(start_dt, tz),
                    "end": _stamp(end_dt, tz),
                    local_key: _clock(start_dt, tz),
                    local_key.replace("local_start", "local_end"): _clock(end_dt, tz),
                    "note": period.get("note", ""),
                    "active": bool(reference_moment and start_dt <= reference_moment < end_dt),
                }
            )
        return out

    day_duration = sunset - sunrise
    night_duration = next_sunrise - sunset

    # --- Sunrise D1 chart + planetary positions -----------------------------
    d1 = compute_d1(sunrise, lat, lon)
    d1["instant"] = _stamp(sunrise, tz)
    d1["instant_local"] = _clock(sunrise, tz)

    # --- Hora --------------------------------------------------------------
    hora = compute_horas(sunrise, sunset, next_sunrise, weekday, reference_moment)
    preceding = _current_hora_from_previous_day()
    if preceding is not None:
        hora["current"] = preceding
    hora = _serialise_hora(hora, tz)
    hora["current_is_live"] = reference_is_live

    # --- Chandrabalam / Tarabalam ------------------------------------------
    moon_nakshatra_index = nakshatra["index"]
    moon_sign_index = moon_rashi_index
    tarabalam = []
    for janma in range(27):
        tara_index = (moon_nakshatra_index - janma) % 9
        tarabalam.append(
            {
                "nakshatra": NAKSHATRA_NAMES[janma],
                "tara": TARA_NAMES[tara_index],
                "good": tara_index in TARA_GOOD,
            }
        )
    chandrabalam = []
    for janma_sign in range(12):
        house = ((moon_sign_index - janma_sign) % 12) + 1
        chandrabalam.append(
            {
                "rashi": RASHI_NAMES[janma_sign],
                "house_from_janma": house,
                "good": house in CHANDRA_GOOD_HOUSES,
            }
        )

    result = {
        "engine": {
            "name": "KAVACH Panchang (standalone prototype)",
            "ayanamsa": "Lahiri / Chitrapaksha",
            "ephemeris": "Swiss Ephemeris (pyswisseph)",
            "panchang_day": "sunrise to next sunrise",
        },
        "request": {
            "date": request.on_date.isoformat(),
            "timezone": request.timezone_name,
            "at_time": request.at_time.isoformat() if request.at_time else None,
            "reference": _stamp(reference_moment, tz) if reference_moment else None,
            "reference_is_live": reference_is_live,
        },
        "location": {
            "label": request.label,
            "latitude": lat,
            "longitude": lon,
        },
        "day": {
            "date": sunrise.astimezone(tz).date().isoformat(),
            "weekday": VARA_ENGLISH[weekday],
            "vara": VARA_NAMES[weekday],
            "weekday_index": weekday,
            "is_reference_before_sunrise": bool(reference_moment and reference_moment < sunrise),
        },
        "sun_moon": {
            "sunrise": _stamp(sunrise, tz),
            "sunrise_local": _clock(sunrise, tz),
            "sunset": _stamp(sunset, tz),
            "sunset_local": _clock(sunset, tz),
            "next_sunrise": _stamp(next_sunrise, tz),
            "next_sunrise_local": _clock(next_sunrise, tz),
            "moonrise": _stamp(moonrise, tz),
            "moonrise_local": _clock(moonrise, tz),
            "moonset": _stamp(moonset, tz),
            "moonset_local": _clock(moonset, tz),
            "solar_noon": _stamp(solar_noon(sunrise, sunset), tz),
            "solar_noon_local": _clock(solar_noon(sunrise, sunset), tz),
            "day_duration_minutes": round(day_duration.total_seconds() / 60.0, 2),
            "night_duration_minutes": round(night_duration.total_seconds() / 60.0, 2),
        },
        "panchanga": {
            "tithi": tithi,
            "nakshatra": nakshatra,
            "yoga": yoga,
            "karana": {
                "current": karana_sequence[0]["name"] if karana_sequence else None,
                "sequence": karana_sequence,
            },
            "vara": {
                "index": weekday,
                "name": VARA_NAMES[weekday],
                "english": VARA_ENGLISH[weekday],
            },
        },
        "sun_moon_rashi": {"moon": moon_rashi, "sun": sun_rashi},
        "d1": d1,
        "hora": hora,
        "balam": {
            "tarabalam": tarabalam,
            "chandrabalam": chandrabalam,
            "good_tarabalam": [i["nakshatra"] for i in tarabalam if i["good"]],
            "good_chandrabalam": [i["rashi"] for i in chandrabalam if i["good"]],
        },
        "auspicious": _serialise(auspicious, "local_start"),
        "inauspicious": _serialise(inauspicious, "local_start"),
        "choghadiya": {
            "day": _serialise_choghadiya(day_choghadiya(sunrise, sunset, weekday), tz),
            "night": _serialise_choghadiya(night_choghadiya(sunset, next_sunrise, weekday), tz),
        },
        "calendar": _calendar_block(jd_sunrise, weekday),
        "notes": [
            "Dur Muhurta weekday mapping is verified for Sunday only; other weekdays follow the classical table and need reference validation.",
            "Night Choghadiya follows the common convention of continuing from the 5th day segment; needs reference validation.",
            "Godhuli Muhurta duration is derived from the night length; needs reference validation.",
            "Panchaka, Varjyam, Amrit Kalam, Chandra Vasa and Samvatsara details are not implemented yet.",
        ],
    }
    return result


def _serialise_choghadiya(segments: List[dict], tz: ZoneInfo) -> List[dict]:
    return [
        {
            "name": segment["name"],
            "classification": segment["classification"],
            "start": _stamp(segment["start"], tz),
            "end": _stamp(segment["end"], tz),
            "local_start": _clock(segment["start"], tz),
            "local_end": _clock(segment["end"], tz),
        }
        for segment in segments
    ]


def _calendar_block(jd_sunrise: float, weekday: int) -> dict:
    months = _month_names(jd_sunrise)
    sun_rashi = _rashi_index(astro.sun_longitude(jd_sunrise))
    tropical_rashi = _rashi_index(astro.sun_longitude_tropical(jd_sunrise))

    jd_dt = astro.from_jd(jd_sunrise)
    gregorian_year = jd_dt.year
    chaitra = _chaitra_pratipada(gregorian_year)
    if chaitra is not None and jd_sunrise < chaitra:
        base_year = gregorian_year - 1
    else:
        base_year = gregorian_year

    return {
        "amanta_month": months["amanta"],
        "purnimanta_month": months["purnimanta"],
        "vikram_samvat": base_year + 57,
        "shaka_samvat": base_year - 78,
        # Both conventions are exposed rather than silently choosing one.
        "ritu_vedic": RITU_NAMES[sun_rashi // 2],
        "ritu_drik": DRIK_RITU_BY_SUN_RASHI[tropical_rashi],
        "ayana_vedic": "Uttarayana" if sun_rashi in (9, 10, 11, 0, 1, 2) else "Dakshinayana",
        "ayana_drik": "Uttarayana" if tropical_rashi in (9, 10, 11, 0, 1, 2) else "Dakshinayana",
        "disha_shool": DISHA_SHOOL[weekday],
        "sun_rashi": RASHI_NAMES[sun_rashi],
        "sun_rashi_tropical": RASHI_NAMES[tropical_rashi],
    }


def _serialise_hora(hora: dict, tz: ZoneInfo) -> dict:
    def rows(items):
        return [
            {
                **item,
                "start": _stamp(item["start"], tz),
                "end": _stamp(item["end"], tz),
                "start_local": _clock(item["start"], tz),
                "end_local": _clock(item["end"], tz),
            }
            for item in items
        ]

    current = hora["current"]
    upcoming = hora["next"]
    return {
        "weekday_lord": hora["weekday_lord"],
        "day_hora_minutes": hora["day_hora_minutes"],
        "night_hora_minutes": hora["night_hora_minutes"],
        "day": rows(hora["day"]),
        "night": rows(hora["night"]),
        "current": (
            {
                **current,
                "start": _stamp(current["start"], tz),
                "end": _stamp(current["end"], tz),
                "start_local": _clock(current["start"], tz),
                "end_local": _clock(current["end"], tz),
            }
            if current
            else None
        ),
        "next": (
            {
                **upcoming,
                "start": _stamp(upcoming["start"], tz),
                "end": _stamp(upcoming["end"], tz),
                "start_local": _clock(upcoming["start"], tz),
                "end_local": _clock(upcoming["end"], tz),
            }
            if upcoming
            else None
        ),
    }
