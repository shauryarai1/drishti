"""KAVACH YES / NO: number reduction, zero handling and the planet registry."""

from __future__ import annotations

import pytest

from yesno.numbers import ZERO_HANDLING, hour_number, minute_number, reduce_to_single_digit
from yesno.planets import NUMBER_TO_PLANET, PLANET_THEMES, planet_for_number


# --- reduction ---------------------------------------------------------------
@pytest.mark.parametrize("value,expected", [
    (15, 6), (53, 8), (49, 4), (38, 2), (27, 9), (59, 5), (23, 5),
    (10, 1), (20, 2), (5, 5), (9, 9), (1, 1),
])
def test_reduce_to_single_digit(value, expected):
    assert reduce_to_single_digit(value) == expected


def test_repeated_reduction_59():
    """59 -> 5 + 9 -> 14 -> 1 + 4 -> 5."""
    assert reduce_to_single_digit(59) == 5


@pytest.mark.parametrize("value,expected", [(0, ZERO_HANDLING), (9, 9), (18, 9), (90, 9)])
def test_reduction_never_returns_zero(value, expected):
    result = reduce_to_single_digit(value)
    assert result != 0, "the reduction must never produce 0"
    assert 1 <= result <= 9
    assert result == expected


def test_zero_handling_is_documented_and_explicit():
    """0 has no planet, so the rule is an explicit constant pending approval."""
    assert ZERO_HANDLING == 9
    assert reduce_to_single_digit(0) == ZERO_HANDLING


# --- hour and minute are reduced separately ---------------------------------
@pytest.mark.parametrize("hour,minute,h_expected,m_expected", [
    (15, 53, 6, 8),
    (15, 49, 6, 4),
    (12, 38, 3, 2),
    (23, 59, 5, 5),
    (9, 27, 9, 9),
    (10, 5, 1, 5),
])
def test_hour_and_minute_are_independent(hour, minute, h_expected, m_expected):
    assert hour_number(hour) == h_expected
    assert minute_number(minute) == m_expected


def test_hour_and_minute_are_never_added_together():
    """15:53 is 6 and 8 - not 14, and not 5."""
    assert (hour_number(15), minute_number(53)) == (6, 8)
    assert reduce_to_single_digit(6 + 8) == 5, "adding them would give a different number"


# --- number -> planet --------------------------------------------------------
def test_number_to_planet_mapping_is_exact():
    assert dict(NUMBER_TO_PLANET) == {
        1: "Sun", 2: "Moon", 3: "Jupiter", 4: "Rahu", 5: "Mercury",
        6: "Venus", 7: "Ketu", 8: "Saturn", 9: "Mars",
    }


@pytest.mark.parametrize("number,planet", [
    (1, "Sun"), (2, "Moon"), (3, "Jupiter"), (4, "Rahu"), (5, "Mercury"),
    (6, "Venus"), (7, "Ketu"), (8, "Saturn"), (9, "Mars"),
])
def test_planet_for_number(number, planet):
    assert planet_for_number(number) == planet


def test_registry_is_immutable_and_has_no_zero():
    assert 0 not in NUMBER_TO_PLANET
    assert len(NUMBER_TO_PLANET) == 9
    with pytest.raises(TypeError):
        NUMBER_TO_PLANET[10] = "Pluto"  # type: ignore[index]


@pytest.mark.parametrize("bad", [0, 10, -1, None, "x"])
def test_planet_for_number_rejects_invalid(bad):
    with pytest.raises(ValueError):
        planet_for_number(bad)


def test_every_planet_has_themes():
    for planet in NUMBER_TO_PLANET.values():
        assert PLANET_THEMES.get(planet), planet
