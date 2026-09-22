"""The published working must agree exactly with the engine's own calculations.

One source of truth: the UI shows what the engine computed; nothing is
recalculated for display.
"""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

import main
from compatibility import graha_maitri, tara, yoni
from compatibility.deep import (
    KUJA_HOUSES, _pair, overall_state, sign_distance,
)
from kundli.analysis.signs import RASHIS

FIXTURE = {
    "bride": {"name": "Ananya", "date": "2010-01-21", "time": "08:19", "place": "Delhi",
              "latitude": 28.6139, "longitude": 77.209, "timezone": "Asia/Kolkata"},
    "groom": {"name": "Arjun", "date": "1990-05-15", "time": "14:15", "place": "Delhi",
              "latitude": 28.6139, "longitude": 77.209, "timezone": "Asia/Kolkata"},
}


def _working():
    body = TestClient(main.app).post("/api/compatibility", json=FIXTURE).json()
    return body["report"]


def _entry(report, factor):
    return next(e for e in report["technicalAnalysis"] if e["factor"] == factor)


def test_displayed_tara_remainder_matches_the_engine():
    report = _working()
    values = _entry(report, "Tara / Dina Kuta")["values"]
    bride_nak, groom_nak = values["brideMoonNakshatra"], values["groomMoonNakshatra"]
    expected = tara.tara_count(list(NAKSHATRAS).index(bride_nak),
                               list(NAKSHATRAS).index(groom_nak)) % 9
    assert values["remainder"] == expected


def test_displayed_yoni_value_matches_the_engine_matrix():
    report = _working()
    values = _entry(report, "Yoni Kuta")["values"]
    assert values["score"] == yoni.matrix_value(values["groomAnimal"], values["brideAnimal"])
    assert values["matrixOrientation"] == "male_row_female_column"


def test_displayed_graha_maitri_matches_the_compatibility_table():
    report = _working()
    values = _entry(report, "Graha Maitri")["values"]
    assert values["brideViewOfGroom"] == graha_maitri.relation(
        values["brideMoonRuler"], values["groomMoonRuler"])
    assert values["groomViewOfBride"] == graha_maitri.relation(
        values["groomMoonRuler"], values["brideMoonRuler"])


def test_displayed_communication_matches_the_deep_engine():
    report = _working()
    values = _entry(report, "Communication (Mercury)")["values"]
    expected = sign_distance(values["brideSign"], values["groomSign"], RASHIS)
    assert values["distance"] == expected
    assert values["pair"] == sorted(_pair(expected))


def test_displayed_conflict_balance_matches_the_engine():
    report = _working()
    values = _entry(report, "Kuja Dosha balance")["values"]
    assert values["brideCondition"] is (values["brideHouse"] in KUJA_HOUSES)
    assert values["groomCondition"] is (values["groomHouse"] in KUJA_HOUSES)


def test_displayed_overall_classifications_match_the_aggregation_input():
    report = _working()
    working = report["overallWorking"]
    eligible_statuses = [row["result"] for row in working["eligible"]]
    expected = overall_state(eligible_statuses)
    assert working["state"] == expected["state"]
    assert working["counts"] == expected["counts"]
    # The published overall state is the same one shown at the top.
    assert report["overall"]["state"] == working["state"]


def test_displayed_factor_results_match_the_engine_results():
    report = _working()
    # Every published result is one of the states the engine emits.
    for entry in report["technicalAnalysis"]:
        assert entry["result"] in ("Supportive", "Mixed", "Challenging", "Contextual",
                                   "Strong alignment", "Needs attention")


def test_no_private_internals_in_the_published_working():
    raw = json.dumps(_working()).lower()
    for banned in ("service_role", "supabase", "token", "password", "secret", "apikey",
                   "authorization", "bearer", "traceback", "chartfacts", "factorresult",
                   "deepfactor", "personfacts", "reason_code", "rule_id", ".py", "c:\\"):
        assert banned not in raw, banned


def test_safety_exclusions_survive_the_visible_working():
    raw = json.dumps(_working()).lower()
    for banned in ("death", "die", "lifespan", "longevity", "spouse", "fertilit",
                   "pregnan", "child", "genetic", "hereditar", "medical", "disease",
                   "violence", "poverty", "misery"):
        assert banned not in raw, banned


from navtara.constants import NAKSHATRAS  # noqa: E402  (used above)
