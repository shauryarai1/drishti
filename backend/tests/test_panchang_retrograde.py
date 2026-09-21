"""Panchang D1 retrograde consistency with the Kundli natal pipeline.

Fixture: 2010-01-21 08:19 Delhi, India (Mars Rx in Cancer, Saturn Rx in Virgo).
No mocked booleans: values come from the real Swiss Ephemeris path.
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

import main
from calculator import calc_planet_longitudes, calc_planet_retrograde
from panchang.astronomy import to_jd
from panchang.moment import calculate_panchang_moment

TZ = ZoneInfo("Asia/Kolkata")
MOMENT = datetime(2010, 1, 21, 8, 19, tzinfo=TZ)
DELHI = (28.6139, 77.209, "Asia/Kolkata", "Delhi, India")
ORDINARY = ("Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn")
NODES = ("Rahu", "Ketu")


def _positions() -> dict:
    moment = calculate_panchang_moment(MOMENT, *DELHI)
    return {position["planet"]: position for position in moment["chart"]["positions"]}


def test_panchang_exposes_ordinary_planet_retrograde_status():
    positions = _positions()
    for planet in ORDINARY:
        assert isinstance(positions[planet].get("retrograde"), bool), planet


def test_mars_is_retrograde_in_the_panchang_output():
    assert _positions()["Mars"]["retrograde"] is True


def test_saturn_is_retrograde_in_the_panchang_output():
    assert _positions()["Saturn"]["retrograde"] is True


@pytest.mark.parametrize("planet", ["Sun", "Moon", "Mercury", "Venus", "Jupiter"])
def test_direct_ordinary_planets_remain_direct(planet):
    assert _positions()[planet]["retrograde"] is False


def test_panchang_matches_the_calculator_retrograde_truth():
    speeds = calc_planet_retrograde(to_jd(MOMENT))
    positions = _positions()
    for planet in ORDINARY:
        assert positions[planet]["retrograde"] is speeds[planet], planet


def test_longitudes_do_not_drift_between_panchang_and_calculator():
    jd = to_jd(MOMENT)
    reference = calc_planet_longitudes(jd)
    positions = _positions()
    for planet in ORDINARY:
        assert positions[planet]["longitude"] == pytest.approx(reference[planet], abs=1e-6), planet


def test_rashi_nakshatra_and_pada_are_unaffected():
    positions = _positions()
    # Panchang D1 labels rashis in Sanskrit (Makara) while the Kundli payload uses
    # English (Capricorn): the underlying sign is the same, only the label differs.
    assert positions["Sun"]["sign"] == "Makara"
    assert positions["Moon"]["sign"] == "Meena"
    assert positions["Mars"]["sign"] == "Karka" and positions["Mars"]["house"] == 7
    assert positions["Saturn"]["sign"] == "Kanya"
    for planet in ORDINARY:
        assert positions[planet]["nakshatra"]
        assert 1 <= positions[planet]["pada"] <= 4


def test_kundli_and_panchang_now_agree():
    client = TestClient(main.app)
    body = client.post("/api/kundli", json={
        "date": "2010-01-21", "time": "08:19", "place": "Delhi, India",
        "latitude": 28.6139, "longitude": 77.209, "timezone": "Asia/Kolkata"}).json()
    kundli = {planet["planet"]: planet["motion"] for planet in body["planets"]}
    positions = _positions()
    for planet in ORDINARY:
        expected = "Retrograde" if positions[planet]["retrograde"] else "Direct"
        assert kundli[planet] == expected, planet


def test_nodes_are_not_treated_as_ordinary_retrograde_planets():
    positions = _positions()
    for node in NODES:
        assert node in positions
    retro_flags = calc_planet_retrograde(to_jd(MOMENT))
    for node in NODES:
        assert node not in retro_flags            # excluded from the generic rule
    # and BNN still never builds previous-sign layers for nodes
    client = TestClient(main.app)
    body = client.post("/api/kundli", json={
        "date": "2010-01-21", "time": "08:19", "place": "Delhi, India",
        "latitude": 28.6139, "longitude": 77.209, "timezone": "Asia/Kolkata"}).json()
    layers = body["analysis"]["bnnConnections"]["retrogradeLayers"]
    assert "Rahu" not in layers and "Ketu" not in layers
    node_layers = body["analysis"]["bnnConnections"]["nodeLayers"]
    assert {"Rahu", "Ketu"} <= set(node_layers)
    assert node_layers["Rahu"]["direct"] and node_layers["Rahu"]["operational"]
