"""KAVACH YES / NO: the approved directional BNN relationship registry.

The feature must read the project's approved registry and must never invent,
infer symmetry or substitute Parashari natural friendship.
"""

from __future__ import annotations

import pytest

from kundli.analysis.relationships import (
    ENEMY,
    FRIEND,
    NEUTRAL,
    PLANETS,
    BNN_RELATIONSHIPS,
    relationship as approved_relationship,
)

from yesno.relationships import (
    EVEN,
    NO,
    RELATIONSHIP_MATRIX,
    RELATIONSHIP_VERDICTS,
    YES,
    planet_relationship,
    registry_status,
    verdict_for_relationship,
)

# --- the required example ----------------------------------------------------
def test_venus_to_saturn_is_friend_and_yes():
    assert approved_relationship("Venus", "Saturn") == FRIEND
    assert planet_relationship("Venus", "Saturn") == FRIEND
    assert verdict_for_relationship(planet_relationship("Venus", "Saturn")) == YES


def test_verdict_mapping_is_exact():
    assert RELATIONSHIP_VERDICTS[FRIEND] == YES
    assert RELATIONSHIP_VERDICTS[ENEMY] == NO
    assert RELATIONSHIP_VERDICTS[NEUTRAL] == EVEN
    assert (YES, NO, EVEN) == ("YES", "NO", "50/50")


def test_unknown_relationship_is_rejected():
    with pytest.raises(ValueError):
        verdict_for_relationship("BEST_FRIEND")


# --- direction is respected --------------------------------------------------
def test_relationship_is_directional():
    """Jupiter -> Venus is an enemy; Venus -> Jupiter is neutral. Never reversed."""
    assert planet_relationship("Jupiter", "Venus") == ENEMY
    assert planet_relationship("Venus", "Jupiter") == NEUTRAL
    assert verdict_for_relationship(planet_relationship("Jupiter", "Venus")) == NO
    assert verdict_for_relationship(planet_relationship("Venus", "Jupiter")) == EVEN


def test_same_planet_is_neutral():
    for planet in PLANETS:
        assert planet_relationship(planet, planet) == NEUTRAL
        assert verdict_for_relationship(planet_relationship(planet, planet)) == EVEN


# --- no duplicated or invented matrix ---------------------------------------
def test_matrix_is_derived_from_the_approved_registry():
    for reference in PLANETS:
        for target in PLANETS:
            assert RELATIONSHIP_MATRIX[reference][target] == approved_relationship(reference, target)


def test_approved_registry_rows_are_consistent():
    assert set(BNN_RELATIONSHIPS) == set(PLANETS), "all nine planets have rows"
    for planet, (friends, enemies) in BNN_RELATIONSHIPS.items():
        assert not set(friends) & set(enemies), f"{planet} lists a planet as both friend and enemy"
        assert planet not in friends and planet not in enemies, f"{planet} lists itself"


def test_registry_status_reports_no_missing_relationships():
    status = registry_status()
    assert status["unresolved_pairs"] == [], "the approved matrix is complete"
    assert status["planets"] == list(PLANETS)
    assert status["counts"][NEUTRAL] == status["unspecified_pairs_treated_as_neutral"]
    assert sum(status["counts"].values()) == status["ordered_distinct_pairs"]
    assert status["source"] == "kundli.analysis.relationships.BNN_RELATIONSHIPS"


def test_every_ordered_pair_resolves():
    for reference in PLANETS:
        for target in PLANETS:
            assert planet_relationship(reference, target) in RELATIONSHIP_VERDICTS
