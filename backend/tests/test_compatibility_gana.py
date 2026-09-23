"""Gana Kuta: the owner's authoritative direction, exhaustively.

Rule: same Gana = MATCH; when the Ganas differ the FEMALE (bride) must be of the
better temperament than the MALE (groom). Deva > Manushya > Rakshasa.
Binary: MATCH = 6/6, NO MATCH = 0/6.
"""

from __future__ import annotations

import pytest

from compatibility import gana
from compatibility.interpretation import BINARY_SCORING, _award, _matched
from compatibility.models import PersonFacts
from kundli import build_kundli
from kundli.analysis.signs import SIGN_LORD

# One representative Nakshatra per Gana category.
REP = {"Deva": "Ashwini", "Manushya": "Bharani", "Rakshasa": "Krittika"}

# (female/bride Gana, male/groom Gana) -> expected MATCH
EXPECTED = {
    ("Deva", "Deva"): True,
    ("Deva", "Manushya"): True,
    ("Deva", "Rakshasa"): True,
    ("Manushya", "Deva"): False,
    ("Manushya", "Manushya"): True,
    ("Manushya", "Rakshasa"): True,
    ("Rakshasa", "Deva"): False,
    ("Rakshasa", "Manushya"): False,
    ("Rakshasa", "Rakshasa"): True,
}

OWNER_FIXTURE = {
    "male": {"date": "1997-03-23", "time": "19:29", "place": "Sundarnagar",
             "latitude": 31.5333, "longitude": 76.8833, "timezone": "Asia/Kolkata"},
    "female": {"date": "2003-01-24", "time": "05:55", "place": "Sundarnagar",
               "latitude": 31.5333, "longitude": 76.8833, "timezone": "Asia/Kolkata"},
}


def person(role, nakshatra):
    return PersonFacts(name=role, role=role, moon_sign="Aries",
                       moon_nakshatra=nakshatra, moon_ruler=SIGN_LORD["Aries"])


# --- the rule itself --------------------------------------------------------
@pytest.mark.parametrize("female,male,expected", [
    (f, m, e) for (f, m), e in EXPECTED.items()
])
def test_is_match_for_all_nine_combinations(female, male, expected):
    assert gana.is_match(female, male) is expected


@pytest.mark.parametrize("female,male,expected", [
    (f, m, e) for (f, m), e in EXPECTED.items()
])
def test_evaluate_and_binary_scoring_agree_for_all_nine(female, male, expected):
    result = gana.evaluate(person("bride", REP[female]), person("groom", REP[male]))
    assert _matched("gana", result.status) is expected, (female, male, result.status)
    assert _award("gana", result.status) == (6 if expected else 0), (female, male)
    assert result.status in ("Strong alignment", "Supportive", "Needs attention")


def test_direction_is_female_to_male_not_reversed():
    """The same pair of Ganas flips when the roles swap."""
    forward = gana.evaluate(person("bride", REP["Manushya"]), person("groom", REP["Deva"]))
    reverse = gana.evaluate(person("bride", REP["Deva"]), person("groom", REP["Manushya"]))
    assert _award("gana", forward.status) == 0
    assert _award("gana", reverse.status) == 6


def test_no_partial_gana_points():
    for (female, male) in EXPECTED:
        result = gana.evaluate(person("bride", REP[female]), person("groom", REP[male]))
        assert _award("gana", result.status) in (0, 6)


def test_gana_maximum_is_six():
    assert BINARY_SCORING["gana"]["maximum"] == 6


# --- the owner's regression fixture, end to end -----------------------------
def test_owner_fixture_is_a_gana_match_six_of_six():
    male = build_kundli({**OWNER_FIXTURE["male"], "name": "Male"})
    female = build_kundli({**OWNER_FIXTURE["female"], "name": "Female"})
    male_moon = next(r for r in male["planets"] if r["planet"] == "Moon")
    female_moon = next(r for r in female["planets"] if r["planet"] == "Moon")

    # The engine's own nakshatras for the fixture.
    assert male_moon["nakshatra"] == "Uttara Phalguni"
    assert female_moon["nakshatra"] == "Hasta"

    # Uttara Phalguni is Manushya; Hasta is Deva.
    assert gana.gana_of("Uttara Phalguni") == gana.MANUSHYA
    assert gana.gana_of("Hasta") == gana.DEVA

    result = gana.evaluate(person("bride", "Hasta"), person("groom", "Uttara Phalguni"))
    assert _matched("gana", result.status) is True
    assert _award("gana", result.status) == 6
    assert result.facts["brideGana"] == "Deva"
    assert result.facts["groomGana"] == "Manushya"
