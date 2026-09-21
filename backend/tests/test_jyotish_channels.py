"""Tests for the shared five-channel Jyotish interpretation layer."""

from __future__ import annotations

import inspect

import pytest

from jyotish.composition import interpret_channel, interpret_five_channels
from jyotish.houses import HOUSE_GROUPS, HOUSE_MEANINGS
from jyotish.planets import (
    CLASSICAL_PLANETS,
    DEBILITATION,
    EXALTATION,
    NODES,
    PLANET_SIGNIFICATIONS,
    RULERSHIP,
    dignity,
)
from prediction.panchang_natal.summary import build_channel_interpretations, build_life_summary
from question_engine.engine import answer_question

CHANNELS = ("vaar", "tithi", "karana", "nakshatra", "yoga")
DELHI = (28.6139, 77.2090, "Asia/Kolkata", "New Delhi")
BIRTH = ("1990-05-15", "14:15")
WHEN = "2026-09-20T14:15:00+05:30"


@pytest.fixture(scope="module")
def life_summary():
    return build_life_summary(*BIRTH, *DELHI)


@pytest.fixture(scope="module")
def birth_channels():
    return build_channel_interpretations(*BIRTH, *DELHI)


@pytest.fixture(scope="module")
def ask_answer():
    return answer_question("How will my evening go today?", WHEN, *DELHI)


# --- composition over all classical planets --------------------------------
@pytest.mark.parametrize("planet", CLASSICAL_PLANETS)
@pytest.mark.parametrize("house", [1, 5, 10])
def test_composition_produces_text_for_every_planet_and_house(planet, house):
    result = interpret_channel("vaar", planet, house, "Mesha")
    assert result["summary"]
    assert result["public_summary"]


@pytest.mark.parametrize("planet", list(PLANET_SIGNIFICATIONS))
def test_planet_significations_stay_conservative(planet):
    text = PLANET_SIGNIFICATIONS[planet].lower()
    for forbidden in ("death", "lifespan", "fatal", "disease", "diagnos", "guarantee"):
        assert forbidden not in text


def test_same_planet_same_house_differs_per_channel():
    outputs = {
        channel: interpret_channel(channel, "Jupiter", 9, "Dhanu")["summary"]
        for channel in CHANNELS
    }
    assert len(set(outputs.values())) == len(CHANNELS)
    assert outputs["vaar"] != outputs["karana"]
    assert outputs["karana"] != outputs["nakshatra"]
    assert outputs["nakshatra"] != outputs["yoga"]
    assert outputs["tithi"] != outputs["yoga"]


# --- dignity ---------------------------------------------------------------
@pytest.mark.parametrize("planet,sign", [("Sun", "Leo"), ("Moon", "Karka"), ("Mars", "Aries"),
                                         ("Mars", "Vrishchika"), ("Mercury", "Mithuna"),
                                         ("Jupiter", "Meena"), ("Venus", "Tula"), ("Saturn", "Kumbha")])
def test_own_sign_detection(planet, sign):
    assert dignity(planet, sign) == "own_sign"


@pytest.mark.parametrize("planet,sign", [(p, s) for p, s in EXALTATION.items() if s not in RULERSHIP.get(p, [])])
def test_exaltation_detection(planet, sign):
    assert dignity(planet, sign) == "exalted"


def test_own_sign_takes_priority_where_signs_overlap():
    # Mercury is exalted in Virgo AND owns Virgo: own sign is reported first.
    assert dignity("Mercury", "Virgo") == "own_sign"


@pytest.mark.parametrize("planet,sign", list(DEBILITATION.items()))
def test_debilitation_detection(planet, sign):
    assert dignity(planet, sign) == "debilitated"


@pytest.mark.parametrize("node", NODES)
def test_nodes_never_receive_invented_dignity(node):
    for sign in ("Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya",
                 "Tula", "Vrishchika", "Dhanu", "Makara", "Kumbha", "Meena"):
        assert dignity(node, sign) == "not_assigned"


def test_nodes_have_no_sign_ownership():
    for node in NODES:
        assert node not in RULERSHIP


def test_classical_planets_have_ownership():
    for planet in CLASSICAL_PLANETS:
        assert RULERSHIP[planet]


# --- house condition groups -----------------------------------------------
def test_condition_groups_are_exact():
    assert HOUSE_GROUPS["kendra"] == [1, 4, 7, 10]
    assert HOUSE_GROUPS["trikona"] == [1, 5, 9]
    assert HOUSE_GROUPS["upachaya"] == [3, 6, 10, 11]
    assert HOUSE_GROUPS["dusthana"] == [6, 8, 12]


@pytest.mark.parametrize("house", [6, 8, 12])
def test_dusthana_houses_are_conditional_not_fatalistic(house):
    result = interpret_channel("vaar", "Saturn", house, "Makara")
    text = " ".join([str(result["summary"])] + result["watch_for"]).lower()
    assert result["watch_for"]
    for forbidden in ("will lose", "will fail", "bad", "danger", "disaster", "terrible"):
        assert forbidden not in text


def test_house_eight_is_never_death():
    text = HOUSE_MEANINGS[8].lower()
    assert "death" not in text and "die" not in text


def test_no_medical_or_lifespan_language_in_tables():
    blob = " ".join(list(HOUSE_MEANINGS.values()) + list(PLANET_SIGNIFICATIONS.values())).lower()
    for forbidden in ("death", "die", "lifespan", "fatal", "disease", "diagnos"):
        assert forbidden not in blob


# --- System A --------------------------------------------------------------
def test_life_summary_has_five_populated_public_cards(life_summary):
    assert life_summary["available_sections"] == 5
    assert life_summary["total_sections"] == 5
    for section in life_summary["sections"]:
        assert section["status"] == "available"
        assert section["body"]
        assert "not yet been added" not in section["body"]


def test_life_summary_public_layer_leaks_no_methodology(life_summary):
    blob = str(life_summary["sections"]).lower()
    for forbidden in ("vaar", "tithi", "karana", "nakshatra", "yoga.", "lagna", "rashi",
                      "own sign", "exalted", "debilitated", "dignity", "rule_id"):
        assert forbidden not in blob
    for planet in PLANET_SIGNIFICATIONS:
        assert planet.lower() not in blob


def test_life_summary_uses_birth_moment_and_birth_d1(birth_channels):
    assert birth_channels["system"] == "A"
    assert birth_channels["moment"] == "birth_moment"
    assert str(birth_channels["reference"]).startswith("1990-05-15T14:15")
    assert set(birth_channels["channels"]) == set(CHANNELS)
    for channel in CHANNELS:
        data = birth_channels["channels"][channel]
        assert data["available"] is True
        assert data["public_text"]
        assert data["planet_house"]


def test_life_summary_has_no_question_moment_dependency():
    parameters = inspect.signature(build_channel_interpretations).parameters
    for forbidden in ("question_timestamp", "is_follow_up", "original_timestamp", "question"):
        assert forbidden not in parameters


# --- System B --------------------------------------------------------------
def test_ask_uses_question_moment_and_five_channels(ask_answer):
    assert ask_answer["used_timestamp"] == WHEN
    assert set(ask_answer["channels"]) == set(CHANNELS)
    relevant = ask_answer["prashna"]["relevant_channels"]
    assert relevant["primary"] in CHANNELS
    assert relevant["supporting"]


def test_ask_answer_is_not_the_raw_five_channel_dump(ask_answer):
    answer = ask_answer["answer"]
    assert answer
    assert len(answer) > 100
    used = sum(
        1 for channel in CHANNELS
        if (ask_answer["channels"][channel].get("public_text") or "") in answer
    )
    assert used <= 3


def test_birth_moment_and_question_moment_differ(birth_channels, ask_answer):
    assert birth_channels["reference"] != "question_moment"
    assert ask_answer["prashna"]["lords"] != birth_channels["lords"]


def test_ask_has_no_birth_dependency():
    parameters = inspect.signature(answer_question).parameters
    for forbidden in ("birth_date", "birth_time", "birth_place", "natal", "chart"):
        assert forbidden not in parameters


def test_daily_moon_is_supplementary_only(ask_answer):
    signals = ask_answer["prashna"]["signals"]
    assert all(signal["role"] == "supplementary" for signal in signals)


def test_invalid_text_generates_no_reading():
    result = answer_question("sa", WHEN, *DELHI)
    assert result["status"] == "invalid_input"
    assert result["answered"] is False
    assert result["channels"] is None
    assert "does not look like a question" in result["answer"]


def test_ask_answer_has_no_guaranteed_outcomes(ask_answer):
    text = ask_answer["answer"].lower()
    for forbidden in ("will definitely", "guaranteed to", "is guaranteed", "100 percent", "shadbala"):
        assert forbidden not in text


def test_routing_keeps_every_house_available():
    assert set(HOUSE_MEANINGS) == set(range(1, 13))
