"""BNN strength EVIDENCE engine.

Collects explainable evidence only. The final five-level grading rule
(VERY_STRONG..VERY_WEAK) has NOT been supplied, so the classifier is an
isolated interface that returns:

    classification: None
    classificationStatus: "AWAITING_OWNER_GRADING_RULE"

No arbitrary weights, thresholds or percentages are invented.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from jyotish.planets import dignity as dignity_of

from .bnn import (
    GAIN,
    LAYER_DISPOSITOR,
    LAYER_RETRO,
    OPPOSITION,
    PAST,
    STRUGGLE,
    TRINE,
    FUTURE,
    connections_from,
    node_layers,
    relative_position,
    retrograde_layers,
)
from .combustion import is_combust
from .relationships import ENEMY, FRIEND, NEUTRAL, relationship

AWAITING_GRADING_RULE = "AWAITING_OWNER_GRADING_RULE"

# Kartari / surrounding condition outcomes.
SUPPORTIVE_BOTH_SIDES = "SUPPORTIVE_BOTH_SIDES"
PRESSURED_BOTH_SIDES = "PRESSURED_BOTH_SIDES"
MIXED = "MIXED"
FORWARD_ONLY = "FORWARD_ONLY"
BACKWARD_ONLY = "BACKWARD_ONLY"
EMPTY = "EMPTY"

NODES = ("Rahu", "Ketu")


def annotate(rows: List[Dict[str, Any]], reference: str) -> List[Dict[str, Any]]:
    """Attach directional relationship quality WITHOUT changing the connection."""
    for row in rows:
        row["relationshipQuality"] = relationship(reference, row["targetPlanet"])
    return rows


def _quality(row: Dict[str, Any]) -> str:
    return str(row.get("relationshipQuality") or NEUTRAL)


def _side_quality(rows: List[Dict[str, Any]], position: int) -> Optional[str]:
    present = [row for row in rows if row["relativePosition"] == position]
    if not present:
        return None
    qualities = {_quality(row) for row in present}
    if qualities == {FRIEND}:
        return FRIEND
    if qualities == {ENEMY}:
        return ENEMY
    return MIXED if FRIEND in qualities and ENEMY in qualities else NEUTRAL


def kartari_condition(behind: Optional[str], ahead: Optional[str]) -> str:
    if behind is None and ahead is None:
        return EMPTY
    if behind and ahead:
        pair = {behind, ahead}
        if pair == {FRIEND}:
            return SUPPORTIVE_BOTH_SIDES
        if pair == {ENEMY}:
            return PRESSURED_BOTH_SIDES
        if len(pair) == 2:
            return MIXED
        return MIXED if behind == ahead == MIXED else NEUTRAL
    if ahead:
        return FORWARD_ONLY
    return BACKWARD_ONLY


def _isolation(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Structural isolation: network ABSENCE, never friendship based."""
    positions_present = {row["relativePosition"] for row in rows}
    structural = (2, 12, 3, 11, 7)
    trinal = (1, 5, 9)
    missing_structural = [position for position in structural if position not in positions_present]
    missing_trinal = [position for position in trinal if position not in positions_present]
    present_structural = [position for position in structural if position in positions_present]
    present_trinal = [position for position in trinal if position in positions_present]

    covered = len(present_structural) + len(present_trinal)
    if covered == 0:
        level = "ISOLATED"
    elif covered <= 2:
        level = "PARTIAL"
    else:
        level = "CONNECTED"

    return {
        "isIsolated": covered == 0,
        "isolationLevel": level,
        "presentStructuralPositions": present_structural,
        "presentTrinalPositions": present_trinal,
        "missingStructuralPositions": missing_structural,
        "missingTrinalPositions": missing_trinal,
        "note": "structural absence only; enemy connections still count as connections",
    }


def collect_evidence(planet: str, placements: Dict[str, Dict[str, Any]],
                     retrograde: Sequence[str] = (), sun_longitudes: Optional[Dict[str, float]] = None,
                     longitudes: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    placement = placements.get(planet)
    if not placement:
        return {"referencePlanet": planet, "available": False,
                "classification": None, "classificationStatus": AWAITING_GRADING_RULE}

    rashi = str(placement["rashi"])
    rows = annotate(connections_from(planet, rashi, placements), planet)

    by_group: Dict[str, List[str]] = {TRINE: [], FUTURE: [], PAST: [], STRUGGLE: [], GAIN: [], OPPOSITION: []}
    for row in rows:
        by_group.setdefault(str(row["connectionGroup"]), []).append(row["targetPlanet"])

    friendly = [row["targetPlanet"] for row in rows if _quality(row) == FRIEND]
    enemy = [row["targetPlanet"] for row in rows if _quality(row) == ENEMY]
    neutral = [row["targetPlanet"] for row in rows if _quality(row) == NEUTRAL]

    behind = _side_quality(rows, 12)
    ahead = _side_quality(rows, 2)
    kartari = kartari_condition(behind, ahead)

    dignity = dignity_of(planet, rashi)
    combustion = None
    if sun_longitudes is not None and longitudes is not None:
        sun_long = sun_longitudes.get("Sun")
        planet_long = longitudes.get(planet)
        if sun_long is not None and planet_long is not None:
            combustion = {
                "isCombust": is_combust(planet, planet_long, sun_long, planet in set(retrograde)),
                "note": "modifier only; not automatically weak",
            }

    support_reasons: List[str] = []
    if by_group[TRINE]:
        support_reasons.append(
            "trinal network present: " + ", ".join(by_group[TRINE]) + " blend their significations here")
    if friendly:
        support_reasons.append("friendly connections: " + ", ".join(friendly))
    if ahead:
        support_reasons.append(f"forward (2nd) condition: {ahead}")
    if behind:
        support_reasons.append(f"backward (12th) condition: {behind}")
    if by_group[GAIN]:
        support_reasons.append("gain (11th) connections: " + ", ".join(by_group[GAIN]))
    if dignity in ("exalted", "own_sign"):
        support_reasons.append(f"dignity: {dignity}")

    pressure_reasons: List[str] = []
    if enemy:
        pressure_reasons.append("inimical connections: " + ", ".join(enemy))
    if by_group[STRUGGLE]:
        pressure_reasons.append("struggle (3rd) connections: " + ", ".join(by_group[STRUGGLE]))
    if by_group[OPPOSITION]:
        pressure_reasons.append("opposition/completion (7th): " + ", ".join(by_group[OPPOSITION]))
    if dignity == "debilitated":
        pressure_reasons.append("dignity: debilitated")
    if combustion and combustion.get("isCombust"):
        pressure_reasons.append("combustion (modifier)")
    if _isolation(rows)["isIsolated"]:
        pressure_reasons.append("structurally isolated network")

    evidence: Dict[str, Any] = {
        "referencePlanet": planet,
        "available": True,
        "rashi": rashi,
        "house": placement.get("house"),
        "connections": rows,
        "annotatedConnections": rows,
        "trinalConnections": by_group[TRINE],
        "forwardConnections": by_group[FUTURE],
        "backwardConnections": by_group[PAST],
        "struggleConnections": by_group[STRUGGLE],
        "gainConnections": by_group[GAIN],
        "oppositionConnections": by_group[OPPOSITION],
        "friendlyConnections": friendly,
        "enemyConnections": enemy,
        "neutralConnections": neutral,
        "hasForwardSupport": bool(by_group[FUTURE]),
        "hasBackwardSupport": bool(by_group[PAST]),
        "hasOpposition": bool(by_group[OPPOSITION]),
        "hasThreeElevenNetwork": bool(by_group[STRUGGLE] or by_group[GAIN]),
        "hasTrinalNetwork": bool(by_group[TRINE]),
        "isIsolated": _isolation(rows)["isIsolated"],
        "isolation": _isolation(rows),
        "dignity": dignity,
        "combustion": combustion,
        "kartariCondition": kartari,
        "kartariEvidence": {"behind12th": behind, "ahead2nd": ahead},
        "supportReasons": support_reasons,
        "pressureReasons": pressure_reasons,
        "classification": None,
        "classificationStatus": AWAITING_GRADING_RULE,
    }

    if planet in set(retrograde) and planet not in NODES:
        evidence["retrogradeLayers"] = retrograde_layers(placements, [planet]).get(planet, {})

    if planet in NODES:
        node = node_layers(placements).get(planet)
        if node:
            evidence["nodeDispositorLayer"] = {
                "dispositor": node["dispositor"],
                "dispositorRashi": node["dispositorRashi"],
                "operational": annotate(node["operational"], planet),
                "layer": LAYER_DISPOSITOR,
            }

    return evidence


def classify(evidence: Dict[str, Any]) -> Dict[str, Any]:
    """Isolated classifier interface - grading rule not supplied yet."""
    return {
        "referencePlanet": evidence.get("referencePlanet"),
        "classification": None,
        "classificationStatus": AWAITING_GRADING_RULE,
        "note": "five-level grading requires the owner's rule; evidence above is the current output",
    }


def strength_evidence(placements: Dict[str, Dict[str, Any]],
                      retrograde: Sequence[str] = (),
                      sun_longitudes: Optional[Dict[str, float]] = None,
                      longitudes: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    per_planet = {
        planet: collect_evidence(planet, placements, retrograde, sun_longitudes, longitudes)
        for planet in placements
    }
    return {
        "planets": per_planet,
        "classificationStatus": AWAITING_GRADING_RULE,
        "weights": None,
        "note": "no numerical weights or thresholds are defined in this version",
    }
