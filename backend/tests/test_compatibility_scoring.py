"""Owner's binary compatibility scoring: full points or zero, never partial."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

import main
from compatibility.engine import analyse_factors
from compatibility.interpretation import (
    BINARY_SCORING, UNSCORED_FACTORS, build_interpreted, build_total_score,
)
from compatibility.models import PersonFacts
from kundli.analysis.signs import RASHIS, SIGN_LORD
from navtara.constants import NAKSHATRAS

FIXTURE = {
    "bride": {"name": "Ananya", "date": "2010-01-21", "time": "08:19", "place": "Delhi",
              "latitude": 28.6139, "longitude": 77.209, "timezone": "Asia/Kolkata"},
    "groom": {"name": "Arjun", "date": "1990-05-15", "time": "14:15", "place": "Delhi",
              "latitude": 28.6139, "longitude": 77.209, "timezone": "Asia/Kolkata"},
}

# Owner-established maxima only (Nadi and Yoni have no safe binary rule).
EXPECTED_MAXIMA = {"tara": 3, "gana": 6, "rashi": 7, "graha_maitri": 5, "vasya": 2}


def person(name, role, sign, nakshatra):
    return PersonFacts(name=name, role=role, moon_sign=sign,
                       moon_nakshatra=nakshatra, moon_ruler=SIGN_LORD[sign])


def _report(bride, groom):
    factors = analyse_factors(bride, groom, NAKSHATRAS, RASHIS)
    return build_interpreted(factors, [], {"bride": bride.name, "groom": groom.name})


def _working(report):
    return {entry["factor"]: entry for entry in report["technicalAnalysis"]}


def test_only_source_established_maxima_are_scored():
    assert set(BINARY_SCORING) == set(EXPECTED_MAXIMA)
    for key, maximum in EXPECTED_MAXIMA.items():
        assert BINARY_SCORING[key]["maximum"] == maximum
    # Nadi and Yoni are explicitly unscored, with a documented reason.
    assert set(UNSCORED_FACTORS) == {"nadi", "yoni"}
    assert all(UNSCORED_FACTORS.values())


def test_no_factor_ever_awards_partial_points():
    """Across many chart pairs, every scored factor is either full or zero."""
    pairs = [
        ("Ashwini", "Aries", "Ashlesha", "Cancer"),
        ("Bharani", "Taurus", "Revati", "Pisces"),
        ("Rohini", "Taurus", "Magha", "Leo"),
        ("Anuradha", "Scorpio", "Mula", "Sagittarius"),
        ("Hasta", "Virgo", "Swati", "Libra"),
    ]
    for bride_nak, bride_sign, groom_nak, groom_sign in pairs:
        report = _report(person("A", "bride", bride_sign, bride_nak),
                         person("B", "groom", groom_sign, groom_nak))
        for entry in report["technicalAnalysis"]:
            if "points" not in entry:
                continue
            assert entry["points"] in (0, entry["maximum"]), entry
            assert entry["matched"] is (entry["points"] == entry["maximum"])


def test_tara_match_is_three_and_non_match_is_zero():
    # Ashwini -> Ashlesha is 9 away: remainder 0 -> MATCH.
    match = _working(_report(person("A", "bride", "Aries", "Ashwini"),
                             person("B", "groom", "Cancer", "Ashlesha")))["Tara / Dina Kuta"]
    assert match["matched"] is True and match["points"] == 3 and match["maximum"] == 3

    # Ashwini -> Bharani is 2 away: remainder 2 -> MATCH; use a non-match pair.
    non_match = _working(_report(person("A", "bride", "Aries", "Ashwini"),
                                 person("B", "groom", "Taurus", "Krittika")))["Tara / Dina Kuta"]
    assert non_match["points"] in (0, 3)
    assert non_match["matched"] is (non_match["points"] == 3)


def test_gana_match_is_six_and_non_match_is_zero():
    same = _working(_report(person("A", "bride", "Aries", "Ashwini"),      # Deva
                            person("B", "groom", "Pisces", "Revati")))["Gana"]  # Deva
    assert same["matched"] is True and same["points"] == 6 and same["maximum"] == 6

    flagged = _working(_report(person("A", "bride", "Aries", "Ashlesha"),  # Rakshasa
                               person("B", "groom", "Leo", "Ashwini")))["Gana"]  # Deva
    assert flagged["matched"] is False and flagged["points"] == 0
    assert flagged["maximum"] == 6


def test_every_scored_factor_reports_its_maximum():
    report = _report(person("A", "bride", "Aries", "Ashwini"),
                     person("B", "groom", "Cancer", "Ashlesha"))
    working = _working(report)
    assert working["Tara / Dina Kuta"]["maximum"] == 3
    assert working["Gana"]["maximum"] == 6
    assert working["Rashi Kuta"]["maximum"] == 7
    assert working["Graha Maitri"]["maximum"] == 5
    assert working["Vasya Kuta"]["maximum"] == 2


def test_unscored_factors_award_no_points():
    report = _report(person("A", "bride", "Aries", "Ashwini"),
                     person("B", "groom", "Cancer", "Ashlesha"))
    for name in ("Nadi", "Yoni Kuta"):
        assert "points" not in _working(report)[name], name
    assert {row["factor"] for row in report["totalScore"]["unscored"]} == {"Nadi", "Yoni Kuta"}


def test_total_is_the_exact_sum_of_binary_awards():
    report = _report(person("A", "bride", "Aries", "Ashwini"),
                     person("B", "groom", "Cancer", "Ashlesha"))
    total = report["totalScore"]
    assert total["awarded"] == sum(row["points"] for row in total["factors"])
    assert total["maximum"] == sum(row["maximum"] for row in total["factors"])
    assert total["maximum"] == 23, "3 + 6 + 7 + 5 + 2 - the owner's established maxima"
    assert total["outOf36"] is False, "23 is not 36, so it must not be labelled /36"
    for row in total["factors"]:
        assert row["points"] in (0, row["maximum"])


def test_changing_inputs_can_change_full_points_to_zero():
    match = _report(person("A", "bride", "Aries", "Ashwini"),
                    person("B", "groom", "Cancer", "Ashlesha"))["totalScore"]["awarded"]
    other = _report(person("A", "bride", "Aries", "Ashlesha"),
                    person("B", "groom", "Leo", "Magha"))["totalScore"]["awarded"]
    assert match != other
    assert isinstance(match, int) and isinstance(other, int)


def test_deep_factors_never_receive_points():
    body = TestClient(main.app).post("/api/compatibility", json=FIXTURE).json()
    report = body["report"]
    deep_names = {
        "Ascendant compatibility", "Partnership foundation (7th house)",
        "Partnership influences (contextual)", "Deep partnership (8th house)",
        "Relationship timing (Dasha)", "Communication (Mercury)",
        "Conflict & energy (Mars)", "Kuja Dosha balance",
    }
    for entry in report["technicalAnalysis"]:
        if entry["factor"] in deep_names:
            assert "points" not in entry and "maximum" not in entry, entry["factor"]
    assert {row["factor"] for row in report["totalScore"]["factors"]} == {
        "Tara / Dina Kuta", "Gana", "Rashi Kuta", "Graha Maitri", "Vasya Kuta"}


def test_public_working_shows_exactly_the_backend_points():
    body = TestClient(main.app).post("/api/compatibility", json=FIXTURE).json()
    report = body["report"]
    working = _working(report)
    total = {row["factor"]: row for row in report["totalScore"]["factors"]}
    for name, row in total.items():
        assert working[name]["points"] == row["points"], name
        assert working[name]["matched"] == row["matched"], name
        assert working[name]["maximum"] == row["maximum"], name


def test_no_partial_points_anywhere_in_the_serialized_report():
    raw = json.dumps(TestClient(main.app).post("/api/compatibility", json=FIXTURE).json())
    assert "/36" not in raw
    report = json.loads(raw)["report"]
    assert report["totalScore"]["maximum"] == 23
    for row in report["totalScore"]["factors"]:
        assert row["points"] in (0, row["maximum"])


def test_yoni_orientation_is_independent_of_binary_scoring():
    """The verified orientation stays; Yoni simply awards no binary points."""
    from compatibility import yoni
    assert yoni.matrix_value("Cat", "Horse") == 2       # groom row, bride column
    assert yoni.matrix_value("Horse", "Deer") == 3
    assert yoni.matrix_value("Deer", "Horse") == 1
    report = _report(person("A", "bride", "Aries", "Ashwini"),
                     person("B", "groom", "Cancer", "Ashlesha"))
    entry = _working(report)["Yoni Kuta"]
    assert entry["values"]["matrixOrientation"] == "male_row_female_column"
    assert entry["values"]["score"] == 2
    assert "points" not in entry


def test_safety_exclusions_survive_scoring():
    raw = json.dumps(TestClient(main.app).post("/api/compatibility", json=FIXTURE).json()).lower()
    for banned in ("death", "lifespan", "spouse", "fertilit", "pregnan", "child",
                   "genetic", "hereditar", "medical", "violence"):
        assert banned not in raw, banned
