from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import swisseph as swe

from config import AYANAMSA, HOUSE_SYSTEM, PLANETS, SWISS_EPHEMERIS_PATH
from models import PlanetData


swe.set_ephe_path(SWISS_EPHEMERIS_PATH)

if AYANAMSA == "lahiri":
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
else:
    raise ValueError(f"Unsupported ayanamsa: {AYANAMSA}")


def _jd_utc(dt: datetime) -> float:
    if dt.tzinfo is None:
        raise ValueError("datetime must be timezone-aware")
    utc_dt = dt.astimezone(timezone.utc)
    return swe.julday(
        utc_dt.year,
        utc_dt.month,
        utc_dt.day,
        utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0,
        swe.GREG_CAL,
    )


def _planet_index(name: str) -> int:
    mapping = {
        "Sun": swe.SUN,
        "Moon": swe.MOON,
        "Mercury": swe.MERCURY,
        "Venus": swe.VENUS,
        "Mars": swe.MARS,
        "Jupiter": swe.JUPITER,
        "Saturn": swe.SATURN,
        "Rahu": swe.MEAN_NODE,
        "Ketu": None,
    }
    return mapping[name]


def _calc_planet(jd_utc: float, name: str) -> tuple:
    idx = _planet_index(name)
    if name == "Ketu":
        rahu = swe.calc_ut(jd_utc, swe.MEAN_NODE, swe.FLG_SIDEREAL)
        rahu_long = rahu[0]
        if isinstance(rahu_long, tuple):
            rahu_long = rahu_long[0]
        ketu_long = (float(rahu_long) + 180.0) % 360.0
        return ketu_long, "CALCULATED"

    result = swe.calc_ut(jd_utc, idx, swe.FLG_SIDEREAL)
    longitude = result[0]
    if isinstance(longitude, tuple):
        longitude = longitude[0]
    return float(longitude), "CALCULATED"


def calculate_planets(jd_utc: float) -> list[PlanetData]:
    from rashi import longitude_to_rashi
    from nakshatra import longitude_to_nakshatra

    planets = []
    for name in PLANETS:
        longitude, status = _calc_planet(jd_utc, name)
        sign, _, degree = longitude_to_rashi(longitude)
        nakshatra, pada = longitude_to_nakshatra(longitude)
        planets.append(
            PlanetData(
                name=name,
                longitude=round(longitude, 6),
                sign=sign,
                house=0,
                degree=round(degree, 6),
                nakshatra=nakshatra,
                pada=pada,
                status=status,
            )
        )
    return planets


def calculate_houses(jd_utc: float, lat: float, lng: float) -> tuple:
    house_system = HOUSE_SYSTEM[0].upper()
    cusps, ascmc = swe.houses(jd_utc, lat, lng, house_system.encode())
    return cusps, ascmc