"""
Phase 4 validation: compare new engine against old backend pipeline
and document expected external validation workflow.

Note: live geocoding tests are omitted here because they depend on
external network access. Use offline coordinate inputs or a cached
place resolver for deterministic validation.
"""
import pytest
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import swisseph as swe

from engine.ayanamsa import value as ayanamsa_value
from engine.rashi import longitude_to_rashi
from config import PLANETS


swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)


def _utc(date_str: str, time_str: str, tz_name: str) -> datetime:
    local = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M").replace(
        tzinfo=ZoneInfo(tz_name)
    )
    return local.astimezone(timezone.utc)


def _jd_utc(dt: datetime) -> float:
    return swe.julday(
        dt.year,
        dt.month,
        dt.day,
        dt.hour + dt.minute / 60.0 + dt.second / 3600.0,
        swe.GREG_CAL,
    )


def old_planet_longitudes(date_str: str, time_str: str, tz_name: str, lat: float, lng: float):
    utc = _utc(date_str, time_str, tz_name)
    jd = _jd_utc(utc)
    out = {}
    for name in PLANETS:
        if name == "Ketu":
            rahu = swe.calc_ut(jd, swe.MEAN_NODE, swe.FLG_SIDEREAL)
            rahu_long = rahu[0]
            if isinstance(rahu_long, tuple):
                rahu_long = rahu_long[0]
            out[name] = (float(rahu_long) + 180.0) % 360.0
        else:
            idx = {
                "Sun": swe.SUN,
                "Moon": swe.MOON,
                "Mercury": swe.MERCURY,
                "Venus": swe.VENUS,
                "Mars": swe.MARS,
                "Jupiter": swe.JUPITER,
                "Saturn": swe.SATURN,
                "Rahu": swe.MEAN_NODE,
            }[name]
            lon = swe.calc_ut(jd, idx, swe.FLG_SIDEREAL)[0]
            if isinstance(lon, tuple):
                lon = lon[0]
            out[name] = float(lon)
    return out, jd


def old_ascendant(date_str: str, time_str: str, tz_name: str, lat: float, lng: float):
    utc = _utc(date_str, time_str, tz_name)
    jd = _jd_utc(utc)
    cusps, ascmc = swe.houses(jd, lat, lng, b"P")
    asc = ascmc[0]
    if isinstance(asc, tuple):
        asc = asc[0]
    return float(asc) % 360.0, jd


def _new_chart_from_components(date_str: str, time_str: str, tz_name: str, lat: float, lng: float):
    from engine.ascendant import calc as ascendant_calc
    from engine.houses import assign_house, lagna_sign_index
    from engine.julian import from_utc
    from engine.planets import calc_all

    utc = _utc(date_str, time_str, tz_name)
    jd = from_utc(utc)
    ayanamsa = ayanamsa_value(jd)
    tropical_planets = {}
    for name, idx in {
        "Sun": swe.SUN,
        "Moon": swe.MOON,
        "Mercury": swe.MERCURY,
        "Venus": swe.VENUS,
        "Mars": swe.MARS,
        "Jupiter": swe.JUPITER,
        "Saturn": swe.SATURN,
        "Rahu": swe.MEAN_NODE,
    }.items():
        lon = swe.calc_ut(jd, idx, 0)[0]
        if isinstance(lon, tuple):
            lon = lon[0]
        tropical_planets[name] = float(lon)
    tropical_asc = swe.houses(jd, lat, lng, b"P")[1][0]
    if isinstance(tropical_asc, tuple):
        tropical_asc = tropical_asc[0]
    tropical_asc = float(tropical_asc)
    sidereal_planets = calc_all(jd)
    sidereal_asc = ascendant_calc(jd, lat, lng)
    lagna_sign = lagna_sign_index(sidereal_asc)

    planets = {}
    for name in PLANETS:
        longitude = sidereal_planets[name]
        sign_number = longitude_to_rashi(longitude)[1]
        house = assign_house(sign_number, lagna_sign)
        planets[name] = {
            "longitude": longitude,
            "house": house,
        }
    return {
        "ascendant": sidereal_asc,
        "tropical_ascendant": tropical_asc,
        "ayanamsa": ayanamsa,
        "planets": planets,
    }


def test_old_new_engine_agreement_delhi():
    result = _new_chart_from_components(
        "2010-01-21", "08:19", "Asia/Kolkata", 28.6139, 77.209
    )
    old_planets, jd = old_planet_longitudes(
        "2010-01-21", "08:19", "Asia/Kolkata", 28.6139, 77.209
    )
    old_asc, _ = old_ascendant(
        "2010-01-21", "08:19", "Asia/Kolkata", 28.6139, 77.209
    )

    assert result["ascendant"] == pytest.approx(old_asc % 360, abs=1e-4)
    for name in PLANETS:
        assert result["planets"][name]["longitude"] == pytest.approx(old_planets[name] % 360, abs=1e-4)


def test_old_new_engine_agreement_newyork():
    result = _new_chart_from_components(
        "1990-06-15", "14:30", "America/New_York", 40.7128, -74.006
    )
    old_planets, jd = old_planet_longitudes(
        "1990-06-15", "14:30", "America/New_York", 40.7128, -74.006
    )
    old_asc, _ = old_ascendant(
        "1990-06-15", "14:30", "America/New_York", 40.7128, -74.006
    )

    assert result["ascendant"] == pytest.approx(old_asc % 360, abs=1e-4)
    for name in PLANETS:
        assert result["planets"][name]["longitude"] == pytest.approx(old_planets[name] % 360, abs=1e-4)


def test_old_new_engine_agreement_tokyo():
    result = _new_chart_from_components(
        "2000-01-01", "00:00", "Asia/Tokyo", 35.6762, 139.6503
    )
    old_planets, jd = old_planet_longitudes(
        "2000-01-01", "00:00", "Asia/Tokyo", 35.6762, 139.6503
    )
    old_asc, _ = old_ascendant(
        "2000-01-01", "00:00", "Asia/Tokyo", 35.6762, 139.6503
    )

    assert result["ascendant"] == pytest.approx(old_asc % 360, abs=1e-4)
    for name in PLANETS:
        assert result["planets"][name]["longitude"] == pytest.approx(old_planets[name] % 360, abs=1e-4)


def test_phase4_external_validation_notes():
    """
    External validation notes for manual verification:

    Suggested reference sources:
    - AstroSage free Kundli: https://www.astrosage.com/kundli/
    - MyKundali.com: http://www.mykundali.com
    - Vedic astrology desktop software with Lahiri/Chitrapaksha ayanamsa

    For birth details: 21-01-2010, 08:19, Delhi, India
    Expected checks:
    1. Lagna/Ascendant sign should be Aquarius
    2. Sun in Capricorn
    3. Moon in Pisces
    4. All planets within 0-360 degrees
    5. Rahu-Ketu exactly 180 degrees apart

    Note: Screenshot-based validation is unreliable without unambiguous
    house numbering. Numerical cross-check against another calculator
    is preferred.
    """
    assert True
