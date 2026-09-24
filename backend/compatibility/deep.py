"""Deep compatibility analyses, aggregation and the interpreted public report.

Sources: the two owner-supplied decks only. Everything here is either
VERDICT-ELIGIBLE (the source states enough to classify supportive / mixed /
challenging) or CONTEXTUAL-ONLY (the source asks the astrologer to inspect
something but defines no rule), and the two sets are documented explicitly.

Deterministic only: no LLM, no invented weights, no numeric scoring model. Internal
evidence never crosses the public serialization boundary.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

from kundli.analysis.signs import SIGN_LORD

SUPPORTIVE = "Supportive"
MIXED = "Mixed"
CHALLENGING = "Challenging"
CONTEXTUAL = "Contextual"

# Source: Class 2, slide 11-13.
KUJA_HOUSES = (1, 2, 4, 7, 8, 12)
DEEP_MALEFICS = ("Mars", "Rahu", "Ketu")          # named explicitly by the deck
FRIENDLY_PERIOD_LORDS = ("Venus", "Jupiter", "Moon")
DIFFICULT_RULER_HOUSES = (3, 6, 8, 12)
CHALLENGING_RULERS = ("Saturn", "Mars")

# Mercury / Mars sign-distance classes (Class 2, slide 13).
COMM_SUPPORTIVE = ((1,), (7,), (3, 11), (5, 9))
COMM_CHALLENGING = ((6, 8), (2, 12))
ENERGY_SUPPORTIVE = ((1,), (3, 11), (5, 9))


@dataclass(frozen=True)
class ChartFacts:
    """The authoritative chart facts the deep rules need. Read-only."""

    lagna: str
    planets: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # name -> {sign, house}
    houses: Dict[int, str] = field(default_factory=dict)              # number -> sign
    dasha_lords: Tuple[str, ...] = ()                                 # current maha + antar

    def house_of(self, planet: str) -> Optional[int]:
        row = self.planets.get(planet) or {}
        house = row.get("house")
        return int(house) if isinstance(house, int) else None

    def sign_of(self, planet: str) -> Optional[str]:
        row = self.planets.get(planet) or {}
        sign = row.get("sign")
        return sign if isinstance(sign, str) else None


@dataclass(frozen=True)
class DeepFactor:
    key: str
    category: str            # public category label
    status: str              # SUPPORTIVE | MIXED | CHALLENGING | CONTEXTUAL
    eligible: bool
    prose: str
    evidence: Dict[str, Any] = field(default_factory=dict)

    def to_public(self) -> Dict[str, str]:
        return {"category": self.category, "status": self.status, "interpretation": self.prose}


def sign_distance(from_sign: str, to_sign: str, signs: Sequence[str]) -> int:
    """Inclusive cyclic distance from one sign to another (1..12)."""
    return ((list(signs).index(to_sign) - list(signs).index(from_sign)) % 12) + 1


def _pair(d: int) -> Tuple[int, ...]:
    """The distance class: 1 = conjunction, 7 = opposition, else the X/Y pair.

    For a forward distance d the reverse distance is 14 - d, so adjacent signs
    give the 2/12 class and the sixth sign gives 6/8 - exactly as the source
    lists them.
    """
    if d in (1, 7):
        return (d,)
    return (d, 14 - d)


# ---------------------------------------------------------------------------
# A. RELATIONSHIP FOUNDATION (7th house / partnership area)
# ---------------------------------------------------------------------------
def relationship_foundation(bride: ChartFacts, groom: ChartFacts) -> DeepFactor:
    category = "Relationship foundation"
    evidence: Dict[str, Any] = {}
    flags: List[str] = []
    for label, chart in (("bride", bride), ("groom", groom)):
        seventh = chart.houses.get(7)
        ruler = SIGN_LORD.get(seventh or "")
        house = chart.house_of(ruler) if ruler else None
        evidence[f"{label}Ruler"] = ruler
        evidence[f"{label}RulerHouse"] = house
        if ruler in CHALLENGING_RULERS:
            flags.append(f"{label}:challenging_ruler")
        if house in DIFFICULT_RULER_HOUSES:
            flags.append(f"{label}:ruler_in_difficult_house")
    evidence["flags"] = flags

    if not flags:
        return DeepFactor("foundation", category, SUPPORTIVE, True,
                          "The partnership area looks settled in both charts, which is a "
                          "supportive sign for the stability of the relationship.", evidence)
    if len(flags) == 1:
        return DeepFactor("foundation", category, MIXED, True,
                          "The partnership area looks settled in one chart but carries a "
                          "demanding placement in the other, so stability may depend on "
                          "patience and consistency.", evidence)
    return DeepFactor("foundation", category, CHALLENGING, True,
                      "Both charts place pressure on the partnership area, so this "
                      "relationship may need deliberate effort to build a steady base.", evidence)


def foundation_context(bride: ChartFacts, groom: ChartFacts) -> DeepFactor:
    """Contextual-only: the source asks about influences on the partnership area
    but defines no rule for classifying them."""
    return DeepFactor(
        "foundation_context", "Relationship foundation", CONTEXTUAL, False,
        "The wider influences around the partnership area are worth reading together "
        "with the rest of the report rather than on their own.",
        {"brideSeventh": bride.houses.get(7), "groomSeventh": groom.houses.get(7)},
    )


# ---------------------------------------------------------------------------
# B. DEEP PARTNERSHIP DYNAMICS (8th area) - safe portion only
# ---------------------------------------------------------------------------
def deep_partnership(bride: ChartFacts, groom: ChartFacts) -> DeepFactor:
    category = "Deep partnership dynamics"
    evidence: Dict[str, Any] = {}
    pressure: List[str] = []
    for label, chart in (("bride", bride), ("groom", groom)):
        eighth = chart.houses.get(8)
        occupants = [name for name, row in chart.planets.items()
                     if row.get("house") == 8 and name in DEEP_MALEFICS]
        evidence[f"{label}Eighth"] = eighth
        evidence[f"{label}EighthOccupants"] = sorted(occupants)
        if occupants:
            pressure.append(label)
    evidence["pressure"] = pressure

    if not pressure:
        return DeepFactor("deep_partnership", category, SUPPORTIVE, True,
                          "The deeper, more private side of partnership looks comparatively "
                          "clear, which supports adjustment when life gets demanding.", evidence)
    if len(pressure) == 1:
        return DeepFactor("deep_partnership", category, MIXED, True,
                          "One chart carries intensity in the deeper partnership area, so "
                          "shared pressure may need conscious handling.", evidence)
    return DeepFactor("deep_partnership", category, CHALLENGING, True,
                      "Both charts carry intensity in the deeper partnership area, so this "
                      "pairing may need extra care with emotional pressure and adjustment.", evidence)


# ---------------------------------------------------------------------------
# C. CORE PERSONALITY FIT (Ascendant + rulers)
# ---------------------------------------------------------------------------
def personality_fit(bride: ChartFacts, groom: ChartFacts,
                    friendship) -> DeepFactor:
    category = "Core personality fit"
    bride_ruler = SIGN_LORD.get(bride.lagna)
    groom_ruler = SIGN_LORD.get(groom.lagna)
    a = friendship(bride_ruler, groom_ruler) if bride_ruler and groom_ruler else "neutral"
    b = friendship(groom_ruler, bride_ruler) if bride_ruler and groom_ruler else "neutral"
    evidence = {"brideRuler": bride_ruler, "groomRuler": groom_ruler,
                "brideLagna": bride.lagna, "groomLagna": groom.lagna,
                "brideViewOfGroom": a, "groomViewOfBride": b}

    if a == "friend" and b == "friend":
        return DeepFactor("personality_fit", category, SUPPORTIVE, True,
                          "Their core natures are naturally on good terms, so the underlying "
                          "personalities tend to bring out the better side of each other.", evidence)
    if a == "enemy" and b == "enemy":
        return DeepFactor("personality_fit", category, CHALLENGING, True,
                          "Their core natures pull in different directions, so they may need "
                          "to work at understanding each other's instincts.", evidence)
    return DeepFactor("personality_fit", category, MIXED, True,
                      "Their core natures are workable but not identical, which usually means "
                      "some conscious adjustment to each other's style.", evidence)


# ---------------------------------------------------------------------------
# D. RELATIONSHIP TIMING (current periods)
# ---------------------------------------------------------------------------
def relationship_timing(bride: ChartFacts, groom: ChartFacts) -> DeepFactor:
    category = "Relationship timing"
    lords = [lord for lord in (bride.dasha_lords[:1] + groom.dasha_lords[:1]) if lord]
    friendly = [lord for lord in lords if lord in FRIENDLY_PERIOD_LORDS]
    evidence = {"currentLords": list(lords), "friendlyCount": len(friendly)}

    if lords and len(friendly) == len(lords):
        return DeepFactor("timing", category, SUPPORTIVE, True,
                          "The current phase reads as comparatively supportive for "
                          "cooperation and relationship development.", evidence)
    if friendly:
        return DeepFactor("timing", category, SUPPORTIVE, True,
                          "The current phase is partly supportive, so cooperation and "
                          "relationship development have reasonable backing.", evidence)
    return DeepFactor("timing", category, MIXED, True,
                      "The current phase may call for more patience and deliberate "
                      "communication rather than relying on momentum.", evidence)


# ---------------------------------------------------------------------------
# E. COMMUNICATION (Mercury to Mercury by sign)
# ---------------------------------------------------------------------------
def _classify_pair(d: int, supportive: Tuple[Tuple[int, ...], ...]) -> str:
    pair = frozenset(_pair(d))
    for allowed in supportive:
        if pair == frozenset(allowed):
            return SUPPORTIVE
    for allowed in COMM_CHALLENGING:
        if pair == frozenset(allowed):
            return CHALLENGING
    return MIXED


def communication(bride: ChartFacts, groom: ChartFacts, signs: Sequence[str]) -> DeepFactor:
    category = "Communication"
    a, b = bride.sign_of("Mercury"), groom.sign_of("Mercury")
    if not a or not b:
        return DeepFactor("communication", category, MIXED, False,
                          "Communication styles are not clearly indicated here.", {"mercury": None})
    d = sign_distance(a, b, signs)
    status = _classify_pair(d, COMM_SUPPORTIVE)
    evidence = {"brideSign": a, "groomSign": b, "distance": d, "pair": sorted(_pair(d))}

    prose = {
        SUPPORTIVE: "You tend to understand each other's meaning fairly naturally, which "
                    "helps when you need to resolve differences.",
        CHALLENGING: "You may approach conversations differently, especially when emotions "
                     "are high. This does not automatically indicate incompatibility, but "
                     "clarity and patience may be particularly important when resolving "
                     "disagreements.",
        MIXED: "Your communication styles are neither strongly aligned nor strongly at odds, "
               "so how well you understand each other will depend largely on how deliberately "
               "you listen.",
    }[status]
    return DeepFactor("communication", category, status, True, prose, evidence)


# ---------------------------------------------------------------------------
# F. CONFLICT & ENERGY STYLE (Mars to Mars by sign)
# ---------------------------------------------------------------------------
def energy_style(bride: ChartFacts, groom: ChartFacts, signs: Sequence[str]) -> DeepFactor:
    category = "Conflict & energy style"
    a, b = bride.sign_of("Mars"), groom.sign_of("Mars")
    if not a or not b:
        return DeepFactor("energy_style", category, MIXED, False,
                          "Conflict styles are not clearly indicated here.", {"mars": None})
    d = sign_distance(a, b, signs)
    pair = frozenset(_pair(d))
    supportive = any(pair == frozenset(allowed) for allowed in ENERGY_SUPPORTIVE)
    status = SUPPORTIVE if supportive else MIXED
    evidence = {"brideSign": a, "groomSign": b, "distance": d, "pair": sorted(_pair(d))}

    prose = (
        "Your natural action styles sit comfortably together, so conflict is likely to be "
        "handled with less friction."
        if supportive else
        "The source does not flag a strong signal here, so conflict style is best treated as "
        "workable but dependent on conscious coordination."
    )
    return DeepFactor("energy_style", category, status, True, prose, evidence)


# ---------------------------------------------------------------------------
# G. CONFLICT BALANCE (Kuja pairing)
# ---------------------------------------------------------------------------
def conflict_balance(bride: ChartFacts, groom: ChartFacts) -> DeepFactor:
    category = "Conflict balance"
    bride_house = bride.house_of("Mars")
    groom_house = groom.house_of("Mars")
    bride_has = bride_house in KUJA_HOUSES
    groom_has = groom_house in KUJA_HOUSES
    evidence = {"brideHouse": bride_house, "groomHouse": groom_house,
                "brideCondition": bride_has, "groomCondition": groom_has}

    if bride_has and groom_has:
        return DeepFactor("conflict_balance", category, SUPPORTIVE, True,
                          "Both carry the same intensity in their charts, which the tradition "
                          "reads as balancing rather than lopsided.", evidence)
    if not bride_has and not groom_has:
        return DeepFactor("conflict_balance", category, SUPPORTIVE, True,
                          "Neither chart carries that particular intensity, which is a "
                          "supportive sign for smooth conflict handling.", evidence)
    return DeepFactor("conflict_balance", category, MIXED, True,
                      "Only one of the two carries that intensity, so conflict may need more "
                      "conscious coordination between them.", evidence)


# ---------------------------------------------------------------------------
# Registry: which evidence is verdict-eligible, and why
# ---------------------------------------------------------------------------
# VERDICT-ELIGIBLE: the source states a direction we can classify.
#   kutas: tara (remainder rule), gana (directional preference), nadi (same/different),
#          rashi (directional positions + mitigation), graha_maitri (friends/enemies),
#          vasya (amenability), yoni (matrix value bands).
#   deep:  foundation (ruler placement / challenging ruler), deep_partnership
#          (named occupants of the deeper area), personality_fit (ruler friendship),
#          timing (friendly period lords), communication (named sign classes),
#          energy_style (named supportive classes; everything else is MIXED, never
#          invented as negative), conflict_balance (both/neither/one pairing).
ELIGIBLE_FACTORS = (
    "tara", "gana", "nadi", "rashi", "graha_maitri", "vasya", "yoni",
    "foundation", "deep_partnership", "personality_fit", "timing",
    "communication", "energy_style", "conflict_balance",
)

# CONTEXTUAL-ONLY: the source says "inspect this" but gives no classification rule,
# so it never votes.
#   foundation_context: influences/aspects on the partnership area.
CONTEXTUAL_FACTORS = ("foundation_context",)

STATUS_TO_BUCKET = {SUPPORTIVE: "supportive", MIXED: "mixed", CHALLENGING: "challenging"}

# Overall assessment thresholds (deterministic, server-side).
STRONG_MIN_RATIO = 0.75
SUPPORTIVE_NET = 2
CHALLENGING_NET = -2
MIN_ELIGIBLE = 6


def overall_state(statuses: Sequence[str]) -> Dict[str, Any]:
    """Deterministic overall classification from eligible statuses only."""
    buckets = {"supportive": 0, "mixed": 0, "challenging": 0}
    for status in statuses:
        bucket = STATUS_TO_BUCKET.get(status)
        if bucket:
            buckets[bucket] += 1
    total = sum(buckets.values())
    net = buckets["supportive"] - buckets["challenging"]

    if total < MIN_ELIGIBLE:
        state = "MIXED COMPATIBILITY"
    elif buckets["challenging"] == 0 and buckets["supportive"] >= STRONG_MIN_RATIO * total:
        state = "STRONG POTENTIAL"
    elif net >= SUPPORTIVE_NET:
        state = "GENERALLY SUPPORTIVE"
    elif net <= CHALLENGING_NET:
        state = "SIGNIFICANT CHALLENGES"
    else:
        state = "MIXED COMPATIBILITY"

    return {"state": state, "counts": buckets, "net": net, "total": total}


STATE_SUMMARY = {
    "STRONG POTENTIAL": "The traditional matching factors show a high level of compatibility "
                        "in this comparison.",
    "GENERALLY SUPPORTIVE": "The traditional matching factors are supportive overall, with "
                            "some areas carrying more weight than others.",
    "MIXED COMPATIBILITY": "The matching factors are mixed, with both supportive areas and "
                           "points that deserve closer consideration.",
    "SIGNIFICANT CHALLENGES": "The traditional matching factors show several areas of difference "
                              "that deserve closer consideration.",
}

# Owner-approved score bands. The PRIMARY overall status is driven by the Kuta
# Match Score ratio, not by the deep-analysis vote counts.
SCORE_BANDS = ((0.75, "STRONG POTENTIAL"), (0.55, "GENERALLY SUPPORTIVE"),
               (0.35, "MIXED COMPATIBILITY"))


def score_state(awarded: int, maximum: int) -> str:
    """Deterministic overall state from the actual Kuta score ratio."""
    if maximum <= 0:
        return "MIXED COMPATIBILITY"
    ratio = awarded / maximum
    for threshold, state in SCORE_BANDS:
        if ratio >= threshold:
            return state
    return "SIGNIFICANT CHALLENGES"
