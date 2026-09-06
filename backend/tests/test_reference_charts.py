from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest
import swisseph as swe

from chart_calculator import calculate_planets, calculate_houses, _jd_utc
from vedic_assembler import build_ascendant, assign_houses


swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)


def _utc(date_str: str, time_str: str, tz_name: str) -> datetime:
    local = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M").replace(tzinfo=ZoneInfo(tz_name))
    return local.astimezone(timezone.utc)


def test_reference_delhi_2008():
    utc = _utc("2008-05-14", "09:00", "Asia/Kolkata")
    jd = _jd_utc(utc)
    cusps, ascmc = calculate_houses(jd, 28.6139, 77.209)
    asc = build_ascendant(ascmc[0])
    planets = calculate_planets(jd)
    planet_signs = {p.name: p.sign for p in planets}
    houses = assign_houses(asc.sign, planet_signs)

    sun = next(p for p in planets if p.name == "Sun")
    moon = next(p for p in planets if p.name == "Moon")
    mars = next(p for p in planets if p.name == "Mars")

    assert 0 <= asc.longitude < 360
    assert asc.sign in {"Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"}
    assert 0 <= sun.longitude < 360
    assert 0 <= moon.longitude < 360
    assert 0 <= mars.longitude < 360
    assert 1 <= houses["Sun"] <= 12
    assert 1 <= houses["Moon"] <= 12
    assert 1 <= houses["Mars"] <= 12


def test_reference_newyork_1990():
    utc = _utc("1990-01-01", "05:00", "America/New_York")
    jd = _jd_utc(utc)
    cusps, ascmc = calculate_houses(jd, 40.7128, -74.0060)
    asc = build_ascendant(ascmc[0])
    planets = calculate_planets(jd)
    planet_signs = {p.name: p.sign for p in planets}
    houses = assign_houses(asc.sign, planet_signs)

    sun = next(p for p in planets if p.name == "Sun")

    assert 0 <= asc.longitude < 360
    assert 0 <= sun.longitude < 360
    assert 1 <= houses["Sun"] <= 12