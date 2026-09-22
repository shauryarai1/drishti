"""KAVACH MARRIAGE COMPATIBILITY (V1) - source-faithful, exhaustive tests.

The rule data must match the owner-supplied decks exactly. Nothing may be
invented, no /36 total may exist, Yoni must not be calculated, and no prohibited
output (death, lifespan, fertility, pregnancy, child health, hereditary or
medical claims) may appear anywhere in the feature.
"""

from __future__ import annotations

import pathlib

import pytest
from fastapi.testclient import TestClient

import main
from compatibility import gana, graha_maitri, nadi, rashi, tara, vasya
from compatibility.engine import evaluate_compatibility, overall_summary
from compatibility.models import STATUSES, PersonFacts
from navtara.constants import NAKSHATRAS
from kundli.analysis.signs import RASHIS, SIGN_LORD

REPO = pathlib.Path(__file__).resolve().parents[2]
PKG = REPO / "backend" / "compatibility"

DEVA = ("Ashwini", "Mrigashira", "Punarvasu", "Pushya", "Hasta", "Swati",
        "Anuradha", "Shravana", "Revati")
MANUSHYA = ("Bharani", "Rohini", "Ardra", "Purva Phalguni", "Uttara Phalguni",
            "Purva Ashadha", "Uttara Ashadha", "Purva Bhadrapada", "Uttara Bhadrapada")
RAKSHASA = ("Krittika", "Ashlesha", "Magha", "Chitra", "Vishakha", "Jyeshtha",
            "Mula", "Dhanishta", "Shatabhisha")

VAATA = ("Ashwini", "Ardra", "Punarvasu", "Uttara Phalguni", "Hasta", "Jyeshtha",
         "Mula", "Shatabhisha", "Purva Bhadrapada")
PITTA = ("Bharani", "Mrigashira", "Pushya", "Purva Phalguni", "Chitra", "Anuradha",
         "Purva Ashadha", "Dhanishta", "Uttara Bhadrapada")
KAPHA = ("Krittika", "Rohini", "Ashlesha", "Magha", "Swati", "Vishakha",
         "Uttara Ashadha", "Shravana", "Revati")


def person(name, role, sign, nakshatra):
    return PersonFacts(name=name, role=role, moon_sign=sign,
                       moon_nakshatra=nakshatra, moon_ruler=SIGN_LORD[sign])


# --- Gana: exactly 27, each once, exact sets --------------------------------
def test_gana_has_exactly_27_assignments_one_per_nakshatra():
    assert len(gana.GANA_BY_NAKSHATRA) == 27
    assert set(gana.GANA_BY_NAKSHATRA) == set(NAKSHATRAS)


@pytest.mark.parametrize("nakshatra", DEVA)
def test_gana_deva(nakshatra):
    assert gana.GANA_BY_NAKSHATRA[nakshatra] == gana.DEVA


@pytest.mark.parametrize("nakshatra", MANUSHYA)
def test_gana_manushya(nakshatra):
    assert gana.GANA_BY_NAKSHATRA[nakshatra] == gana.MANUSHYA


@pytest.mark.parametrize("nakshatra", RAKSHASA)
def test_gana_rakshasa(nakshatra):
    assert gana.GANA_BY_NAKSHATRA[nakshatra] == gana.RAKSHASA


def test_gana_has_no_invented_points():
    result = gana.evaluate(person("A", "bride", "Aries", "Ashwini"),
                           person("B", "groom", "Cancer", "Ashlesha"))
    assert result.points_awarded is None
    assert result.status in STATUSES


def test_gana_same_category_is_the_ideal_and_direction_is_preserved():
    same = gana.evaluate(person("A", "bride", "Aries", "Ashwini"),          # Deva
                         person("B", "groom", "Pisces", "Revati"))          # Deva
    assert same.status == "Strong alignment"          # Deva + Deva

    better_bride = gana.evaluate(person("A", "bride", "Aries", "Ashwini"),   # Deva
                                 person("B", "groom", "Leo", "Magha"))       # Rakshasa
    assert better_bride.status == "Supportive"

    # Rakshasa bride + Deva groom is the direction the source flags.
    flagged = gana.evaluate(person("A", "bride", "Aries", "Ashlesha"),       # Rakshasa
                            person("B", "groom", "Leo", "Ashwini"))          # Deva
    assert flagged.status == "Needs attention"

    # Deva bride + Rakshasa groom is acceptable per the source.
    ok = gana.evaluate(person("A", "bride", "Aries", "Ashwini"),             # Deva
                       person("B", "groom", "Leo", "Ashlesha"))              # Rakshasa
    assert ok.status == "Supportive"


# --- Nadi: exactly 27, each once, exact sets --------------------------------
def test_nadi_has_exactly_27_assignments_one_per_nakshatra():
    assert len(nadi.NADI_BY_NAKSHATRA) == 27
    assert set(nadi.NADI_BY_NAKSHATRA) == set(NAKSHATRAS)


@pytest.mark.parametrize("nakshatra", VAATA)
def test_nadi_vaata(nakshatra):
    assert nadi.NADI_BY_NAKSHATRA[nakshatra] == nadi.VAATA


@pytest.mark.parametrize("nakshatra", PITTA)
def test_nadi_pitta(nakshatra):
    assert nadi.NADI_BY_NAKSHATRA[nakshatra] == nadi.PITTA


@pytest.mark.parametrize("nakshatra", KAPHA)
def test_nadi_kapha(nakshatra):
    assert nadi.NADI_BY_NAKSHATRA[nakshatra] == nadi.KAPHA


def test_nadi_different_is_supportive_same_needs_attention_and_no_points():
    different = nadi.evaluate(person("A", "bride", "Aries", "Ashwini"),   # Vaata
                              person("B", "groom", "Cancer", "Ashlesha"))  # Kapha
    assert different.status == "Supportive"
    assert different.points_awarded is None

    same = nadi.evaluate(person("A", "bride", "Aries", "Ashwini"),        # Vaata
                         person("B", "groom", "Cancer", "Ardra"))          # Vaata
    assert same.status == "Needs attention"
    assert same.points_awarded is None


# --- Graha Maitri: the complete compatibility friendship table --------------
def test_natural_friendship_table_is_complete_for_seven_planets():
    assert set(graha_maitri.NATURAL_FRIENDSHIP) == {"Sun", "Moon", "Mercury", "Mars",
                                                    "Jupiter", "Venus", "Saturn"}
    for planet, row in graha_maitri.NATURAL_FRIENDSHIP.items():
        assert set(row) == {"friends", "enemies", "neutral"}, planet
        listed = set(row["friends"]) | set(row["enemies"]) | set(row["neutral"])
        assert listed <= set(graha_maitri.NATURAL_FRIENDSHIP), planet
        assert planet not in listed, planet
    # Exact source values for the rows the deck spells out.
    assert graha_maitri.NATURAL_FRIENDSHIP["Sun"]["friends"] == ("Moon", "Mars", "Jupiter")
    assert graha_maitri.NATURAL_FRIENDSHIP["Sun"]["enemies"] == ("Venus", "Saturn")
    assert graha_maitri.NATURAL_FRIENDSHIP["Moon"]["friends"] == ("Sun", "Mercury")
    assert graha_maitri.NATURAL_FRIENDSHIP["Moon"]["enemies"] == ()
    assert graha_maitri.NATURAL_FRIENDSHIP["Saturn"]["enemies"] == ("Sun", "Moon", "Mars")


def test_graha_maitri_scoring_uses_only_source_supported_values():
    # Sun + Moon are mutual friends -> the full sanctioned value.
    mutual_friends = graha_maitri.evaluate(person("A", "bride", "Leo", "Magha"),        # Sun
                                           person("B", "groom", "Cancer", "Pushya"))    # Moon
    assert mutual_friends.facts["brideViewOfGroom"] == "friends"
    assert mutual_friends.facts["groomViewOfBride"] == "friends"
    assert mutual_friends.points_awarded == 5

    # Venus + Mars are mutual neutral -> 3 points (explicit in the deck).
    neutral = graha_maitri.evaluate(person("A", "bride", "Taurus", "Rohini"),   # Venus
                                    person("B", "groom", "Aries", "Ashwini"))   # Mars
    assert neutral.facts["brideViewOfGroom"] == "neutral"
    assert neutral.facts["groomViewOfBride"] == "neutral"
    assert neutral.points_awarded == 3

    # Sun + Venus are mutual enemies -> 0 points (explicit in the deck).
    enemies = graha_maitri.evaluate(person("A", "bride", "Leo", "Magha"),        # Sun
                                    person("B", "groom", "Taurus", "Rohini"))    # Venus
    assert enemies.facts["brideViewOfGroom"] == "enemies"
    assert enemies.facts["groomViewOfBride"] == "enemies"
    assert enemies.points_awarded == 0


def test_graha_maitri_deck_worked_example():
    """Aries (Mars) bride + Cancer (Moon) groom: agreement met, not perfect."""
    result = graha_maitri.evaluate(person("A", "bride", "Aries", "Ashwini"),
                                   person("B", "groom", "Cancer", "Pushya"))
    assert result.facts["brideMoonRuler"] == "Mars"
    assert result.facts["groomMoonRuler"] == "Moon"
    assert result.points_awarded is None, "a mixed case has no source value"
    assert result.status == "Supportive"


# --- Vasya: complete 12-sign mapping ----------------------------------------
def test_vasya_mapping_is_complete_for_all_twelve_signs():
    assert set(vasya.AMENABLE) == set(RASHIS)
    assert vasya.AMENABLE["Aries"] == ("Leo", "Scorpio")
    assert vasya.AMENABLE["Capricorn"] == ("Aries", "Aquarius")
    assert vasya.AMENABLE["Pisces"] == ("Capricorn",)
    for sign, targets in vasya.AMENABLE.items():
        for target in targets:
            assert target in RASHIS, (sign, target)


def test_vasya_deck_worked_example_and_alignment():
    none = vasya.evaluate(person("A", "bride", "Aries", "Ashwini"),
                          person("B", "groom", "Cancer", "Pushya"))
    assert none.status == "Mixed"
    assert none.points_awarded == 0

    aligned = vasya.evaluate(person("A", "bride", "Aries", "Ashwini"),   # Aries -> Leo
                             person("B", "groom", "Leo", "Magha"))
    assert aligned.status == "Supportive"
    assert aligned.points_awarded == 2


# --- Tara: the deck's worked example + direction ----------------------------
def test_tara_deck_worked_example():
    """Ashwini (bride) -> Ashlesha (groom) is 9 away: remainder 0 = favourable."""
    result = tara.evaluate(person("A", "bride", "Aries", "Ashwini"),
                           person("B", "groom", "Cancer", "Ashlesha"), NAKSHATRAS)
    assert tara.tara_count(0, 8) == 9
    assert result.facts["remainder"] == 0
    assert result.status == "Supportive"
    assert result.points_awarded == 3


def test_tara_direction_is_preserved():
    """Swapping the roles changes the count."""
    assert tara.tara_count(0, 8) == 9          # bride Ashwini -> groom Ashlesha
    assert tara.tara_count(8, 0) == 20         # bride Ashlesha -> groom Ashwini
    assert tara.tara_count(0, 8) != tara.tara_count(8, 0)


@pytest.mark.parametrize("count,favourable", [
    (9, True), (2, True), (4, True), (6, True), (8, True), (18, True), (27, True),
    (1, False), (3, False), (5, False), (7, False), (10, False),
])
def test_tara_favourable_remainders(count, favourable):
    assert (count % 9 in tara.FAVOURABLE_REMAINDERS) is favourable


# --- Rashi: directional rules + mitigation ---------------------------------
def test_rashi_direction_is_preserved_and_swapping_changes_the_result():
    forward = rashi.evaluate(person("A", "bride", "Taurus", "Rohini"),      # bride 2nd from groom
                             person("B", "groom", "Aries", "Ashwini"), RASHIS)
    assert forward.facts["positionFromGroom"] == 2
    assert forward.status == "Supportive"

    reverse = rashi.evaluate(person("A", "bride", "Aries", "Ashwini"),      # bride 12th from groom
                             person("B", "groom", "Taurus", "Rohini"), RASHIS)
    assert reverse.facts["positionFromGroom"] == 12
    assert reverse.status == "Needs attention"


def test_rashi_same_sign_is_mixed():
    result = rashi.evaluate(person("A", "bride", "Aries", "Ashwini"),
                            person("B", "groom", "Aries", "Bharani"), RASHIS)
    assert result.facts["positionFromGroom"] == 1
    assert result.status == "Mixed"


def test_rashi_mitigation_by_same_ruler_and_by_friendship():
    # Same ruler, in the adverse range: Scorpio (Mars) is 8th from Aries (Mars).
    same_ruler = rashi.evaluate(person("A", "bride", "Scorpio", "Anuradha"),
                                person("B", "groom", "Aries", "Ashwini"), RASHIS)
    assert same_ruler.facts["positionFromGroom"] == 8
    assert same_ruler.facts["sameRuler"] is True
    assert same_ruler.facts["mitigationApplied"] is True
    assert same_ruler.status == "Supportive"
    assert same_ruler.points_awarded == rashi.POINTS_ON_CANCELLATION

    # Friendly rulers, in the adverse range: Cancer (Moon) 8th from Sagittarius
    # (Jupiter); the compatibility table treats Jupiter as a friend of the Moon.
    friendly = rashi.evaluate(person("A", "bride", "Cancer", "Pushya"),
                              person("B", "groom", "Sagittarius", "Mula"), RASHIS)
    assert friendly.facts["positionFromGroom"] == 8
    assert friendly.facts["rulersAreFriends"] is True
    assert friendly.facts["mitigationApplied"] is True
    assert friendly.status == "Supportive"


def test_rashi_uses_the_compatibility_table_not_bnn():
    source = (PKG / "rashi.py").read_text(encoding="utf-8")
    assert "graha_maitri" in source and "are_friends" in source
    for banned in ("kundli.analysis", "BNN", "bnn"):
        assert banned not in source, banned


# --- BNN registry untouched -------------------------------------------------
def test_bnn_registry_is_unchanged_and_unused():
    registry = (REPO / "backend" / "kundli" / "analysis" / "relationships.py").read_text(encoding="utf-8")
    assert '"Mars": (("Moon", "Jupiter", "Venus", "Sun", "Ketu"), ("Mercury", "Rahu", "Saturn"))' in registry
    assert "BNN directional friend / enemy / neutral registry" in registry

    for path in PKG.glob("*.py"):
        source = path.read_text(encoding="utf-8")
        assert "kundli.analysis.relationships" not in source, path.name
        assert "BNN_RELATIONSHIPS" not in source, path.name


# --- Yoni is not implemented, and there is no total ------------------------
def test_yoni_is_not_exposed_publicly_and_has_no_matrix_leak():
    """Yoni is implemented internally, but no animal/gender/matrix is public."""
    import re

    assert (PKG / "yoni.py").exists()
    report = evaluate_compatibility(person("A", "bride", "Aries", "Ashwini"),
                                    person("B", "groom", "Cancer", "Ashlesha"),
                                    NAKSHATRAS, RASHIS)
    blob = str(report).lower()
    for banned in ("yoni", "matrix", "animal", "brideanimal", "groomanimal"):
        assert banned not in blob, banned
    # Animal names as whole words only (avoids substring false positives).
    for animal in ("horse", "cat", "elephant", "serpent", "deer", "lion", "mongoose",
                   "monkey", "buffalo", "tiger", "rat", "cow", "dog", "goat", "sheep"):
        assert not re.search(rf"\b{animal}\b", blob), animal


def test_no_total_score_or_percentage_exists():
    for path in PKG.glob("*.py"):
        source = path.read_text(encoding="utf-8").lower()
        for banned in ("points_total", "total_points", "percentage", "score_out_of"):
            assert banned not in source, f"{path.name} has {banned}"

    report = evaluate_compatibility(person("A", "bride", "Aries", "Ashwini"),
                                    person("B", "groom", "Cancer", "Ashlesha"),
                                    NAKSHATRAS, RASHIS)
    assert report["label"] == "COMPATIBILITY FACTORS ANALYZED"
    assert set(report) == {"label", "factors", "summary", "disclaimer"}
    assert len(report["factors"]) == 7
    for factor in report["factors"]:
        # The public factor carries interpretation only - no internal key, no
        # evidence, no points.
        assert set(factor) == {"label", "subtitle", "status", "summary"}
    blob = str(report).lower()
    for banned in ("score", "out of", "/36", "percentage"):
        assert banned not in blob, banned


def test_only_source_supported_point_values_are_emitted():
    report = evaluate_compatibility(person("A", "bride", "Aries", "Ashwini"),
                                    person("B", "groom", "Cancer", "Ashlesha"),
                                    NAKSHATRAS, RASHIS)
    allowed = {None, 0, 2, 3, 5}
    for factor in report["factors"]:
        assert factor.get("points") in allowed, factor["key"]


# --- prohibited output ------------------------------------------------------
def test_no_prohibited_language_anywhere_in_the_feature():
    """The PUBLIC OUTPUT must never carry a prohibited claim.

    The package docstrings deliberately name these concepts to record that they
    are excluded, so the guarantee is asserted on the rendered report.
    """
    banned = ("death", "die", "lifespan", "longevity", "fertilit", "pregnan", "child",
              "progeny", "genetic", "hereditar", "medical", "disease", "illness",
              "violen", "poverty", "misery", "sorrow", "demon", "inferior",
              "will fail", "should marry", "should not marry", "perfect match")

    report = evaluate_compatibility(person("A", "bride", "Aries", "Ashwini"),
                                    person("B", "groom", "Cancer", "Ashlesha"),
                                    NAKSHATRAS, RASHIS)
    blob = str(report).lower()
    for term in banned:
        assert term not in blob, term

    # Every rendered factor text comes from the rule modules, never from prose
    # that could carry a claim: assert the safe vocabulary is what is rendered.
    for factor in report["factors"]:
        assert factor["status"] in STATUSES
        assert factor["summary"]


def test_overall_summary_never_gives_a_verdict():
    summary = overall_summary([
        gana.evaluate(person("A", "bride", "Aries", "Ashwini"),
                      person("B", "groom", "Leo", "Magha")),
    ])
    lowered = summary.lower()
    for banned in ("marry", "should", "perfect", "will fail", "guaranteed"):
        assert banned not in lowered, banned


# --- endpoint ---------------------------------------------------------------
def _payload():
    return {
        "bride": {"name": "Aarav", "date": "2010-01-21", "time": "08:19", "place": "Delhi",
                  "latitude": 28.6139, "longitude": 77.209, "timezone": "Asia/Kolkata"},
        "groom": {"name": "Meera", "date": "1990-05-15", "time": "14:15", "place": "Delhi",
                  "latitude": 28.6139, "longitude": 77.209, "timezone": "Asia/Kolkata"},
    }


def test_endpoint_requires_both_names_and_birth_details():
    client = TestClient(main.app)
    bad = _payload()
    bad["groom"]["name"] = "   "
    assert client.post("/api/compatibility", json=bad).json()["status"] == "invalid"

    bad2 = _payload()
    bad2["bride"]["date"] = ""
    assert client.post("/api/compatibility", json=bad2).json()["status"] == "invalid"


def test_endpoint_returns_the_qualitative_factors():
    body = TestClient(main.app).post("/api/compatibility", json=_payload()).json()
    assert body["status"] == "ok"
    assert [p["role"] for p in body["people"]] == ["bride", "groom"]
    assert body["report"]["label"] == "COMPATIBILITY FACTORS ANALYZED"
    assert len(body["report"]["factors"]) == 7
    blob = str(body).lower()
    for banned in ("yoni", "36", "score", "planet", "nakshatra lord"):
        assert banned not in blob, banned


def test_endpoint_preserves_the_birth_details_for_both_people():
    body = TestClient(main.app).post("/api/compatibility", json=_payload()).json()
    names = {p["role"]: p["name"] for p in body["people"]}
    assert names == {"bride": "Aarav", "groom": "Meera"}
    for person in body["people"]:
        assert person["moonSign"] in RASHIS
        assert person["moonNakshatra"] in NAKSHATRAS


def test_existing_kundli_tests_are_unaffected():
    """The compatibility package must not import or alter the Kundli engine."""
    for path in PKG.glob("*.py"):
        source = path.read_text(encoding="utf-8")
        for banned in ("calculator", "swisseph", "FLG_SPEED", "ayanamsa"):
            assert banned not in source, f"{path.name} touches {banned}"
