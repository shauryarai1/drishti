"""
Minimal Vedic D1 Kundli calculator.

Birth details -> place resolution -> sidereal calculations ->
Lagna + 12 whole-sign houses + 9 planets + debug output.
"""
from __future__ import annotations

import swisseph as swe
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from config import (
    AYANAMSA,
    HOUSE_SYSTEM,
    PLANETS,
    EXTRA_PLANETS,
    ALL_PLANETS,
    RASHI_NAMES,
    RASHI_SYMBOLS,
    PLANET_ABBREVIATIONS,
)
from models import BirthData, ChartResponse, PlanetData, HouseData, AscendantData


# ---------------------------------------------------------------------------
# 1. Constants / setup
# ---------------------------------------------------------------------------

swe.set_ephe_path("")
if AYANAMSA == "lahiri":
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
else:
    raise ValueError(f"Unsupported ayanamsa: {AYANAMSA}")

_GEO = Nominatim(user_agent="kundli-minimal")
_TZ_FINDER = TimezoneFinder()

_PLANET_IDX = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mercury": swe.MERCURY,
    "Venus": swe.VENUS,
    "Mars": swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN,
    "Rahu": swe.MEAN_NODE,
    "Uranus": swe.URANUS,
    "Neptune": swe.NEPTUNE,
    "Pluto": swe.PLUTO,
}


# ---------------------------------------------------------------------------
# 2. Helpers
# ---------------------------------------------------------------------------

def _jd_utc(dt: datetime) -> float:
    if dt.tzinfo is None:
        raise ValueError("datetime must be timezone-aware")
    utc = dt.astimezone(timezone.utc)
    return swe.julday(
        utc.year,
        utc.month,
        utc.day,
        utc.hour + utc.minute / 60.0 + utc.second / 3600.0,
        swe.GREG_CAL,
    )


def _sign_from_longitude(lon: float) -> tuple[str, int, float]:
    """Return (sign_name, sign_index_0-11, degree_in_sign)."""
    if lon is None or lon < 0 or lon >= 360:
        raise ValueError(f"Longitude out of range: {lon}")
    idx = int(lon // 30) % 12
    return RASHI_NAMES[idx], idx, lon - idx * 30.0


def resolve_place(place: str) -> dict:
    try:
        location = _GEO.geocode(place, language="en", timeout=10)
    except Exception as exc:
        raise ValueError(f"Geocoding service unavailable for '{place}': {exc}") from exc
    if location is None:
        raise ValueError(f"Place could not be resolved: {place}")
    lat = float(location.latitude)
    lng = float(location.longitude)
    tz = _TZ_FINDER.timezone_at(lat=lat, lng=lng)
    if tz is None:
        raise ValueError(f"Timezone could not be resolved for: {place}")
    return {"latitude": lat, "longitude": lng, "timezone": tz}


# ---------------------------------------------------------------------------
# 3. Core calculation
# ---------------------------------------------------------------------------

def calc_planet_longitudes(jd: float) -> dict[str, float]:
    out: dict[str, float] = {}
    for name in ALL_PLANETS:
        if name == "Ketu":
            rahu = swe.calc_ut(jd, swe.MEAN_NODE, swe.FLG_SIDEREAL)
            rahu_lon = rahu[0]
            if isinstance(rahu_lon, tuple):
                rahu_lon = rahu_lon[0]
            out[name] = (float(rahu_lon) + 180.0) % 360.0
        else:
            res = swe.calc_ut(jd, _PLANET_IDX[name], swe.FLG_SIDEREAL)
            lon = res[0]
            if isinstance(lon, tuple):
                lon = lon[0]
            out[name] = float(lon)
    return out


def calc_ascendant(jd: float, lat: float, lng: float) -> float:
    cusps, ascmc = swe.houses(jd, lat, lng, b"P")
    asc = ascmc[0]
    if isinstance(asc, tuple):
        asc = asc[0]
    return float(asc)


def whole_sign_house(sign_index: int, lagna_sign_index: int) -> int:
    return ((sign_index - lagna_sign_index) % 12) + 1


# ---------------------------------------------------------------------------
# 4. Public API
# ---------------------------------------------------------------------------

def generate_chart(payload: BirthData) -> ChartResponse:
    # --- input ---
    date_str = payload.date.strip()
    time_str = payload.time.strip()
    place_str = payload.place.strip()

    # --- place ---
    place_info = resolve_place(place_str)
    local_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M").replace(
        tzinfo=ZoneInfo(place_info["timezone"])
    )
    utc_dt = local_dt.astimezone(timezone.utc)
    jd = _jd_utc(utc_dt)

    # --- ayanamsa ---
    ayanamsa = swe.get_ayanamsa(jd)
    if isinstance(ayanamsa, tuple):
        ayanamsa = ayanamsa[0]
    ayanamsa = float(ayanamsa)

    # --- sidereal longitudes ---
    sid_lons = calc_planet_longitudes(jd)
    tropical_asc = calc_ascendant(jd, place_info["latitude"], place_info["longitude"])
    sid_asc = tropical_asc - ayanamsa
    sid_asc = sid_asc % 360.0

    asc_sign, asc_sign_idx, asc_degree = _sign_from_longitude(sid_asc)

    # --- houses: whole-sign from lagna ---
    houses: list[HouseData] = []
    for i in range(12):
        sign_idx = (asc_sign_idx + i) % 12
        sign_name = RASHI_NAMES[sign_idx]
        houses.append(
            HouseData(
                number=i + 1,
                sign=sign_name,
                cusp_longitude=float(sign_idx) * 30.0,
            )
        )

    # --- planets ---
    planets: list[PlanetData] = []
    extra_planets: list[PlanetData] = []
    for name in ALL_PLANETS:
        lon = sid_lons[name]
        sign, sign_idx, degree = _sign_from_longitude(lon)
        house = whole_sign_house(sign_idx, asc_sign_idx)
        planet_data = PlanetData(
            name=name,
            longitude=round(lon, 6),
            sign=sign,
            house=house,
            degree=round(degree, 6),
            source="Swiss Ephemeris",
            status="CALCULATED",
        )
        if name in EXTRA_PLANETS:
            extra_planets.append(planet_data)
        else:
            planets.append(planet_data)

    # --- debug table ---
    planet_debug = []
    for p in planets:
        planet_debug.append(
            f"{p.name:8s} | {p.longitude:8.4f}° | {p.sign:12s} | {p.degree:6.2f}° | House {p.house}"
        )

    debug_lines = [
        "DEBUG",
        "────────────────────────",
        f"Ascendant     : {asc_sign} {asc_degree:.4f}°",
        f"Latitude      : {place_info['latitude']}",
        f"Longitude     : {place_info['longitude']}",
        f"Timezone      : {place_info['timezone']}",
        f"UTC           : {utc_dt.isoformat()}",
        f"Ayanamsa      : {ayanamsa:.6f}°",
        "",
        "Planet | Sidereal Longitude | Sign | Degree | House",
        "───────────────────────────────────────────────────────",
    ]
    debug_lines.extend(planet_debug)
    debug_lines.append("───────────────────────────────────────────────────────")
    debug_text = "\n".join(debug_lines)

    # --- validation ---
    validation_passed = True
    validation_checks = []
    try:
        validation_checks.append({"name": "birth_date_valid", "passed": True})
        datetime.strptime(date_str, "%Y-%m-%d")
    except Exception:
        validation_passed = False
        validation_checks.append({"name": "birth_date_valid", "passed": False})

    try:
        datetime.strptime(time_str, "%H:%M")
        validation_checks.append({"name": "birth_time_valid", "passed": True})
    except Exception:
        validation_passed = False
        validation_checks.append({"name": "birth_time_valid", "passed": False})

    validation_checks.append({"name": "place_resolved", "passed": True})
    validation_checks.append({"name": "planets_calculated", "passed": len(planets) == len(PLANETS)})
    validation_checks.append({"name": "houses_generated", "passed": len(houses) == 12})

    signs_in_houses = [h.sign for h in houses]
    validation_checks.append(
        {
            "name": "all_twelve_signs_present",
            "passed": sorted(signs_in_houses) == sorted(RASHI_NAMES),
        }
    )
    validation_checks.append(
        {
            "name": "planets_in_valid_houses",
            "passed": all(1 <= p.house <= 12 for p in planets),
        }
    )

    return ChartResponse(
        status="CALCULATED",
        birth={
            "date": date_str,
            "time": time_str,
            "place": place_str,
            "latitude": round(place_info["latitude"], 6),
            "longitude": round(place_info["longitude"], 6),
            "timezone": place_info["timezone"],
            "utc_datetime": utc_dt.isoformat(),
        },
        ascendant=AscendantData(
            longitude=round(sid_asc, 6),
            sign=asc_sign,
            house=1,
            degree=round(asc_degree, 6),
        ),
        planets=planets,
        houses=houses,
        validation={
            "passed": validation_passed and all(c["passed"] for c in validation_checks),
            "checks": validation_checks,
        },
        debug=debug_text,
        extra_planets=extra_planets,
    )
