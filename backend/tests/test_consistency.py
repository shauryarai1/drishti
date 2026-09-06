import swisseph as swe
import pytest

from models import BirthDetails
from engine.ayanamsa import init_sidereal, value as ayanamsa_value
from engine.ascendant import calc as ascendant_calc
from engine.chart import build_chart
from engine.houses import assign_house, lagna_sign_index
from engine.julian import from_utc
from engine.planets import calc_all
from engine.rashi import longitude_to_nakshatra, longitude_to_rashi
from config import PLANETS, RASHI_NAMES


init_sidereal()


_PLACE_INFO = {
    "Delhi, India": {"latitude": 28.6139, "longitude": 77.2090, "timezone": "Asia/Kolkata"},
    "New York, USA": {"latitude": 40.7128, "longitude": -74.0060, "timezone": "America/New_York"},
    "Tokyo, Japan": {"latitude": 35.6762, "longitude": 139.6503, "timezone": "Asia/Tokyo"},
}


def _chart(birth: BirthDetails):
    place_info = _PLACE_INFO.get(birth.place)
    if place_info is None:
        raise pytest.skip(f"no cached place info for {birth.place}")
    return build_chart(birth, place_info=place_info)


def test_build_chart_basic():
    birth = BirthDetails(date="2010-01-21", time="08:19", place="Delhi, India")
    chart = _chart(birth)
    assert chart.status == "CALCULATED"
    assert chart.ascendant is not None
    assert len(chart.planets) == len(PLANETS)


def test_planets_count_and_names():
    birth = BirthDetails(date="1990-06-15", time="14:30", place="New York, USA")
    chart = _chart(birth)
    names = [p.name for p in chart.planets]
    assert sorted(names) == sorted(PLANETS)


def test_longitudes_in_valid_range():
    birth = BirthDetails(date="2000-01-01", time="00:00", place="Tokyo, Japan")
    chart = _chart(birth)
    for p in chart.planets:
        assert 0 <= p.longitude < 360


def test_all_houses_between_1_and_12():
    birth = BirthDetails(date="2000-01-01", time="00:00", place="Tokyo, Japan")
    chart = _chart(birth)
    for p in chart.planets:
        assert 1 <= p.house <= 12


def test_exactly_twelve_houses_from_lagna():
    birth = BirthDetails(date="2000-01-01", time="00:00", place="Tokyo, Japan")
    chart = _chart(birth)
    lagna_number = chart.ascendant["house"]
    assert lagna_number == 1
    assert chart.houses is not None and len(chart.houses) == 12
    house_numbers = sorted({h["number"] for h in chart.houses})
    assert house_numbers == list(range(1, 13))


def test_rahu_ketu_exactly_180_apart():
    birth = BirthDetails(date="2000-01-01", time="00:00", place="Tokyo, Japan")
    chart = _chart(birth)
    planets = {p.name: p for p in chart.planets}
    diff = abs(planets["Rahu"].longitude - planets["Ketu"].longitude) % 360
    assert diff == pytest.approx(180.0, abs=1e-6)


def test_whole_sign_house_formula():
    birth = BirthDetails(date="2010-01-21", time="08:19", place="Delhi, India")
    chart = _chart(birth)
    planets = {p.name: p for p in chart.planets}
    _, lagna_sign_number, _ = longitude_to_rashi(chart.ascendant["longitude"])
    for name in PLANETS:
        sign_number = longitude_to_rashi(planets[name].longitude)[1]
        expected = ((sign_number - lagna_sign_number) % 12) + 1
        assert planets[name].house == expected


def test_birth_time_changes_chart():
    birth1 = BirthDetails(date="2010-01-21", time="08:19", place="Delhi, India")
    birth2 = BirthDetails(date="2010-01-21", time="08:20", place="Delhi, India")
    chart1 = _chart(birth1)
    chart2 = _chart(birth2)
    asc1 = chart1.ascendant["longitude"]
    asc2 = chart2.ascendant["longitude"]
    assert asc1 != pytest.approx(asc2, abs=1e-3)


def test_location_change_changes_chart():
    birth1 = BirthDetails(date="2010-01-21", time="08:19", place="Delhi, India")
    birth2 = BirthDetails(date="2010-01-21", time="08:19", place="New York, USA")
    chart1 = _chart(birth1)
    chart2 = _chart(birth2)
    asc1 = chart1.ascendant["longitude"]
    asc2 = chart2.ascendant["longitude"]
    assert asc1 != pytest.approx(asc2, abs=1e-3)


def test_sequential_houses_from_lagna():
    birth = BirthDetails(date="2010-01-21", time="08:19", place="Delhi, India")
    chart = _chart(birth)
    lagna_number = chart.ascendant["house"]
    assert lagna_number == 1
    lagna_sign_number = chart.debug["lagna_sign_number"]
    for p in chart.planets:
        sign_number = longitude_to_rashi(p.longitude)[1]
        expected = ((sign_number - lagna_sign_number) % 12) + 1
        assert p.house == expected


def test_planet_sign_derived_from_longitude():
    birth = BirthDetails(date="2010-01-21", time="08:19", place="Delhi, India")
    chart = _chart(birth)
    for p in chart.planets:
        expected_sign, expected_number, _ = longitude_to_rashi(p.longitude)
        assert p.sign == expected_sign
        assert p.degree == pytest.approx(p.longitude - (expected_number - 1) * 30, abs=1e-6)


def test_nakshatra_derived_from_longitude():
    birth = BirthDetails(date="2010-01-21", time="08:19", place="Delhi, India")
    chart = _chart(birth)
    for p in chart.planets:
        expected_nakshatra, expected_pada = longitude_to_nakshatra(p.longitude)
        assert p.nakshatra == expected_nakshatra
        assert p.pada == expected_pada


def test_ascendant_sign_matches_lagna_sign():
    birth = BirthDetails(date="2010-01-21", time="08:19", place="Delhi, India")
    chart = _chart(birth)
    asc = chart.ascendant
    assert asc["sign"] == chart.debug["lagna_sign"]
    assert asc["degree"] == pytest.approx(chart.debug["lagna_degree"], abs=1e-6)


def test_lagna_is_house_1():
    birth = BirthDetails(date="2010-01-21", time="08:19", place="Delhi, India")
    chart = _chart(birth)
    assert chart.ascendant["house"] == 1


def test_sidereal_longitude_formula():
    jd = swe.julday(2010, 1, 21, 2.816667, swe.GREG_CAL)
    tropical = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL)[0]
    if isinstance(tropical, tuple):
        tropical = tropical[0]
    chart = _chart(BirthDetails(date="2010-01-21", time="08:19", place="Delhi, India"))
    planets = {p.name: p for p in chart.planets}
    assert planets["Sun"].longitude == pytest.approx(float(tropical) % 360, abs=1e-4)


def test_sidereal_ascendant_formula():
    birth = BirthDetails(date="2010-01-21", time="08:19", place="Delhi, India")
    chart = _chart(birth)
    assert chart.ascendant["longitude"] == pytest.approx(chart.debug["sidereal_ascendant"], abs=1e-6)
    ayanamsa = chart.debug["ayanamsa"]["value"]
    assert chart.debug["tropical_ascendant"] == pytest.approx(
        (chart.debug["sidereal_ascendant"] + ayanamsa) % 360, abs=1e-4
    )


def test_houses_contain_all_twelve_signs_exactly_once():
    birth = BirthDetails(date="2010-01-21", time="08:19", place="Delhi, India")
    chart = _chart(birth)
    signs = [h["sign"] for h in chart.houses]
    assert len(signs) == 12
    assert sorted(signs) == sorted(RASHI_NAMES)


def test_houses_are_sequential_from_lagna():
    birth = BirthDetails(date="2010-01-21", time="08:19", place="Delhi, India")
    chart = _chart(birth)
    lagna_index = RASHI_NAMES.index(chart.ascendant["sign"])
    for i, h in enumerate(chart.houses):
        expected_sign = RASHI_NAMES[(lagna_index + i) % 12]
        assert h["sign"] == expected_sign


def test_whole_sign_houses_for_multiple_lagnas():
    test_cases = [
        ("Delhi, India", "2010-01-21", "08:19"),
        ("New York, USA", "1990-06-15", "14:30"),
        ("Tokyo, Japan", "2000-01-01", "00:00"),
    ]
    for place, date, time in test_cases:
        birth = BirthDetails(date=date, time=time, place=place)
        chart = _chart(birth)
        signs = [h["sign"] for h in chart.houses]
        assert len(signs) == 12
        assert sorted(signs) == sorted(RASHI_NAMES)
        lagna_index = RASHI_NAMES.index(chart.ascendant["sign"])
        for i, sign in enumerate(signs):
            assert sign == RASHI_NAMES[(lagna_index + i) % 12]
