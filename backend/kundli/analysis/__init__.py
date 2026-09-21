"""KAVACH Kundli technical-analysis layer.

IMPLEMENTED (fully specified by the owner):
  signs, BNN directional mechanics, retrograde dual layers, node direct +
  dispositor layers, dispositor engine, Mala-Shree, standard aspects, dignity,
  combustion, Atmakaraka, Yogakaraka, Maraka, Badhaka/Badhakesh, modality,
  elements, purushartha, conjunctions, Moon chart.

BLOCKED (rule not supplied / not present in the repository):
  BNN connection QUALITY (friend / enemy) and the resulting 5-level BNN
  strength classification. No friendship registry exists in the repo and the
  owner's table was not supplied, so nothing is invented here.
"""

from .aspects import DRISHTI, standard_aspects, target_houses
from .bnn import (
    CONNECTION_GROUPS,
    EXCLUDED_POSITIONS,
    GROUP_MEANING,
    PRIMARY_POSITIONS,
    chart_connections,
    connection,
    connections_from,
    node_layers,
    previous_rashi,
    relative_position,
    retrograde_layers,
)
from .classifications import (
    dignity_distribution,
    element_distribution,
    modality_distribution,
    moon_chart,
    purushartha_distribution,
    same_sign_conjunctions,
)
from .combustion import COMBUSTION_LIMITS, angular_separation, is_combust, limit_for
from .dispositor import chains_for_all, dispositor_chain, dispositor_of, mala_shree, network_size
from .karakas import AK_PLANETS, YOGAKARAKA_BY_LAGNA, atmakaraka, badhaka, lagna_summary, maraka, yogakaraka
from .signs import (
    DUAL,
    ELEMENTS,
    FIXED,
    MODALITIES,
    MOVABLE,
    PURUSHARTHA,
    RASHIS,
    SIGN_LORD,
    house_lord,
    house_sign,
    sign_distance,
)

from .analysis import build_analysis
from .relationships import BNN_RELATIONSHIPS, ENEMY, FRIEND, NEUTRAL, enemies_of, friends_of, relationship
from .strength import (
    AWAITING_GRADING_RULE,
    EMPTY,
    FORWARD_ONLY,
    BACKWARD_ONLY,
    MIXED,
    PRESSURED_BOTH_SIDES,
    SUPPORTIVE_BOTH_SIDES,
    classify,
    collect_evidence,
    kartari_condition,
    strength_evidence,
)

__all__ = [
    "AWAITING_GRADING_RULE", "BACKWARD_ONLY", "BNN_RELATIONSHIPS", "EMPTY", "ENEMY",
    "FORWARD_ONLY", "FRIEND", "MIXED", "NEUTRAL", "PRESSURED_BOTH_SIDES",
    "SUPPORTIVE_BOTH_SIDES", "build_analysis", "classify", "collect_evidence",
    "enemies_of", "friends_of", "kartari_condition", "relationship", "strength_evidence",
    "AK_PLANETS", "CONNECTION_GROUPS", "COMBUSTION_LIMITS", "DRISHTI", "DUAL",
    "ELEMENTS", "EXCLUDED_POSITIONS", "FIXED", "GROUP_MEANING", "MODALITIES",
    "MOVABLE", "PRIMARY_POSITIONS", "PURUSHARTHA", "RASHIS", "SIGN_LORD",
    "YOGAKARAKA_BY_LAGNA", "angular_separation", "atmakaraka", "badhaka",
    "chains_for_all", "chart_connections", "connection", "connections_from",
    "dignity_distribution", "dispositor_chain", "dispositor_of",
    "element_distribution", "house_lord", "house_sign", "is_combust",
    "lagna_summary", "limit_for", "mala_shree", "maraka", "modality_distribution",
    "moon_chart", "network_size", "node_layers", "previous_rashi",
    "purushartha_distribution", "relative_position", "retrograde_layers",
    "same_sign_conjunctions", "sign_distance", "standard_aspects",
    "target_houses", "yogakaraka",
]
