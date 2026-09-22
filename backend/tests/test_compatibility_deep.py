"""Deep compatibility rules, aggregation and the public interpretation layer."""

from __future__ import annotations

import json
import pathlib

import pytest

from compatibility import graha_maitri
from compatibility.deep import (
    CHALLENGING, CONTEXTUAL, ELIGIBLE_FACTORS, CONTEXTUAL_FACTORS, MIXED, SUPPORTIVE,
    ChartFacts, communication, conflict_balance, deep_partnership, energy_style,
    overall_state, personality_fit, relationship_foundation, relationship_timing,
)
from compatibility.interpretation import PUBLIC_THEMES, build_interpreted
from kundli.analysis.signs import RASHIS

REPO = pathlib.Path(__file__).resolve().parents[2]

FRIENDSHIP = graha_maitri.relation


def chart(lagna="Aries", planets=None, houses=None, lords=("Venus", "Jupiter")):
    return ChartFacts(
        lagna=lagna,
        planets=planets or {},
        houses=houses or {n: RASHIS[n - 1] for n in range(1, 13)},
        dasha_lords=tuple(lords),
    )


SETTLED = chart("Aries", {"Mercury": {"sign": "Aries", "house": 1}, "Mars": {"sign": "Cancer", "house": 4}},
                lords=("Venus", "Jupiter"))
EASY = chart("Leo", {"Mercury": {"sign": "Aries", "house": 9}, "Mars": {"sign": "Aries", "house": 9}},
             lords=("Moon", "Venus"))


# --- A. foundation -----------------------------------------------------------
def test_foundation_supportive_when_both_lords_are_well_placed():
    result = relationship_foundation(SETTLED, EASY)
    assert result.status == SUPPORTIVE and result.eligible is True


def test_foundation_mixed_when_one_chart_is_pressured():
    # 7th house in Libra -> Venus rules it; Venus placed in a difficult house in
    # one chart only.
    pressured = chart("Aries", {"Venus": {"sign": "Scorpio", "house": 8}},
                      houses={**SETTLED.houses, 7: "Libra"})
    result = relationship_foundation(SETTLED, pressured)
    assert result.status == MIXED
    assert result.eligible is True


def test_foundation_context_is_never_eligible():
    result = __import__("compatibility.deep", fromlist=["foundation_context"]).foundation_context(SETTLED, EASY)
    assert result.status == CONTEXTUAL and result.eligible is False


# --- B. deep partnership -----------------------------------------------------
def test_deep_partnership_supportive_when_clear():
    assert deep_partnership(SETTLED, EASY).status == SUPPORTIVE


def test_deep_partnership_challenging_when_both_carry_named_pressure():
    a = chart("Aries", {"Mars": {"sign": "Aries", "house": 8}})
    b = chart("Leo", {"Rahu": {"sign": "Leo", "house": 8}})
    assert deep_partnership(a, b).status == CHALLENGING


def test_deep_partnership_never_mentions_mortality():
    result = deep_partnership(chart("Aries", {"Mars": {"sign": "Aries", "house": 8}}),
                              chart("Leo", {"Ketu": {"sign": "Leo", "house": 8}}))
    text = result.prose.lower()
    for banned in ("death", "lifespan", "longevity", "health", "spouse"):
        assert banned not in text, banned


# --- C. personality fit ------------------------------------------------------
def test_personality_fit_uses_the_compatibility_friendship_table_only():
    friends = personality_fit(chart("Leo"), chart("Cancer"), FRIENDSHIP)   # Sun + Moon
    assert friends.status == SUPPORTIVE
    enemies = personality_fit(chart("Leo"), chart("Taurus"), FRIENDSHIP)   # Sun + Venus
    assert enemies.status == CHALLENGING

    mixed = personality_fit(chart("Aries"), chart("Cancer"), FRIENDSHIP)     # Mars + Moon
    assert mixed.status in (SUPPORTIVE, MIXED, CHALLENGING)


def test_personality_fit_does_not_use_bnn():
    source = (REPO / "backend" / "compatibility" / "deep.py").read_text(encoding="utf-8")
    assert "kundli.analysis.relationships" not in source
    assert "BNN_RELATIONSHIPS" not in source


# --- D. timing ---------------------------------------------------------------
def test_timing_supportive_for_friendly_lords_and_mixed_otherwise():
    assert relationship_timing(chart(lords=("Venus", "Moon")), chart(lords=("Jupiter", "Venus"))).status == SUPPORTIVE
    assert relationship_timing(chart(lords=("Saturn", "Mars")), chart(lords=("Saturn", "Mars"))).status == MIXED


def test_timing_never_predicts_events():
    prose = relationship_timing(chart(lords=("Saturn",)), chart(lords=("Mars",))).prose.lower()
    for banned in ("will marry", "divorce", "marriage will", "will happen"):
        assert banned not in prose, banned


# --- E. communication --------------------------------------------------------
@pytest.mark.parametrize("a,b,expected", [
    ("Aries", "Aries", SUPPORTIVE),      # conjunction
    ("Aries", "Libra", SUPPORTIVE),      # opposition
    ("Aries", "Gemini", SUPPORTIVE),     # 3/11
    ("Aries", "Leo", SUPPORTIVE),        # 5/9
    ("Aries", "Virgo", CHALLENGING),     # 6/8
    ("Aries", "Pisces", CHALLENGING),    # 2/12
    ("Aries", "Sagittarius", SUPPORTIVE),  # 5/9
    ("Aries", "Cancer", MIXED),          # unspecified
    ("Aries", "Capricorn", MIXED),       # unspecified
])
def test_communication_classes(a, b, expected):
    result = communication(chart("Aries", {"Mercury": {"sign": a, "house": 1}}),
                           chart("Leo", {"Mercury": {"sign": b, "house": 1}}), RASHIS)
    assert result.status == expected, (a, b)


def test_communication_never_mentions_mercury():
    result = communication(chart("Aries", {"Mercury": {"sign": "Virgo", "house": 1}}),
                           chart("Leo", {"Mercury": {"sign": "Aries", "house": 1}}), RASHIS)
    assert "mercury" not in result.prose.lower()


# --- F. energy ---------------------------------------------------------------
@pytest.mark.parametrize("a,b,expected", [
    ("Aries", "Aries", SUPPORTIVE),
    ("Aries", "Gemini", SUPPORTIVE),
    ("Aries", "Leo", SUPPORTIVE),
    ("Aries", "Virgo", MIXED),      # not classified by the source -> never negative
    ("Aries", "Pisces", MIXED),
])
def test_energy_classes(a, b, expected):
    result = energy_style(chart("Aries", {"Mars": {"sign": a, "house": 1}}),
                          chart("Leo", {"Mars": {"sign": b, "house": 1}}), RASHIS)
    assert result.status == expected, (a, b)


def test_energy_never_mentions_mars():
    result = energy_style(chart("Aries", {"Mars": {"sign": "Aries", "house": 1}}),
                          chart("Leo", {"Mars": {"sign": "Leo", "house": 1}}), RASHIS)
    assert "mars" not in result.prose.lower()


# --- G. conflict balance -----------------------------------------------------
def test_conflict_balance_both_neither_and_one():
    both = conflict_balance(chart("Aries", {"Mars": {"sign": "Aries", "house": 1}}),
                            chart("Leo", {"Mars": {"sign": "Leo", "house": 7}}))
    assert both.status == SUPPORTIVE and both.evidence["brideCondition"] is True

    neither = conflict_balance(chart("Aries", {"Mars": {"sign": "Aries", "house": 3}}),
                               chart("Leo", {"Mars": {"sign": "Leo", "house": 5}}))
    assert neither.status == SUPPORTIVE

    one = conflict_balance(chart("Aries", {"Mars": {"sign": "Aries", "house": 1}}),
                           chart("Leo", {"Mars": {"sign": "Leo", "house": 3}}))
    assert one.status == MIXED


def test_conflict_balance_hides_the_technique():
    result = conflict_balance(chart("Aries", {"Mars": {"sign": "Aries", "house": 1}}),
                              chart("Leo", {"Mars": {"sign": "Leo", "house": 1}}))
    text = result.prose.lower()
    for banned in ("kuja", "mars", "house", "violen", "passion", "age 30", "thirty"):
        assert banned not in text, banned


# --- aggregation audit -------------------------------------------------------
def test_eligible_and_contextual_registries_are_explicit():
    assert set(ELIGIBLE_FACTORS) == {
        "tara", "gana", "nadi", "rashi", "graha_maitri", "vasya", "yoni",
        "foundation", "deep_partnership", "personality_fit", "timing",
        "communication", "energy_style", "conflict_balance",
    }
    assert CONTEXTUAL_FACTORS == ("foundation_context",)
    assert not set(CONTEXTUAL_FACTORS) & set(ELIGIBLE_FACTORS)


def test_contextual_evidence_can_never_change_the_verdict():
    base = [SUPPORTIVE] * 10
    with_context = base + [CONTEXTUAL] * 5
    assert overall_state(base)["state"] == overall_state(with_context)["state"]


@pytest.mark.parametrize("statuses,expected", [
    ([SUPPORTIVE] * 12, "STRONG POTENTIAL"),
    ([SUPPORTIVE] * 8 + [MIXED] * 2, "STRONG POTENTIAL"),
    ([SUPPORTIVE] * 6 + [MIXED] * 2 + [CHALLENGING] * 1, "GENERALLY SUPPORTIVE"),
    ([SUPPORTIVE] * 4 + [CHALLENGING] * 3 + [MIXED] * 1, "MIXED COMPATIBILITY"),
    ([CHALLENGING] * 6 + [SUPPORTIVE] * 1, "SIGNIFICANT CHALLENGES"),
    ([MIXED] * 8, "MIXED COMPATIBILITY"),
    ([SUPPORTIVE] * 2, "MIXED COMPATIBILITY"),          # insufficient evidence
])
def test_overall_boundaries(statuses, expected):
    assert overall_state(statuses)["state"] == expected


def test_overall_ties_are_deterministic():
    tied = [SUPPORTIVE, CHALLENGING] * 4
    first = overall_state(tied)
    assert first["net"] == 0
    assert first["state"] == "MIXED COMPATIBILITY"
    assert overall_state(tied) == first


def test_no_weights_are_used():
    source = (REPO / "backend" / "compatibility" / "deep.py").read_text(encoding="utf-8")
    assert "weighted" not in source.lower()
    assert "weight=" not in source.lower()
    assert "score" not in source.lower().split("no ")  # no scoring model is built


# --- public interpretation layer --------------------------------------------
def _interpreted():
    kutas = [type("F", (), {"key": k, "status": SUPPORTIVE, "prose": "This area reads well."})()
             for k in ("tara", "gana", "nadi", "rashi", "graha_maitri", "vasya", "yoni")]
    deep = [
        relationship_foundation(SETTLED, EASY),
        deep_partnership(SETTLED, EASY),
        personality_fit(chart("Aries"), chart("Cancer"), FRIENDSHIP),
        relationship_timing(chart(lords=("Venus",)), chart(lords=("Moon",))),
        communication(chart("Aries", {"Mercury": {"sign": "Aries", "house": 1}}),
                      chart("Leo", {"Mercury": {"sign": "Leo", "house": 1}}), RASHIS),
        energy_style(chart("Aries", {"Mars": {"sign": "Aries", "house": 1}}),
                     chart("Leo", {"Mars": {"sign": "Leo", "house": 1}}), RASHIS),
        conflict_balance(chart("Aries", {"Mars": {"sign": "Aries", "house": 1}}),
                         chart("Leo", {"Mars": {"sign": "Leo", "house": 7}})),
    ]
    return build_interpreted(kutas, deep, {"bride": "Ananya", "groom": "Arjun"})


def test_public_report_has_the_required_sections():
    report = _interpreted()
    assert set(report) >= {"overall", "atAGlance", "strengths", "attentionAreas",
                           "inDepth", "kavachView", "technicalAnalysis", "overallWorking"}
    assert set(report["overall"]) == {"state", "summary"}
    assert report["overall"]["state"] in (
        "STRONG POTENTIAL", "GENERALLY SUPPORTIVE", "MIXED COMPATIBILITY", "SIGNIFICANT CHALLENGES")
    assert len(report["atAGlance"]) == len(PUBLIC_THEMES)
    assert 2 <= len(report["strengths"]) <= 4
    assert report["kavachView"]


def test_public_report_is_deterministic():
    assert json.dumps(_interpreted(), sort_keys=True) == json.dumps(_interpreted(), sort_keys=True)


def test_public_report_publishes_the_approved_working_only():
    """Methodology is now openly shown; only approved astrology fields appear."""
    report = _interpreted()
    assert "technicalAnalysis" in report and "overallWorking" in report
    names = [entry["factor"] for entry in report["technicalAnalysis"]]
    assert "Tara / Dina Kuta" in names and "Yoni Kuta" in names
    blob = json.dumps(report).lower()
    for banned in ("service_role", "supabase", "token", "password", "traceback",
                   "chartfacts", "factorresult", "deepfactor", ".py", "c:\\"):
        assert banned not in blob, banned


def test_public_report_never_serializes_internal_evidence():
    report = _interpreted()
    for entry in report["atAGlance"]:
        assert set(entry) == {"category", "status", "interpretation"}
    for entry in report["inDepth"]:
        assert set(entry) == {"category", "interpretation"}


def test_in_depth_text_changes_with_the_evidence():
    strong = _interpreted()
    weak_kutas = [type("F", (), {"key": k, "status": CHALLENGING, "prose": "challenging"})()
                  for k in ("tara", "gana", "nadi", "rashi", "graha_maitri", "vasya", "yoni")]
    weak = build_interpreted(weak_kutas, [], {"bride": "A", "groom": "B"})
    assert strong["inDepth"] != weak["inDepth"]
    assert strong["overall"]["state"] != weak["overall"]["state"]


def test_kavach_view_follows_the_overall_state():
    for statuses, state in (([SUPPORTIVE] * 12, "STRONG POTENTIAL"),
                            ([CHALLENGING] * 8, "SIGNIFICANT CHALLENGES")):
        assert overall_state(statuses)["state"] == state
    view = _interpreted()["kavachView"].lower()
    for banned in ("guaranteed", "definitely", "will fail", "should marry", "should not marry"):
        assert banned not in view, banned


def test_safety_language_absent_from_the_whole_public_report():
    blob = json.dumps(_interpreted()).lower()
    for banned in ("death", "die", "lifespan", "longevity", "fertilit", "pregnan", "child",
                   "genetic", "hereditar", "medical", "disease", "violence", "poverty",
                   "misery", "sorrow"):
        assert banned not in blob, banned
