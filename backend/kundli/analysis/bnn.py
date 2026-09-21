"""BNN connection mechanics (owner-specified).

Direction is preserved: A->B = 2 is NOT the same as B->A = 12.

Primary positions: 1/5/9 (trinal support + karakatwa blending), 2 (future),
12 (past), 3 (struggle), 11 (gain), 7 (opposition + completion).

4/6/8/10 are deliberately NOT part of the primary BNN support model - they are
only reported as `excluded` if requested.

Connection QUALITY (friend/enemy) is intentionally absent: the owner's BNN
relationship table has not been supplied and no registry exists in the repo.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from .signs import RASHIS, sign_distance

TRINE = "TRINE_SUPPORT"
FUTURE = "FUTURE"
PAST = "PAST"
STRUGGLE = "STRUGGLE"
GAIN = "GAIN"
OPPOSITION = "OPPOSITION_COMPLETION"

# ONE registry of directional semantics.
CONNECTION_GROUPS: Dict[int, str] = {
    1: TRINE, 5: TRINE, 9: TRINE,
    2: FUTURE,
    12: PAST,
    3: STRUGGLE,
    11: GAIN,
    7: OPPOSITION,
}

PRIMARY_POSITIONS: tuple = (1, 5, 9, 2, 12, 3, 11, 7)
EXCLUDED_POSITIONS: tuple = (4, 6, 8, 10)

GROUP_MEANING: Dict[str, str] = {
    TRINE: "support and karakatwa blending",
    FUTURE: "future / forward development",
    PAST: "past / previous background",
    STRUGGLE: "struggle / effort required",
    GAIN: "gain / result",
    OPPOSITION: "opposition and completion",
}

NODES = ("Rahu", "Ketu")

LAYER_DIRECT = "DIRECT_POSITION"
LAYER_ACTUAL = "ACTUAL_POSITION"
LAYER_RETRO = "RETRO_PREVIOUS_POSITION"
LAYER_DISPOSITOR = "DISPOSITOR_OPERATIONAL"


def group_for_position(position: int) -> Optional[str]:
    return CONNECTION_GROUPS.get(position)


def relative_position(reference_rashi: str, target_rashi: str) -> int:
    return sign_distance(reference_rashi, target_rashi)


def connection(reference: str, reference_rashi: str, target: str, target_rashi: str,
               layer: str) -> Dict[str, Any]:
    from .relationships import relationship

    position = relative_position(reference_rashi, target_rashi)
    group = group_for_position(position)
    return {
        "referencePlanet": reference,
        "referenceRashi": reference_rashi,
        "targetPlanet": target,
        "targetRashi": target_rashi,
        "relativePosition": position,
        "connectionGroup": group,
        "isPrimary": group is not None,
        "direction": f"{reference}->{target}",
        "layer": layer,
        "relationshipQuality": relationship(reference, target),
    }


def padas(position: int) -> int:
    return position


def connections_from(reference: str, reference_rashi: str,
                     placements: Dict[str, Dict[str, Any]],
                     layer: str = LAYER_ACTUAL,
                     include_excluded: bool = False) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for target, data in placements.items():
        if target == reference:
            continue
        target_rashi = str(data.get("rashi"))
        row = connection(reference, reference_rashi, target, target_rashi, layer)
        if row["isPrimary"] or include_excluded:
            rows.append(row)
    order = {position: index for index, position in enumerate(PRIMARY_POSITIONS)}
    return sorted(rows, key=lambda item: (order.get(item["relativePosition"], 99),
                                          item["targetPlanet"]))


def previous_rashi(rashi: str) -> str:
    return RASHIS[(RASHIS.index(rashi) - 1) % 12]


def retrograde_layers(placements: Dict[str, Dict[str, Any]],
                      retrograde: Sequence[str]) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
    """For retrograde planets BOTH the actual and previous rashi are active.

    Nodes never receive this generic rule.
    """
    result: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
    for planet in retrograde:
        if planet in NODES or planet not in placements:
            continue
        actual_rashi = str(placements[planet]["rashi"])
        result[planet] = {
            LAYER_ACTUAL: connections_from(planet, actual_rashi, placements, LAYER_ACTUAL),
            LAYER_RETRO: connections_from(planet, previous_rashi(actual_rashi), placements, LAYER_RETRO),
        }
    return result


def node_layers(placements: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Direct node layer + dispositor/operational layer (kept separate)."""
    from .dispositor import dispositor_of

    result: Dict[str, Dict[str, Any]] = {}
    for node in NODES:
        if node not in placements:
            continue
        direct_rashi = str(placements[node]["rashi"])
        dispositor = dispositor_of(direct_rashi)
        dispositor_placement = placements.get(dispositor or "", {})
        operational_rashi = str(dispositor_placement.get("rashi") or direct_rashi)
        result[node] = {
            "nodeRashi": direct_rashi,
            "dispositor": dispositor,
            "dispositorRashi": dispositor_placement.get("rashi"),
            "direct": connections_from(node, direct_rashi, placements, LAYER_DIRECT),
            "operational": connections_from(node, operational_rashi, placements, LAYER_DISPOSITOR),
            "operationalReferenceRashi": operational_rashi,
        }
    return result


def chart_connections(placements: Dict[str, Dict[str, Any]],
                      retrograde: Optional[Sequence[str]] = None) -> Dict[str, Any]:
    """PRIVATE: all directional BNN connections for the chart."""
    retro = list(retrograde or [])
    base = {
        planet: connections_from(planet, str(data["rashi"]), placements)
        for planet, data in placements.items()
    }
    return {
        "connections": base,
        "retrogradeLayers": retrograde_layers(placements, retro),
        "nodeLayers": node_layers(placements),
        "primaryPositions": list(PRIMARY_POSITIONS),
        "excludedPositions": list(EXCLUDED_POSITIONS),
        "mechanismOnly": True,
        "blocked": "connection quality (friend/enemy) and BNN strength "
                   "classification require the owner's friendship registry, "
                   "which is not present in the repository",
    }
