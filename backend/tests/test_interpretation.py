from types import SimpleNamespace
from unittest.mock import patch

import pytest

from interpretation import compute_interpretation


def fake_chart(mars_sign):
    return SimpleNamespace(
        planets=[SimpleNamespace(name="Mars", sign=mars_sign, house=1, degree=12.3)],
        extra_planets=[],
        ascendant=SimpleNamespace(sign="Aries"),
        houses=[],
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
