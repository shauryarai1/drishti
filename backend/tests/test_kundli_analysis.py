"""Deterministic tests for the KAVACH Kundli technical-analysis layer."""

from __future__ import annotations

import pytest

from kundli.analysis import (
    COMBUSTION_LIMITS,
    CONNECTION_GROUPS,
    DRISHTI,
    EXCLUDED_POSITIONS,
    PRIMARY_POSITIONS,
    angular_separation,
    atmakaraka,
    badhaka,
    chart_connections,
    connections_from,
    dignity_distribution,
    dispositor_chain,
    dispositor_of,
    element_distribution,
    is_combust,
    mala_shree,
    maraka,
    modality_distribution,
    moon_chart,
    node_layers,
    purushartha_distribution,
    relative_position,
    retrograde_layers,
    same_sign_conjunctions,
    sign_distance,
    standard_aspects,
    yogakaraka,
)


# --- helpers --------------------------------------------------------------
def placements(mapping):
    """mapping: planet -> (rashi, house)"""
    return {planet: {"rashi": rashi, "house": house} for planet, (rashi, house) in mapping.items()}


# --- signs / relative distance (§51) --------------------------------------
def test_relative_distance_one_to_twelve():
    assert sign_distance("Aries", "Aries") == 1
    assert sign_distance("Aries", "Taurus") == 2
    assert sign_distance("Aries", "Sagittarius") == 9
    assert sign_distance("Aries", "Pisces") == 12
    assert relative_position("Pisces", "Aquarius") == 12


def test_direction_is_preserved():
    assert relative_position("Aries", "Taurus") == 2
    assert relative_position("Taurus", "Aries") == 12
    assert relative_position("Aries", "Gemini") == 3
    assert relative_position("Gemini", "Aries") == 11


def test_primary_position_groups():
    assert CONNECTION_GROUPS[1] == CONNECTION_GROUPS[5] == CONNECTION_GROUPS[9] == "TRINE_SUPPORT"
    assert CONNECTION_GROUPS[2] == "FUTURE"
    assert CONNECTION_GROUPS[12] == "PAST"
    assert CONNECTION_GROUPS[3] == "STRUGGLE"
    assert CONNECTION_GROUPS[11] == "GAIN"
    assert CONNECTION_GROUPS[7] == "OPPOSITION_COMPLETION"


def test_primary_positions_exclude_4_6_8_10():
    assert PRIMARY_POSITIONS == (1, 5, 9, 2, 12, 3, 11, 7)
    assert EXCLUDED_POSITIONS == (4, 6, 8, 10)
    for position in EXCLUDED_POSITIONS:
        assert position not in CONNECTION_GROUPS


def test_connections_are_directional_and_exclude_4_6_8_10():
    chart = placements({"Sun": ("Aries", 1), "Mars": ("Cancer", 4), "Jupiter": ("Sagittarius", 9)})
    rows = connections_from("Sun", "Aries", chart)
    groups = {row["targetPlanet"]: (row["relativePosition"], row["connectionGroup"]) for row in rows}
    assert groups["Jupiter"] == (9, "TRINE_SUPPORT")
    # Mars sits at position 4, which is NOT primary BNN support, so by default
    # it is not part of the BNN connection set at all.
    assert "Mars" not in [row["targetPlanet"] for row in rows]
    excluded_rows = {row["targetPlanet"]: (row["relativePosition"], row["isPrimary"])
                     for row in connections_from("Sun", "Aries", chart, include_excluded=True)}
    assert excluded_rows["Mars"] == (4, False)

    reverse = connections_from("Jupiter", "Sagittarius", chart)
    # Sun is in Aries = 5th from Sagittarius (trinal), Mars in Cancer = 8th (excluded)
    assert {row["targetPlanet"]: row["relativePosition"] for row in reverse} == {"Sun": 5}

    include_excluded = connections_from("Sun", "Aries", chart, include_excluded=True)
    assert {row["targetPlanet"]: row["isPrimary"] for row in include_excluded}["Mars"] is False


def test_enemy_style_connection_is_still_recorded():
    # Connection existence never depends on friendship (which is unregistered).
    chart = placements({"Sun": ("Aries", 1), "Saturn": ("Leo", 5), "Venus": ("Sagittarius", 9)})
    rows = connections_from("Sun", "Aries", chart)
    assert {row["targetPlanet"] for row in rows} == {"Saturn", "Venus"}
    assert all(row["isPrimary"] for row in rows)


# --- retrograde (§52) ----------------------------------------------------
def test_retrograde_keeps_both_layers():
    chart = placements({"Jupiter": ("Leo", 5), "Sun": ("Aries", 1), "Moon": ("Cancer", 4)})
    layers = retrograde_layers(chart, ["Jupiter"])
    assert set(layers["Jupiter"]) == {"ACTUAL_POSITION", "RETRO_PREVIOUS_POSITION"}
    actual = layers["Jupiter"]["ACTUAL_POSITION"]
    previous = layers["Jupiter"]["RETRO_PREVIOUS_POSITION"]
    # previous rashi of Leo is Cancer -> Moon is 1st, Sun is 10th (excluded)
    assert {row["targetPlanet"] for row in previous} == {"Moon"}
    assert {row["targetPlanet"] for row in actual} == {"Sun", "Moon"}


def test_previous_rashi_wraps_from_aries_to_pisces():
    from kundli.analysis.bnn import previous_rashi
    assert previous_rashi("Aries") == "Pisces"


def test_non_retro_planet_has_no_previous_layer():
    chart = placements({"Sun": ("Aries", 1), "Mars": ("Leo", 5)})
    assert retrograde_layers(chart, []) == {}


def test_nodes_never_get_generic_retrograde_handling():
    chart = placements({"Rahu": ("Aries", 1), "Sun": ("Leo", 5)})
    assert retrograde_layers(chart, ["Rahu", "Ketu"]) == {}


# --- nodes (§53) ---------------------------------------------------------
def test_node_direct_and_operational_layers_are_separate():
    # Venus (dispositor of Taurus) sits in Leo; Sun is 5th from Leo (trinal).
    chart = placements({"Rahu": ("Taurus", 2), "Venus": ("Leo", 5), "Sun": ("Sagittarius", 9)})
    chart["Sun"] = {"rashi": "Sagittarius", "house": 9}
    chart["Mars"] = {"rashi": "Virgo", "house": 6}   # 2nd from Leo
    layers = node_layers(chart)
    rahu = layers["Rahu"]
    assert rahu["nodeRashi"] == "Taurus"
    assert rahu["dispositor"] == "Venus"
    assert rahu["dispositorRashi"] == "Leo"
    assert rahu["direct"] and rahu["operational"]
    assert rahu["direct"][0]["layer"] == "DIRECT_POSITION"
    assert rahu["operational"][0]["layer"] == "DISPOSITOR_OPERATIONAL"
    # Operational reference is Venus's rashi (Leo): Venus is 1st (same sign),
    # Mars 2nd (future) and Sun 5th (trinal) from that reference.
    assert {row["targetPlanet"]: row["relativePosition"] for row in rahu["operational"]} == {
        "Venus": 1, "Mars": 2, "Sun": 5}


def test_no_invented_node_aspect_rule():
    assert "Rahu" not in DRISHTI and "Ketu" not in DRISHTI


# --- dispositor / Mala-Shree (§54) ---------------------------------------
def test_dispositor_of_uses_sign_lordship():
    assert dispositor_of("Virgo") == "Mercury"
    assert dispositor_of("Aquarius") == "Saturn"
    assert dispositor_of("Capricorn") == "Saturn"
    assert dispositor_of("Sagittarius") == "Jupiter"


def test_mala_shree_fixture_jupiter_mercury_saturn():
    chart = placements({"Jupiter": ("Virgo", 6), "Mercury": ("Aquarius", 11), "Saturn": ("Virgo", 6)})
    chain = dispositor_chain("Jupiter", chart)
    assert chain["chain"][:3] == ["Jupiter", "Mercury", "Saturn"]
    assert set(chain["uniquePlanets"]) == {"Jupiter", "Mercury", "Saturn"}
    assert chain["count"] == 3
    assert chain["cycleStart"] == "Mercury"
    assert set(chain["cycle"]) == {"Mercury", "Saturn"}
    assert chain["isCycle"] is True


def test_mala_shree_fixture_sun_saturn_mercury_jupiter():
    chart = placements({
        "Sun": ("Capricorn", 10), "Saturn": ("Virgo", 6),
        "Mercury": ("Sagittarius", 9), "Jupiter": ("Aquarius", 11),
    })
    chain = dispositor_chain("Sun", chart)
    assert chain["chain"][:4] == ["Sun", "Saturn", "Mercury", "Jupiter"]
    assert set(chain["uniquePlanets"]) == {"Sun", "Saturn", "Mercury", "Jupiter"}
    assert chain["count"] == 4
    assert set(chain["cycle"]) == {"Saturn", "Mercury", "Jupiter"}
    assert chain["cycleArrow"].endswith("Saturn")


def test_self_dispositor_and_two_planet_cycle():
    self_chart = placements({"Sun": ("Leo", 5), "Moon": ("Cancer", 4)})
    chain = dispositor_chain("Sun", self_chart)
    assert chain["cycleStart"] == "Sun" and chain["isCycle"] is False

    pair = placements({"Sun": ("Aries", 1), "Mars": ("Leo", 5)})
    pair_chain = dispositor_chain("Sun", pair)
    assert pair_chain["chain"][:2] == ["Sun", "Mars"]
    assert set(pair_chain["cycle"]) == {"Sun", "Mars"}


def test_three_planet_cycle_and_no_infinite_loop():
    chart = placements({"Sun": ("Aries", 1), "Mars": ("Leo", 5), "Moon": ("Scorpio", 8)})
    # Sun->Mars->Sun is a 2-cycle; add a longer path to be safe
    chain = dispositor_chain("Sun", chart)
    assert len(chain["chain"]) <= len(chart)
    assert chain["cycle"]


def test_mala_shree_sorted_by_network_size():
    chart = placements({
        "Sun": ("Capricorn", 10), "Saturn": ("Virgo", 6),
        "Mercury": ("Sagittarius", 9), "Jupiter": ("Aquarius", 11),
        "Moon": ("Cancer", 4),
    })
    results = mala_shree(chart)
    assert results[0]["count"] >= results[-1]["count"]
    assert all(item["startingPlanet"] for item in results)


# --- combustion (§28) ----------------------------------------------------
def test_combustion_limits_and_retro_variants():
    assert COMBUSTION_LIMITS["Moon"][0] == 12.0
    assert COMBUSTION_LIMITS["Mars"][0] == 17.0
    assert COMBUSTION_LIMITS["Mercury"] == (14.0, 12.0)
    assert COMBUSTION_LIMITS["Jupiter"][0] == 11.0
    assert COMBUSTION_LIMITS["Venus"] == (10.0, 8.0)
    assert COMBUSTION_LIMITS["Saturn"][0] == 15.0
    assert is_combust("Mercury", 100.0, 112.0) is True          # 12 deg <= 14
    assert is_combust("Mercury", 100.0, 113.0) is True          # 13 deg <= 14
    assert is_combust("Mercury", 100.0, 113.0, retrograde=True) is False   # 13 > 12
    assert is_combust("Venus", 100.0, 108.0, retrograde=True) is True      # 8 <= 8


def test_combustion_angle_wrap_and_nodes_excluded():
    assert angular_separation(359.0, 2.0) == pytest.approx(3.0, abs=1e-9)
    assert is_combust("Moon", 359.0, 2.0) is True
    assert is_combust("Rahu", 100.0, 100.0) is False
    assert is_combust("Ketu", 100.0, 100.0) is False


# --- strength: evidence collector is present, classification is OFF ------
def test_bnn_strength_is_explicitly_blocked_not_invented():
    from kundli.analysis.bnn import chart_connections
    chart = placements({"Sun": ("Aries", 1), "Moon": ("Cancer", 4)})
    payload = chart_connections(chart)
    assert payload["mechanismOnly"] is True
    assert "friendship registry" in payload["blocked"]
    assert "strength" in payload["blocked"]


# --- other analysis (§56) ------------------------------------------------
def test_atmakaraka_uses_seven_planets_and_excludes_nodes():
    longitudes = {"Sun": 10.0, "Moon": 25.0, "Mars": 5.0, "Mercury": 12.0,
                  "Jupiter": 29.0, "Venus": 17.0, "Saturn": 21.0,
                  "Rahu": 29.9, "Ketu": 29.9}
    result = atmakaraka(longitudes)
    assert result["atmakaraka"] == "Jupiter"
    assert "Rahu" not in result["degrees"] and "Ketu" not in result["degrees"]
    assert result["excluded"] == ["Rahu", "Ketu"]


def test_atmakaraka_boundary_and_retrograde_irrelevance():
    assert atmakaraka({"Sun": 29.9, "Moon": 29.8})["atmakaraka"] == "Sun"
    # degree within sign is what ranks; 359.9 == 29.9 in Pisces
    assert atmakaraka({"Sun": 359.9, "Moon": 10.0})["atmakaraka"] == "Sun"


def test_yogakaraka_owner_mapping_only():
    assert yogakaraka("Taurus") == "Saturn"
    assert yogakaraka("Cancer") == "Mars"
    assert yogakaraka("Leo") == "Mars"
    assert yogakaraka("Libra") == "Saturn"
    assert yogakaraka("Capricorn") == "Venus"
    assert yogakaraka("Aquarius") == "Venus"
    assert yogakaraka("Aries") is None and yogakaraka("Virgo") is None


def test_maraka_uses_h2_and_h7_lords():
    result = maraka("Aries")
    assert result["houses"] == [2, 7]
    assert result["lords"][2] == "Venus"   # Taurus
    assert result["lords"][7] == "Venus"   # Libra
    assert "not a lifespan" in result["note"]
    sag = maraka("Sagittarius")
    assert sag["lords"][2] == "Saturn" and sag["lords"][7] == "Mercury"


def test_badhaka_movable_fixed_dual():
    assert badhaka("Aries") == {"modality": "movable", "house": 11, "sign": "Aquarius", "lord": "Saturn"}
    assert badhaka("Cancer")["house"] == 11
    assert badhaka("Leo") == {"modality": "fixed", "house": 9, "sign": "Aries", "lord": "Mars"}
    assert badhaka("Taurus")["house"] == 9
    assert badhaka("Virgo") == {"modality": "dual", "house": 7, "sign": "Pisces", "lord": "Jupiter"}
    assert badhaka("Gemini")["house"] == 7


def test_modality_elements_and_purushartha():
    chart = placements({"Sun": ("Aries", 1), "Moon": ("Cancer", 4), "Mars": ("Gemini", 3)})
    modality = modality_distribution(chart)
    assert set(modality["Movable"]) == {"Sun", "Moon"}
    assert modality["Dual"] == ["Mars"]
    elements = element_distribution(chart)
    assert elements["Fire"] == ["Sun"] and elements["Water"] == ["Moon"] and elements["Air"] == ["Mars"]
    pur = purushartha_distribution(chart)
    assert pur["Dharma"] == ["Sun"] and pur["Moksha"] == ["Moon"] and pur["Kama"] == ["Mars"]


def test_standard_aspects_offsets_and_targets():
    aspects = {row["planet"]: row for row in standard_aspects({
        "Mars": 3, "Saturn": 4, "Jupiter": 2, "Sun": 5, "Moon": 6, "Mercury": 7, "Venus": 8,
    })}
    assert aspects["Mars"]["offsets"] == [4, 7, 8]
    assert aspects["Mars"]["aspects"] == [6, 9, 10]
    assert aspects["Saturn"]["offsets"] == [3, 7, 10]
    assert aspects["Saturn"]["aspects"] == [6, 10, 1]
    assert aspects["Jupiter"]["offsets"] == [5, 7, 9]
    assert aspects["Jupiter"]["aspects"] == [6, 8, 10]
    for planet in ("Sun", "Moon", "Mercury", "Venus"):
        assert aspects[planet]["offsets"] == [7]


def test_dignity_distribution_and_conjunctions():
    chart = placements({"Sun": ("Aries", 1), "Moon": ("Taurus", 2), "Mars": ("Aries", 1)})
    buckets = dignity_distribution(chart)
    assert "Sun" in buckets["exalted"] and "Moon" in buckets["exalted"]
    conjunctions = same_sign_conjunctions(chart)
    assert any(set(row["planets"]) == {"Sun", "Mars"} and row["type"] == "same_sign" for row in conjunctions)


def test_moon_chart_transforms_houses_not_positions():
    chart = placements({"Moon": ("Cancer", 4), "Sun": ("Aries", 1), "Mars": ("Cancer", 4)})
    transformed = moon_chart(chart)
    assert transformed["lagnaSign"] == "Cancer"
    assert transformed["placements"]["Moon"]["house"] == 1
    assert transformed["placements"]["Mars"]["house"] == 1
    assert transformed["placements"]["Sun"]["house"] == 10
    assert transformed["placements"]["Sun"]["rashi"] == "Aries"      # unchanged
    assert chart["Sun"]["house"] == 1                                 # original untouched
