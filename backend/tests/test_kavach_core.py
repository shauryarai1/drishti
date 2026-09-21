"""KAVACH core knowledge, posture and public-output acceptance tests."""

from __future__ import annotations

import inspect

import pytest
from fastapi.testclient import TestClient

from jyotish.houses import HOUSE_MEANINGS
from jyotish.planets import (
    CLASSICAL_PLANETS,
    DEBILITATION,
    EXALTATION,
    NODES,
    PLANET_SIGNIFICATIONS,
    RASHI_ALIASES,
    RULERSHIP,
    dignity,
)
from kavach_core.knowledge.graha_bhava import GRAHA_BHAVA
from kavach_core.lens import CHANNELS, interpret_placement
from kavach_core.mappings import KARANA_LORDS, NAKSHATRA_LORDS, TITHI_LORDS, VAAR_LORDS, YOGA_LORDS
from main import app
from prediction.panchang_natal.summary import build_channel_interpretations, build_life_summary
from question_engine.engine import answer_question

ALL_PLANETS = list(CLASSICAL_PLANETS) + list(NODES)
DELHI = (28.6139, 77.2090, "Asia/Kolkata", "New Delhi")
WHEN = "2026-09-20T14:15:00+05:30"
PUBLIC_FORBIDDEN = ("vaar", "tithi", "karana", "nakshatra", "yoga", "lagna", "bhava",
                    "rashi", "house", "channel", "dignity", "rule_id", "source_type",
                    "could not be composed", "interpretation rule", "significator")


@pytest.fixture(scope="module")
def life_summary():
    return build_life_summary("1990-05-15", "14:15", *DELHI)


@pytest.fixture(scope="module")
def birth_channels():
    return build_channel_interpretations("1990-05-15", "14:15", *DELHI)


@pytest.fixture(scope="module")
def ask_answer():
    return answer_question("How will my interview go?", WHEN, *DELHI)


# --- A / B: knowledge base -------------------------------------------------
def test_a_all_108_graha_bhava_entries_exist():
    assert len(GRAHA_BHAVA) == 9
    for planet in ALL_PLANETS:
        assert sorted(GRAHA_BHAVA[planet]) == list(range(1, 13)), planet


def test_b_entries_are_placement_specific_not_keyword_assembly():
    themes = []
    for planet in ALL_PLANETS:
        for house in range(1, 13):
            entry = GRAHA_BHAVA[planet][house]
            assert len(entry["themes"]) >= 3
            assert entry["constructive"] and entry["challenging"] and entry["guidance"]
            for text, tags in entry["themes"]:
                assert len(text.split()) >= 6, text
                assert tags, text
                themes.append(text)
    assert len(set(themes)) >= int(len(themes) * 0.5)  # wide lexical variety


def test_mappings_match_the_astrologers_tables():
    assert VAAR_LORDS == {0: "Moon", 1: "Mars", 2: "Mercury", 3: "Jupiter",
                          4: "Venus", 5: "Saturn", 6: "Sun"}
    for number, lord in ((1, "Sun"), (5, "Jupiter"), (8, "Rahu"), (9, "Sun"),
                         (14, "Venus"), (15, "Saturn")):
        assert TITHI_LORDS[number] == lord
    assert KARANA_LORDS["Taitila"] == "Mercury"
    assert KARANA_LORDS["Garaja"] == "Jupiter"
    assert KARANA_LORDS["Chatushpada"] == "Ketu"
    assert YOGA_LORDS[1] == "Ketu" and YOGA_LORDS[23] == "Mars" and YOGA_LORDS[27] == "Mercury"
    assert NAKSHATRA_LORDS["Ketu"] == ["Ashvini", "Magha", "Mula"]


# --- C / D: dignity -------------------------------------------------------
@pytest.mark.parametrize("planet,sign", [(p, s) for p, s in EXALTATION.items() if s not in RULERSHIP.get(p, [])])
def test_c_exaltation(planet, sign):
    assert dignity(planet, sign) == "exalted"


@pytest.mark.parametrize("planet,sign", list(DEBILITATION.items()))
def test_c_debilitation(planet, sign):
    assert dignity(planet, sign) == "debilitated"


def test_c_own_sign_and_neutral():
    assert dignity("Sun", "Simha") == "own_sign"
    assert dignity("Mars", "Mesha") == "own_sign"
    assert dignity("Jupiter", "Mithuna") == "neutral"


def test_d_nodes_have_no_disputed_dignity():
    for node in NODES:
        for rashi in RASHI_ALIASES:
            assert dignity(node, rashi) == "not_assigned"


# --- E: channel lens ------------------------------------------------------
def test_e_same_placement_differs_across_all_channels():
    outputs = [
        interpret_placement("Jupiter", 2, "Dhanu", "own_sign", channel)["public_text"]
        for channel in CHANNELS
    ]
    assert all(outputs)
    assert len(set(outputs)) == len(CHANNELS)


def test_e_every_placement_has_text_in_every_channel():
    for planet in ALL_PLANETS:
        for house in range(1, 13):
            for channel in CHANNELS:
                result = interpret_placement(planet, house, "Mesha", dignity(planet, "Mesha"), channel)
                assert result["available"] is True
                assert result["public_text"]


# --- F / G / H: moment separation ----------------------------------------
def test_f_system_a_uses_the_birth_moment(birth_channels):
    assert birth_channels["system"] == "A"
    assert birth_channels["moment"] == "birth_moment"
    assert birth_channels["reference"].startswith("1990-05-15T14:15")


def test_g_system_b_uses_the_exact_question_moment(ask_answer):
    assert ask_answer["system"] == "B"
    assert ask_answer["used_timestamp"] == WHEN
    assert ask_answer["uses_birth_details"] is False


def test_h_system_b_has_no_birth_dependency():
    parameters = inspect.signature(answer_question).parameters
    for forbidden in ("birth_date", "birth_time", "birth_place", "natal", "chart"):
        assert forbidden not in parameters


def test_f_g_moments_are_independent(birth_channels, ask_answer):
    assert birth_channels["reference"] != ask_answer["used_timestamp"]
    assert birth_channels["lords"] != ask_answer["prashna"]["lords"]


# --- I / J / K / L: message validity -------------------------------------
@pytest.mark.parametrize("message", ["sa", "ads", "sda", "asdads", "...."])
def test_i_nonsense_never_produces_a_reading(message):
    result = answer_question(message, WHEN, *DELHI)
    assert result["status"] == "invalid_input"
    assert result["channels"] is None
    assert "does not look like a question" in result["answer"]


@pytest.mark.parametrize("greeting", ["hi", "hello"])
def test_j_greetings_are_conversational(greeting):
    result = answer_question(greeting, WHEN, *DELHI)
    assert result["status"] == "greeting"
    assert result["answered"] is False
    assert result["channels"] is None


@pytest.mark.parametrize("question", ["job?", "exam?", "love?", "money?"])
def test_k_meaningful_short_questions_are_valid(question):
    result = answer_question(question, WHEN, *DELHI)
    assert result["answered"] is True
    assert result["status"] in ("supportive", "mixed", "extra_care", "unclear")


def test_l_follow_up_retains_the_original_moment():
    result = answer_question(
        "What should I watch for?", "2026-09-20T14:16:00+05:30", *DELHI,
        is_follow_up=True, original_timestamp=WHEN,
    )
    assert result["used_timestamp"] == WHEN
    assert result["is_follow_up"] is True


def test_l_nonsense_after_a_real_question_is_still_invalid():
    result = answer_question(
        "ads", "2026-09-20T14:16:00+05:30", *DELHI,
        is_follow_up=True, original_timestamp=WHEN,
    )
    assert result["status"] == "invalid_input"


# --- M: daily moon is supplementary --------------------------------------
def test_m_daily_moon_is_one_supplementary_signal(ask_answer):
    signals = ask_answer["prashna"]["signals"]
    assert len(signals) <= 1
    assert all(signal["role"] == "supplementary" for signal in signals)


# --- N / O: public leakage -------------------------------------------------
def test_n_public_ask_leaks_no_internals():
    client = TestClient(app)
    for message in ("How will my interview go?", "sa", "hi"):
        response = client.post("/api/ask", json={
            "question": message, "timestamp": WHEN, "latitude": 28.6139,
            "longitude": 77.209, "timezone": "Asia/Kolkata", "location_label": "New Delhi"})
        assert response.status_code == 200
        body = response.json()
        assert set(body) == {"status", "answered", "answer", "conversation_id"}
        blob = str(body).lower()
        for forbidden in PUBLIC_FORBIDDEN:
            assert forbidden not in blob, forbidden


def test_o_public_life_summary_leaks_no_internals(life_summary):
    blob = str(life_summary["sections"]).lower()
    for forbidden in PUBLIC_FORBIDDEN:
        assert forbidden not in blob, forbidden
    for planet in ALL_PLANETS:
        assert planet.lower() not in blob


# --- P / Q / R / S / T: public language -----------------------------------
def _public_texts(life_summary, ask_answer):
    texts = [ask_answer["answer"]] + [section["body"] for section in life_summary["sections"]]
    return " ".join(texts).lower()


def test_p_no_lifespan_or_death_content(life_summary, ask_answer):
    blob = _public_texts(life_summary, ask_answer)
    for forbidden in ("death", "die", "lifespan", "fatal", "shorten your life"):
        assert forbidden not in blob


def test_q_no_medical_content(life_summary, ask_answer):
    blob = _public_texts(life_summary, ask_answer)
    for forbidden in ("diagnos", "disease", "cancer", "illness", "cure"):
        assert forbidden not in blob


def test_r_no_guaranteed_outcomes(life_summary, ask_answer):
    blob = _public_texts(life_summary, ask_answer)
    for forbidden in ("will definitely", "guaranteed to", "is guaranteed", "certain to happen"):
        assert forbidden not in blob


def test_s_no_numeric_scores(life_summary, ask_answer):
    blob = _public_texts(life_summary, ask_answer)
    for forbidden in ("shadbala", "probability", "percent", "score of", "confidence score"):
        assert forbidden not in blob


def test_t_no_placeholders_or_errors(life_summary, ask_answer):
    blob = _public_texts(life_summary, ask_answer)
    for forbidden in ("could not be composed", "has not yet been added", "not available",
                      "pending", "placeholder", "undefined"):
        assert forbidden not in blob
    for section in life_summary["sections"]:
        assert section["status"] == "available"
        assert len(section["body"]) > 80


def test_life_summary_style_is_human_not_keyword_joined(life_summary):
    blob = " ".join(section["body"] for section in life_summary["sections"]).lower()
    for banned in ("channelled into", "is connected with", "expressed through",
                   "comparatively supportive structural context"):
        assert banned not in blob
