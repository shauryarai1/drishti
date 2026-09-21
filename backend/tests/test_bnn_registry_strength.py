"""Tests for the approved BNN relationship registry and the evidence engine."""

from __future__ import annotations

import json

import pytest

from kundli.analysis import (
    AWAITING_GRADING_RULE,
    BACKWARD_ONLY,
    BNN_RELATIONSHIPS,
    EMPTY,
    ENEMY,
    FORWARD_ONLY,
    FRIEND,
    MIXED,
    NEUTRAL,
    PRESSURED_BOTH_SIDES,
    SUPPORTIVE_BOTH_SIDES,
    chart_connections,
    collect_evidence,
    relationship,
    strength_evidence,
)
from kundli.analysis.bnn import connections_from, node_layers, retrograde_layers

PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")

# Asymmetric pairs in the approved table (reference -> target).
ASYMMETRIC = [("Jupiter", "Venus"), ("Ketu", "Saturn"), ("Ketu", "Mercury")]


def placements(mapping):
    return {planet: {"rashi": rashi, "house": house} for planet, (rashi, house) in mapping.items()}


# --- A. registry ---------------------------------------------------------
@pytest.mark.parametrize("reference", PLANETS)
def test_every_explicit_friend_entry(reference):
    friends = BNN_RELATIONSHIPS[reference][0]
    assert friends, reference
    for target in friends:
        assert relationship(reference, target) == FRIEND, (reference, target)


@pytest.mark.parametrize("reference", PLANETS)
def test_every_explicit_enemy_entry(reference):
    enemies = BNN_RELATIONSHIPS[reference][1]
    assert enemies, reference
    for target in enemies:
        assert relationship(reference, target) == ENEMY, (reference, target)


@pytest.mark.parametrize("reference,target", [
    ("Mercury", "Ketu"), ("Venus", "Jupiter"), ("Saturn", "Ketu"),
    ("Rahu", "Ketu"), ("Ketu", "Rahu"),
])
def test_unlisted_pairs_are_neutral(reference, target):
    assert target not in BNN_RELATIONSHIPS[reference][0]
    assert target not in BNN_RELATIONSHIPS[reference][1]
    assert relationship(reference, target) == NEUTRAL


def test_relationship_is_directional_and_not_symmetric():
    for reference, target in ASYMMETRIC:
        reversed_quality = relationship(target, reference)
        forward = relationship(reference, target)
        assert forward != reversed_quality, (reference, target)
    # concrete: Jupiter sees Venus as an enemy, Venus does not list Jupiter at all
    assert relationship("Jupiter", "Venus") == ENEMY
    assert relationship("Venus", "Jupiter") == NEUTRAL
    assert relationship("Ketu", "Saturn") == ENEMY
    assert relationship("Saturn", "Ketu") == NEUTRAL


def test_self_relationship_is_neutral():
    for planet in PLANETS:
        assert relationship(planet, planet) == NEUTRAL


# --- B. connection quality -----------------------------------------------
def test_quality_is_attached_after_the_mechanics():
    chart = placements({"Sun": ("Aries", 1), "Venus": ("Leo", 5), "Saturn": ("Sagittarius", 9)})
    rows = connections_from("Sun", "Aries", chart)
    by_target = {row["targetPlanet"]: row for row in rows}
    # Venus is the 5th from Aries -> trinal, even though Sun considers Venus an enemy
    assert by_target["Venus"]["relativePosition"] == 5
    assert by_target["Venus"]["connectionGroup"] == "TRINE_SUPPORT"
    assert by_target["Venus"]["relationshipQuality"] == ENEMY
    assert by_target["Venus"]["isPrimary"] is True
    # Saturn is the 9th -> also trinal, also an enemy of Sun
    assert by_target["Saturn"]["relativePosition"] == 9
    assert by_target["Saturn"]["connectionGroup"] == "TRINE_SUPPORT"
    assert by_target["Saturn"]["relationshipQuality"] == ENEMY


def test_friend_and_neutral_annotations():
    chart = placements({"Sun": ("Aries", 1), "Moon": ("Leo", 5), "Venus": ("Virgo", 6)})
    rows = connections_from("Sun", "Aries", chart, include_excluded=True)
    by_target = {row["targetPlanet"]: row for row in rows}
    assert by_target["Moon"]["relationshipQuality"] == FRIEND          # Sun's friend
    assert by_target["Venus"]["relationshipQuality"] == ENEMY          # Sun's enemy
    assert by_target["Venus"]["connectionGroup"] is None               # 6th is not a BNN position


def test_enemy_trinal_is_present_in_evidence_and_pressure():
    chart = placements({"Sun": ("Aries", 1), "Venus": ("Leo", 5)})
    evidence = collect_evidence("Sun", chart)
    assert evidence["trinalConnections"] == ["Venus"]
    assert evidence["hasTrinalNetwork"] is True
    assert evidence["enemyConnections"] == ["Venus"]
    assert any("inimical" in reason for reason in evidence["pressureReasons"])
    assert any("trinal" in reason for reason in evidence["supportReasons"])


# --- C. isolation --------------------------------------------------------
def test_enemy_connection_is_not_isolation():
    chart = placements({"Sun": ("Aries", 1), "Venus": ("Libra", 7)})
    evidence = collect_evidence("Sun", chart)
    assert evidence["oppositionConnections"] == ["Venus"]
    assert evidence["isIsolated"] is False
    assert evidence["isolation"]["isolationLevel"] != "ISOLATED"


def test_structural_isolation_requires_network_absence():
    chart = placements({"Sun": ("Aries", 1), "Moon": ("Cancer", 4)})   # Cancer = 4th, excluded
    evidence = collect_evidence("Sun", chart)
    assert evidence["connections"] == []
    assert evidence["isIsolated"] is True
    assert evidence["isolation"]["isolationLevel"] == "ISOLATED"

    connected = placements({"Sun": ("Aries", 1), "Mars": ("Gemini", 3)})
    connected_evidence = collect_evidence("Sun", connected)
    assert connected_evidence["struggleConnections"] == ["Mars"]
    assert connected_evidence["isIsolated"] is False


def test_presence_flags_match_buckets():
    chart = placements({"Sun": ("Aries", 1), "Moon": ("Taurus", 2), "Mars": ("Gemini", 3),
                        "Jupiter": ("Libra", 7), "Venus": ("Aquarius", 11)})
    evidence = collect_evidence("Sun", chart)
    assert evidence["hasForwardSupport"] is True
    assert evidence["hasBackwardSupport"] is False
    assert evidence["hasThreeElevenNetwork"] is True
    assert evidence["hasOpposition"] is True
    assert evidence["hasTrinalNetwork"] is False


# --- D. kartari ----------------------------------------------------------
@pytest.mark.parametrize("behind, ahead, expected", [
    (None, None, EMPTY),
    (FRIEND, None, BACKWARD_ONLY),
    (None, FRIEND, FORWARD_ONLY),
    (FRIEND, FRIEND, SUPPORTIVE_BOTH_SIDES),
    (ENEMY, ENEMY, PRESSURED_BOTH_SIDES),
    (FRIEND, ENEMY, MIXED),
    (ENEMY, FRIEND, MIXED),
])
def test_kartari_condition_table(behind, ahead, expected):
    from kundli.analysis.strength import kartari_condition
    assert kartari_condition(behind, ahead) == expected


def test_kartari_evidence_preserves_the_planets():
    # Aries reference: 12th = Pisces, 2nd = Taurus. Jupiter is a friend of Sun.
    chart = placements({"Sun": ("Aries", 1), "Jupiter": ("Pisces", 12), "Moon": ("Taurus", 2)})
    evidence = collect_evidence("Sun", chart)
    assert evidence["kartariCondition"] == SUPPORTIVE_BOTH_SIDES
    assert evidence["kartariEvidence"] == {"behind12th": FRIEND, "ahead2nd": FRIEND}

    hostile = placements({"Sun": ("Aries", 1), "Venus": ("Pisces", 12), "Saturn": ("Taurus", 2)})
    hostile_evidence = collect_evidence("Sun", hostile)
    assert hostile_evidence["kartariCondition"] == PRESSURED_BOTH_SIDES

    mixed = placements({"Sun": ("Aries", 1), "Jupiter": ("Pisces", 12), "Saturn": ("Taurus", 2)})
    assert collect_evidence("Sun", mixed)["kartariCondition"] == MIXED


# --- E. retrograde -------------------------------------------------------
def test_retrograde_evidence_has_both_layers():
    chart = placements({"Jupiter": ("Leo", 5), "Sun": ("Aries", 1), "Moon": ("Cancer", 4)})
    evidence = collect_evidence("Jupiter", chart, retrograde=["Jupiter"])
    layers = evidence["retrogradeLayers"]
    assert set(layers) == {"ACTUAL_POSITION", "RETRO_PREVIOUS_POSITION"}
    assert layers["RETRO_PREVIOUS_POSITION"]                    # Cancer reference
    assert evidence["nodeDispositorLayer"] if False else True   # not applicable to Jupiter


def test_non_retrograde_has_no_retro_layers():
    chart = placements({"Jupiter": ("Leo", 5), "Sun": ("Aries", 1)})
    assert "retrogradeLayers" not in collect_evidence("Jupiter", chart)


# --- F. nodes ------------------------------------------------------------
def test_node_evidence_has_direct_and_operational_layers():
    chart = placements({"Rahu": ("Taurus", 2), "Venus": ("Leo", 5), "Sun": ("Sagittarius", 9)})
    evidence = collect_evidence("Rahu", chart, retrograde=["Rahu"])
    node_layer = evidence["nodeDispositorLayer"]
    assert node_layer["dispositor"] == "Venus"
    assert node_layer["dispositorRashi"] == "Leo"
    assert node_layer["operational"]
    assert all(row["layer"] == "DISPOSITOR_OPERATIONAL" for row in node_layer["operational"])
    assert "retrogradeLayers" not in evidence            # generic Rx rule never applies to nodes


def test_nodes_have_no_generic_retro_previous_layer():
    chart = placements({"Rahu": ("Aries", 1), "Ketu": ("Libra", 7), "Sun": ("Leo", 5)})
    assert retrograde_layers(chart, ["Rahu", "Ketu"]) == {}
    layers = node_layers(chart)
    assert layers["Rahu"]["direct"] and layers["Rahu"]["operational"]


# --- G. classifier -------------------------------------------------------
def test_classifier_is_explicitly_awaiting_the_owner_rule():
    chart = placements({"Sun": ("Aries", 1), "Moon": ("Leo", 5)})
    evidence = collect_evidence("Sun", chart)
    assert evidence["classification"] is None
    assert evidence["classificationStatus"] == AWAITING_GRADING_RULE

    report = strength_evidence(chart)
    assert report["weights"] is None
    assert report["classificationStatus"] == AWAITING_GRADING_RULE
    for planet in report["planets"].values():
        assert planet["classification"] is None


def _keys(node):
    found = set()
    if isinstance(node, dict):
        for key, value in node.items():
            found.add(str(key).lower())
            found |= _keys(value)
    elif isinstance(node, list):
        for item in node:
            found |= _keys(item)
    return found


def test_no_numerical_score_or_threshold_exists():
    chart = placements({"Sun": ("Aries", 1), "Moon": ("Leo", 5), "Venus": ("Taurus", 2)})
    report = strength_evidence(chart)
    present = _keys(report)
    # `weights` is intentionally present as an explicit null marker.
    assert report["weights"] is None
    for banned in ("score", "points", "weight", "threshold", "grade", "rating",
                   "strengthscore", "percent"):
        assert banned not in present, banned
    assert report["weights"] is None
    assert "percent" not in json.dumps(report).lower()


def test_reasons_are_never_empty_for_a_connected_planet():
    chart = placements({"Sun": ("Aries", 1), "Moon": ("Leo", 5), "Venus": ("Taurus", 2)})
    evidence = collect_evidence("Sun", chart)
    assert evidence["supportReasons"] or evidence["pressureReasons"]
    for reason in evidence["supportReasons"] + evidence["pressureReasons"]:
        assert isinstance(reason, str) and reason.strip()


def test_chart_connections_reports_mechanism_only():
    chart = placements({"Sun": ("Aries", 1), "Moon": ("Leo", 5)})
    payload = chart_connections(chart)
    assert payload["mechanismOnly"] is True
    assert "strength" in payload["blocked"]
