"""Production-path retrograde regression tests (real Swiss Ephemeris speeds)."""

from __future__ import annotations

from datetime import datetime, time
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

import main
from calculator import (
    calc_planet_longitudes,
    calc_planet_longitudes_and_speed,
    calc_planet_retrograde,
    generate_chart,
)
from kundli.analysis import build_analysis
from kundli.analysis.bnn import retrograde_layers
from models import BirthData

TZ = ZoneInfo("Asia/Kolkata")
FIXTURE = {"name": "Fixture Native", "date": "2010-01-21", "time": "08:19",
           "place": "Delhi, India", "latitude": 28.6139, "longitude": 77.209,
           "timezone": "Asia/Kolkata"}
ORDINARY = ("Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn")
EXPECTED_LAGNA = "Capricorn"


def _jd() -> float:
    from panchang import astronomy

    return astronomy.to_jd(datetime(2010, 1, 21, 8, 19, tzinfo=TZ))


def _birth() -> BirthData:
    return BirthData(date=FIXTURE["date"], time=FIXTURE["time"], place=FIXTURE["place"],
                     latitude=FIXTURE["latitude"], longitude=FIXTURE["longitude"])


def _api_payload() -> dict:
    response = TestClient(main.app).post("/api/kundli", json={
        "name": FIXTURE["name"], "date": FIXTURE["date"], "time": FIXTURE["time"],
        "place": FIXTURE["place"], "latitude": FIXTURE["latitude"],
        "longitude": FIXTURE["longitude"], "timezone": FIXTURE["timezone"]})
    assert response.status_code == 200
    return response.json()


# --- A: speed availability ------------------------------------------------
def test_speed_is_available_for_every_ordinary_planet():
    speeds = calc_planet_longitudes_and_speed(_jd())
    for planet in ORDINARY:
        longitude, speed = speeds[planet]
        assert isinstance(longitude, float) and isinstance(speed, float)
        assert speed != 0.0


def test_retrograde_flag_is_derived_from_speed():
    speeds = calc_planet_longitudes_and_speed(_jd())
    flags = calc_planet_retrograde(_jd())
    for planet in ORDINARY:
        _longitude, speed = speeds[planet]
        assert flags[planet] is (speed < 0), planet


# --- B/C: the rule itself -------------------------------------------------
def test_negative_speed_means_retrograde():
    speeds = calc_planet_longitudes_and_speed(_jd())
    retro = [planet for planet in ORDINARY if speeds[planet][1] < 0]
    assert retro, "the fixture is expected to contain at least one retrograde planet"
    flags = calc_planet_retrograde(_jd())
    for planet in retro:
        assert flags[planet] is True


def test_non_negative_speed_means_direct():
    speeds = calc_planet_longitudes_and_speed(_jd())
    flags = calc_planet_retrograde(_jd())
    for planet in ORDINARY:
        if speeds[planet][1] >= 0:
            assert flags[planet] is False


# --- D: longitudes unchanged by adding the speed flag ---------------------
def test_longitudes_are_unchanged_by_requesting_speed():
    plain = calc_planet_longitudes(_jd())
    with_speed = calc_planet_longitudes_and_speed(_jd())
    for planet, longitude in plain.items():
        # FLG_SPEED must not change positions; Swiss Ephemeris may differ only
        # at floating-point level, so allow a tiny documented tolerance.
        assert with_speed[planet][0] == pytest.approx(longitude, abs=1e-6), planet


# --- E: no hardcoded date table -------------------------------------------
def test_no_hardcoded_retrograde_table():
    import pathlib
    import re

    source = pathlib.Path(__file__).resolve().parents[1] / "calculator.py"
    text = source.read_text(encoding="utf-8").lower()
    for banned in ("retrograde_dates", "retro_table", "2010-01-21", "known_retro"):
        assert banned not in text
    assert "flg_speed" in text


# --- nodes never get the generic rule ------------------------------------
def test_nodes_never_receive_previous_sign_layers():
    chart = generate_chart(_birth())
    placements = {planet.name: {"rashi": planet.sign, "house": planet.house}
                  for planet in chart.planets}
    assert retrograde_layers(placements, ["Rahu", "Ketu"]) == {}
    flags = calc_planet_retrograde(_jd())
    assert "Rahu" not in flags and "Ketu" not in flags


# --- propagation: natal object -> API -> analysis -------------------------
def test_api_returns_correct_retrograde_boolean():
    body = _api_payload()
    speeds = calc_planet_longitudes_and_speed(_jd())
    by_name = {planet["planet"]: planet for planet in body["planets"]}
    for planet in ORDINARY:
        expected = "Retrograde" if speeds[planet][1] < 0 else "Direct"
        assert by_name[planet]["motion"] == expected, planet
    for node in ("Rahu", "Ketu"):
        assert by_name[node]["motion"] == "Node"


def test_build_analysis_receives_retrograde_and_builds_both_layers():
    body = _api_payload()
    retro_planets = [planet["planet"] for planet in body["planets"]
                     if planet["motion"] == "Retrograde"]
    assert retro_planets, "expected the fixture to have a retrograde planet"

    analysis = build_analysis(body["chart"])
    for planet in retro_planets:
        layers = analysis["bnnConnections"]["retrogradeLayers"][planet]
        assert "ACTUAL_POSITION" in layers
        assert "RETRO_PREVIOUS_POSITION" in layers
        # the actual layer must use the planet's real rashi
        truth = next(item for item in body["planets"] if item["planet"] == planet)
        assert all(row["referenceRashi"] == truth["rashi"] for row in layers["ACTUAL_POSITION"])
        # the previous layer must use the immediately preceding rashi (wraps Aries -> Pisces)
        from kundli.analysis.bnn import previous_rashi
        assert all(row["referenceRashi"] == previous_rashi(truth["rashi"])
                   for row in layers["RETRO_PREVIOUS_POSITION"])


def test_strength_receives_retrograde_evidence_without_grading():
    body = _api_payload()
    retro_planets = [planet["planet"] for planet in body["planets"]
                     if planet["motion"] == "Retrograde"]
    analysis = build_analysis(body["chart"])
    for planet in retro_planets:
        evidence = analysis["strength"]["planets"][planet]
        assert evidence["retrogradeLayers"]
        assert set(evidence["retrogradeLayers"]) == {"ACTUAL_POSITION", "RETRO_PREVIOUS_POSITION"}
        assert evidence["classification"] is None
        assert evidence["classificationStatus"] == "AWAITING_OWNER_GRADING_RULE"
    assert analysis["strength"]["weights"] is None


def test_chart_positions_are_not_changed_by_the_fix():
    body = _api_payload()
    assert body["chart"]["ascendant"]["rashi"] == EXPECTED_LAGNA
    by_name = {planet["planet"]: planet for planet in body["planets"]}
    assert by_name["Sun"]["rashi"] == "Capricorn"
    assert by_name["Moon"]["rashi"] == "Pisces"
    assert by_name["Mars"]["house"] == 7 and by_name["Mars"]["rashi"] == "Cancer"
    for planet in body["planets"]:
        assert planet["nakshatra"] and planet["pada"] is not None
