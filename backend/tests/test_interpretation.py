from types import SimpleNamespace
from unittest.mock import patch

import pytest

from interpretation import HOUSE_LIFE_AREAS, compute_interpretation


def fake_chart(mars_sign):
    return SimpleNamespace(
        planets=[SimpleNamespace(name="Mars", sign=mars_sign, house=1, degree=12.3)],
        extra_planets=[],
        ascendant=SimpleNamespace(sign="Aries"),
        houses=[],
    )


def chart_with_ascendant(ascendant_sign):
    signs = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
    ]
    ascendant_index = signs.index(ascendant_sign)
    return SimpleNamespace(
        planets=[SimpleNamespace(name="Mars", sign="Aries", house=1, degree=12.3)],
        extra_planets=[],
        ascendant=SimpleNamespace(sign=ascendant_sign),
        houses=[
            SimpleNamespace(number=index + 1, sign=signs[(ascendant_index + index) % 12])
            for index in range(12)
        ],
    )


@pytest.mark.parametrize(
    ("mars_sign", "protect_phrase", "danger_phrase", "attention_phrase"),
    [
        ("Aries", "attachment", "insecurity", "Do not act without thinking"),
        ("Libra", "workplace disputes", "food, speech", "healthy boundaries"),
        ("Pisces", "communication", "possessiveness", "fixed way of thinking"),
    ],
)
def test_interpretation_layers_use_the_correct_rashis(
    mars_sign, protect_phrase, danger_phrase, attention_phrase
):
    with patch("interpretation.generate_chart", return_value=fake_chart(mars_sign)):
        result = compute_interpretation(None)

    assert result["attention"]["description"]
    assert result["protect"]["description"]
    assert result["danger"]["description"]
    assert result["attention"]["area"] != result["protect"]["area"]
    assert protect_phrase in result["protect"]["description"]
    assert danger_phrase in result["danger"]["description"]
    assert attention_phrase.lower() in result["attention"]["description"].lower()
    assert "current" in result["timing"]
    assert "upcoming" in result["timing"]


def test_danger_copy_does_not_make_guaranteed_harm_predictions():
    with patch("interpretation.generate_chart", return_value=fake_chart("Capricorn")):
        result = compute_interpretation(None)

    danger_text = result["danger"]["description"].lower()
    assert "serious" in danger_text or "bigger problems" in danger_text
    assert "guaranteed" not in danger_text
    assert "will happen" not in danger_text


def test_mars_rashi_aspect_selection_and_response_shape_remain_unchanged():
    with patch("interpretation.generate_chart", return_value=fake_chart("Aries")):
        result = compute_interpretation(None)

    # Mars Aries, plus 3 signs Cancer, plus 7 signs Scorpio.
    assert result["attention"]["rashi"] == "Aries"
    assert result["protect"]["rashi"] == "Cancer"
    assert result["danger"]["rashi"] == "Scorpio"
    assert {"status", "attention", "protect", "danger", "timing", "chart"} <= result.keys()


def test_highlighted_rashi_uses_the_actual_d1_house():
    with patch("interpretation.generate_chart", return_value=chart_with_ascendant("Aries")):
        aries_ascendant = compute_interpretation(None)
    with patch("interpretation.generate_chart", return_value=chart_with_ascendant("Cancer")):
        cancer_ascendant = compute_interpretation(None)

    assert aries_ascendant["attention"]["rashi"] == "Aries"
    assert cancer_ascendant["attention"]["rashi"] == "Aries"
    assert aries_ascendant["attention"]["house"] == 1
    assert cancer_ascendant["attention"]["house"] == 10
    assert aries_ascendant["attention"]["life_area"] == HOUSE_LIFE_AREAS[1]
    assert cancer_ascendant["attention"]["life_area"] == HOUSE_LIFE_AREAS[10]


@pytest.mark.parametrize(
    ("house_number", "life_area", "unexpected_phrase"),
    [
        (5, "creativity, education, children, romance, and judgment", "organisation"),
        (6, "work, service, health, discipline, obstacles, and debts", ""),
        (10, "profession, authority, reputation, and public responsibilities", ""),
    ],
)
def test_virgo_danger_integrates_the_house_domain(house_number, life_area, unexpected_phrase):
    chart = SimpleNamespace(
        planets=[SimpleNamespace(name="Mars", sign="Aquarius", house=1, degree=12.3)],
        extra_planets=[],
        ascendant=SimpleNamespace(sign="Aries"),
        houses=[SimpleNamespace(number=house_number, sign="Virgo")],
    )
    with patch("interpretation.generate_chart", return_value=chart):
        result = compute_interpretation(None)

    danger = result["danger"]
    assert danger["rashi"] == "Virgo"
    assert danger["house"] == house_number
    assert danger["life_area"] == life_area
    assert "many skills and significant potential" in danger["description"]
    assert "lack of discipline and other unresolved weaknesses" in danger["description"]
    assert "Develop discipline and consistent work" in danger["description"]
    assert "may face setbacks" in danger["description"]
    if unexpected_phrase:
        assert unexpected_phrase not in danger["description"]


def test_virgo_danger_house_10_keeps_internal_mapping_out_of_public_copy():
    chart = SimpleNamespace(
        planets=[SimpleNamespace(name="Mars", sign="Aquarius", house=1, degree=12.3)],
        extra_planets=[],
        ascendant=SimpleNamespace(sign="Aries"),
        houses=[SimpleNamespace(number=10, sign="Virgo")],
    )
    with patch("interpretation.generate_chart", return_value=chart):
        danger = compute_interpretation(None)["danger"]

    # The engine still resolves the real house and life area internally.
    assert danger["house"] == 10
    assert danger["life_area"] == "profession, authority, reputation, and public responsibilities"
    assert "highly capable and valuable in this area" in danger["description"]

    # Public copy must not reveal the house mapping or the planetary method.
    public_text = danger["description"].lower() + " " + danger["area"].lower()
    for forbidden in ("mars", "mangal", "rashi", "aspect", "house", "d1"):
        assert forbidden not in public_text


def test_public_reading_areas_do_not_reveal_the_internal_method():
    with patch("interpretation.generate_chart", return_value=fake_chart("Cancer")):
        result = compute_interpretation(None)

    public_text = " ".join(
        result[layer][field]
        for layer in ("attention", "protect", "danger")
        for field in ("area", "description")
    ).lower()

    for forbidden in ("mars", "mangal", "saturn", "shani", "rahu", "ketu", "rashi", "aspect", "transit", "house", "d1"):
        assert forbidden not in public_text

