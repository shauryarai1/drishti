"""Wire-level tests: the real serialized compatibility response.

These call the endpoint and inspect the FINAL JSON, which is the only boundary
that matters for methodology leakage.
"""

from __future__ import annotations

import json
import pathlib
import re

import pytest
from fastapi.testclient import TestClient

import main

REPO = pathlib.Path(__file__).resolve().parents[2]

# Two different fixtures: the deep, input-driven behaviour must change between them.
FIXTURE_A = {
    "bride": {"name": "Ananya", "date": "2010-01-21", "time": "08:19", "place": "Delhi",
              "latitude": 28.6139, "longitude": 77.209, "timezone": "Asia/Kolkata"},
    "groom": {"name": "Arjun", "date": "1990-05-15", "time": "14:15", "place": "Delhi",
              "latitude": 28.6139, "longitude": 77.209, "timezone": "Asia/Kolkata"},
}
FIXTURE_B = {
    "bride": {"name": "Meera", "date": "1988-11-02", "time": "21:40", "place": "Mumbai",
              "latitude": 19.076, "longitude": 72.8777, "timezone": "Asia/Kolkata"},
    "groom": {"name": "Rohan", "date": "1995-03-09", "time": "05:05", "place": "Chennai",
              "latitude": 13.0827, "longitude": 80.2707, "timezone": "Asia/Kolkata"},
}


def _post(payload):
    return TestClient(main.app).post("/api/compatibility", json=payload)


def _walk(node):
    """Every string in the JSON, recursively."""
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for key, value in node.items():
            yield str(key)
            yield from _walk(value)
    elif isinstance(node, list):
        for item in node:
            yield from _walk(item)


def test_public_contract_shape():
    body = _post(FIXTURE_A).json()
    assert body["status"] == "ok"
    report = body["report"]
    assert set(report) >= {"overall", "atAGlance", "strengths", "attentionAreas",
                           "inDepth", "kavachView"}
    assert set(report["overall"]) == {"state", "summary"}
    assert report["overall"]["state"] in (
        "STRONG POTENTIAL", "GENERALLY SUPPORTIVE", "MIXED COMPATIBILITY", "SIGNIFICANT CHALLENGES")
    assert isinstance(report["atAGlance"], list) and report["atAGlance"]
    assert isinstance(report["strengths"], list)
    assert isinstance(report["attentionAreas"], list)
    assert isinstance(report["inDepth"], list) and report["inDepth"]
    assert report["kavachView"]


def test_people_field_carries_no_chart_information():
    body = _post(FIXTURE_A).json()
    for person in body["people"]:
        assert set(person) == {"role", "name"}, person
    assert [p["role"] for p in body["people"]] == ["bride", "groom"]
    assert [p["name"] for p in body["people"]] == ["Ananya", "Arjun"]


def test_technical_analysis_is_published_as_an_allowlist():
    """The working is openly shown now - but only the approved astrology fields."""
    report = _post(FIXTURE_A).json()["report"]
    working = report["technicalAnalysis"]
    names = [entry["factor"] for entry in working]
    assert names == [
        "Tara / Dina Kuta", "Gana", "Nadi", "Rashi Kuta", "Graha Maitri", "Vasya Kuta",
        "Yoni Kuta", "Ascendant compatibility", "Partnership foundation (7th house)",
        "Partnership influences (contextual)", "Deep partnership (8th house)",
        "Relationship timing (Dasha)", "Communication (Mercury)",
        "Conflict & energy (Mars)", "Kuja Dosha balance",
    ]
    for entry in working:
        assert set(entry) == {"factor", "values", "result", "meaning"}
        assert entry["result"] in ("Supportive", "Mixed", "Challenging", "Contextual",
                                   "Strong alignment", "Needs attention")
        assert entry["meaning"]


def test_overall_working_separates_voters_from_contextual_evidence():
    working = _post(FIXTURE_A).json()["report"]["overallWorking"]
    assert set(working) == {"state", "counts", "eligible", "contextualOnly", "note"}
    assert working["contextualOnly"] == [
        {"factor": "Partnership influences (contextual)", "result": "Contextual"}]
    assert all(row["result"] != "Contextual" for row in working["eligible"])
    assert working["state"] in (
        "STRONG POTENTIAL", "GENERALLY SUPPORTIVE", "MIXED COMPATIBILITY", "SIGNIFICANT CHALLENGES")


def test_public_working_carries_no_private_internals():
    raw = json.dumps(_post(FIXTURE_A).json())
    lowered = raw.lower()
    for banned in ("service_role", "supabase", "token", "password", "secret", "apikey",
                   "authorization", "bearer", "env", "traceback", "chartfacts",
                   "factorresult", "deepfactor", "personfacts", "class ", "def ",
                   "c:\\", "/users/", ".py", "reason_code", "rule_id", "source_code"):
        assert banned not in lowered, banned


def test_internal_analysis_object_is_not_serialized():
    raw = json.dumps(_post(FIXTURE_A).json()).lower()
    for banned in ("moon_sign", "moon_nakshatra", "moon_ruler", "status_counts",
                   "bucket", "chartfacts", "deepfactor", "factorresult"):
        assert banned not in raw, banned


def test_interpretation_is_input_driven():
    a = _post(FIXTURE_A).json()["report"]
    b = _post(FIXTURE_B).json()["report"]
    assert a != b, "different charts must produce different interpreted reports"
    assert (a["atAGlance"] != b["atAGlance"]
            or a["inDepth"] != b["inDepth"]
            or a["overall"] != b["overall"])


def test_strengths_and_attention_correspond_to_evidence():
    report = _post(FIXTURE_A).json()["report"]
    # A strength exists only where the corresponding glance state is supportive.
    supportive = {e["category"] for e in report["atAGlance"] if e["status"] == "Supportive"}
    if report["strengths"]:
        assert supportive, "strengths require supportive evidence"
    assert len(report["strengths"]) <= 4
    assert len(report["attentionAreas"]) <= 4


def test_kavach_view_follows_the_overall_state():
    report = _post(FIXTURE_A).json()["report"]
    assert report["kavachView"]
    assert report["overall"]["summary"]
    view = report["kavachView"].lower()
    for banned in ("guaranteed", "definitely", "will fail", "should marry",
                   "should not marry", "perfect match"):
        assert banned not in view, banned


def test_safety_language_absent_from_the_http_response():
    raw = json.dumps(_post(FIXTURE_A).json()).lower()
    for banned in ("death", "die", "lifespan", "longevity", "fertilit", "pregnan",
                   "genetic", "hereditar", "medical", "disease", "violence", "poverty",
                   "misery", "sorrow"):
        assert banned not in raw, banned


def test_adapter_uses_the_authoritative_chart_and_dasha_output():
    """The wiring reads ChartFacts from build_kundli; it never recalculates."""
    source = (REPO / "backend" / "compatibility" / "api.py").read_text(encoding="utf-8")
    assert "build_kundli" in source
    assert 'inner.get("ascendant")' in source
    assert 'inner.get("houses")' in source
    assert 'dasha.get("currentMahadasha")' not in source  # via the _lord helper
    assert '_lord("currentMahadasha")' in source
    assert '_lord("currentAntardasha")' in source
    # No competing calculation anywhere in the adapter.
    for banned in ("swisseph", "swe.", "FLG_SPEED", "ayanamsa", "vimshottari", "calc_planet"):
        assert banned not in source, banned


def test_chart_facts_are_derived_not_invented(monkeypatch):
    """A focused proof that the adapter maps real chart output into ChartFacts."""
    import compatibility.api as api

    captured = {}

    def fake_build(payload):
        return {
            "planets": [
                {"planet": "Moon", "rashi": "Pisces", "house": 3, "nakshatra": "Uttara Bhadrapada"},
                {"planet": "Mars", "rashi": "Cancer", "house": 7},
                {"planet": "Mercury", "rashi": "Capricorn", "house": 1},
            ],
            "chart": {
                "ascendant": {"rashi": "Capricorn"},
                "houses": [{"number": n, "rashi": "Capricorn"} for n in range(1, 13)],
            },
            "dasha": {"currentMahadasha": {"lord": "Venus"},
                      "currentAntardasha": {"lord": "Moon"}},
        }

    import kundli
    monkeypatch.setattr(kundli, "build_kundli", fake_build)

    person, facts = api._facts(api.PersonInput(name="Test", date="2010-01-21", time="08:19",
                                               place="Delhi", latitude=28.6, longitude=77.2,
                                               timezone="Asia/Kolkata"), "bride")
    assert person.moon_nakshatra == "Uttara Bhadrapada"
    assert facts.lagna == "Capricorn"
    assert facts.planets["Mars"] == {"sign": "Cancer", "house": 7}
    assert facts.houses[1] == "Capricorn"
    assert facts.dasha_lords == ("Venus", "Moon")
