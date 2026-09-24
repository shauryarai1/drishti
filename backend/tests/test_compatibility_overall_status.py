"""Overall Matchmaking status is driven by the Kuta Match Score ratio."""

from __future__ import annotations

import pathlib

from compatibility.deep import score_state
from compatibility.engine import analyse_factors
from compatibility.interpretation import build_interpreted
from compatibility.models import PersonFacts
from kundli.analysis.signs import RASHIS, SIGN_LORD
from navtara.constants import NAKSHATRAS

REPO = pathlib.Path(__file__).resolve().parents[2]
PAGE = REPO / "frontend-next" / "components" / "CompatibilityExperience.tsx"


def _person(name, role, sign, nakshatra):
    return PersonFacts(name=name, role=role, moon_sign=sign,
                       moon_nakshatra=nakshatra, moon_ruler=SIGN_LORD[sign])


def test_score_bands_are_deterministic_at_boundaries():
    assert score_state(100, 100) == "STRONG POTENTIAL"
    assert score_state(75, 100) == "STRONG POTENTIAL"
    assert score_state(74, 100) == "GENERALLY SUPPORTIVE"      # just below 75%
    assert score_state(55, 100) == "GENERALLY SUPPORTIVE"
    assert score_state(54, 100) == "MIXED COMPATIBILITY"       # just below 55%
    assert score_state(35, 100) == "MIXED COMPATIBILITY"
    assert score_state(34, 100) == "SIGNIFICANT CHALLENGES"    # just below 35%
    assert score_state(0, 100) == "SIGNIFICANT CHALLENGES"


def test_score_bands_work_for_non_36_denominators():
    assert score_state(25, 27) == "STRONG POTENTIAL"           # 92.59%
    assert score_state(27, 36) == "STRONG POTENTIAL"           # 75%
    assert score_state(20, 36) == "GENERALLY SUPPORTIVE"       # 55.6%
    assert score_state(18, 36) == "MIXED COMPATIBILITY"        # 50%
    assert score_state(12, 36) == "SIGNIFICANT CHALLENGES"     # 33.3%
    assert score_state(0, 0) == "MIXED COMPATIBILITY"          # no denominator


def test_known_regression_pair_is_strong_potential():
    factors = analyse_factors(
        _person("Bride", "bride", "Virgo", "Hasta"),
        _person("Groom", "groom", "Virgo", "Uttara Phalguni"),
        NAKSHATRAS, RASHIS,
    )
    report = build_interpreted(factors, [], {"bride": "Bride", "groom": "Groom"})
    assert report["totalScore"]["awarded"] == 25
    assert report["totalScore"]["maximum"] == 27
    assert report["overall"]["state"] == "STRONG POTENTIAL"
    assert report["overall"]["state"] != "GENERALLY SUPPORTIVE"


def test_deep_analysis_no_longer_overwrites_the_primary_status():
    """The primary state follows the score, even if deep factors differ."""
    from compatibility.deep import SUPPORTIVE, DeepFactor

    factors = analyse_factors(
        _person("Bride", "bride", "Virgo", "Hasta"),
        _person("Groom", "groom", "Virgo", "Uttara Phalguni"),
        NAKSHATRAS, RASHIS,
    )
    challenging_deep = [
        DeepFactor("foundation", "Relationship foundation", "Challenging", True, "x"),
        DeepFactor("deep_partnership", "Deep partnership dynamics", "Challenging", True, "x"),
    ]
    report = build_interpreted(factors, challenging_deep, {"bride": "B", "groom": "G"})
    assert report["overall"]["state"] == "STRONG POTENTIAL"


def test_frontend_renders_the_authoritative_result_only():
    page = PAGE.read_text(encoding="utf-8")
    assert "report.overall?.state" in page
    assert "report.totalScore.awarded" in page
    # No second, competing score-status algorithm in the frontend.
    for banned in ("0.75", "0.55", "0.35", "score_state", "STRONG_MIN_RATIO", "/36"):
        assert banned not in page, banned
