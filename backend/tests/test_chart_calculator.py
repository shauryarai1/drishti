from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest
import swisseph as swe

from chart_calculator import calculate_planets, calculate_houses, _jd_utc


swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)


def test_jd_utc():
    dt = datetime(1990, 1, 15, 9, 0, tzinfo=timezone.utc)
    jd = _jd_utc(dt)
    assert jd > 2440000 and jd < 2460000


def test_sun_position_basic():
    dt = datetime(2008, 5, 14, 9, 0, tzinfo=timezone.utc)
    jd = _jd_utc(dt)
    planets = calculate_planets(jd)
    sun = next(p for p in planets if p.name == "Sun")
    assert 0 <= sun.longitude < 360
    assert sun.sign in {
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
    }
    assert sun.status == "CALCULATED"


def test_moon_position_basic():
    dt = datetime(2008, 5, 14, 9, 0, tzinfo=timezone.utc)
    jd = _jd_utc(dt)
    planets = calculate_planets(jd)
    moon = next(p for p in planets if p.name == "Moon")
    assert 0 <= moon.longitude < 360


def test_ascendant_and_houses_basic():
    dt = datetime(2008, 5, 14, 9, 0, tzinfo=timezone.utc)
    jd = _jd_utc(dt)
    cusps, ascmc = calculate_houses(jd, 28.6139, 77.209)
    assert 0 <= ascmc[0] < 360