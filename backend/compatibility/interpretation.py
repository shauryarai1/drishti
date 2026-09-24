"""The interpreted, customer-facing compatibility report.

Builds the public model from internal evidence. Nothing here serializes a rule
name, a planet, a house, a sign distance, an animal, a gender, a matrix value,
a point or a reason code - only categories, states and prose.
"""

from __future__ import annotations

from typing import Any, Dict, List, Sequence

from .deep import (
    CHALLENGING, CONTEXTUAL, MIXED, SUPPORTIVE, STATE_SUMMARY, overall_state, score_state,
)

# Public themes. Several internal rules are synthesised into one theme so the
# customer never sees one card per astrology rule.
PUBLIC_THEMES = (
    ("Emotional connection", ("nadi", "graha_maitri")),
    ("Temperament", ("gana", "vasya")),
    ("Day-to-day ease", ("tara", "rashi")),
    ("Attraction & chemistry", ("yoni",)),
    ("Communication", ("communication",)),
    ("Core personality fit", ("personality_fit",)),
    ("Relationship foundation", ("foundation",)),
    ("Deep partnership dynamics", ("deep_partnership",)),
    ("Conflict & energy style", ("energy_style",)),
    ("Conflict balance", ("conflict_balance",)),
    ("Relationship timing", ("timing",)),
)

_STRENGTHS = {
    "Emotional connection": "Natural emotional understanding",
    "Temperament": "Compatible temperaments",
    "Day-to-day ease": "Compatible everyday rhythm",
    "Attraction & chemistry": "Strong natural attraction",
    "Communication": "Supportive communication pattern",
    "Core personality fit": "Naturally compatible core natures",
    "Relationship foundation": "A settled base for the partnership",
    "Deep partnership dynamics": "Ease with the deeper side of partnership",
    "Conflict & energy style": "Balanced approach to conflict",
    "Conflict balance": "Well-matched intensity",
    "Relationship timing": "A comparatively supportive current phase",
}

_ATTENTION = {
    "Emotional connection": "Emotional understanding may need extra care",
    "Temperament": "Different temperaments may require compromise",
    "Day-to-day ease": "Everyday rhythms may need coordination",
    "Attraction & chemistry": "Instinctive chemistry may need patience",
    "Communication": "Communication may need extra clarity",
    "Core personality fit": "Core natures may need conscious understanding",
    "Relationship foundation": "The partnership base may need steady effort",
    "Deep partnership dynamics": "Shared pressure may need conscious handling",
    "Conflict & energy style": "Conflict styles may need conscious coordination",
    "Conflict balance": "Intensity may need conscious coordination",
    "Relationship timing": "The current phase may reward patience",
}

_GLANCE = {
    "Emotional connection": "How naturally you read each other's feelings.",
    "Temperament": "How well your everyday natures sit together.",
    "Day-to-day ease": "How smoothly ordinary life together is likely to run.",
    "Attraction & chemistry": "The instinctive pull between you.",
    "Communication": "How easily you understand and resolve things together.",
    "Core personality fit": "How your underlying personalities meet.",
    "Relationship foundation": "How settled the base of the partnership looks.",
    "Deep partnership dynamics": "How you handle the deeper, more private side of partnership.",
    "Conflict & energy style": "How your action styles meet when things get tense.",
    "Conflict balance": "How evenly matched your intensity is.",
    "Relationship timing": "How supportive the present phase looks for the relationship.",
}

_IN_DEPTH = {
    SUPPORTIVE: (
        "This area reads as naturally supportive. You are likely to find this part of the "
        "relationship relatively easy to rely on, and it can act as a resource when other "
        "areas feel more demanding."
    ),
    MIXED: (
        "This area shows a workable but not automatic match. In ordinary life it may feel "
        "fine most of the time, with occasional moments where you notice you are not quite "
        "reading each other the same way. Clarity and a little patience usually carry it."
    ),
    CHALLENGING: (
        "This area is likely to ask more of both of you. That does not mean it cannot work, "
        "but it will probably respond to deliberate effort rather than to good intentions "
        "alone. Naming differences early tends to help more than avoiding them."
    ),
}


def _merge_state(statuses: Sequence[str]) -> str:
    values = [s for s in statuses if s != CONTEXTUAL]
    if not values:
        return MIXED
    if all(s == SUPPORTIVE for s in values):
        return SUPPORTIVE
    if all(s == CHALLENGING for s in values):
        return CHALLENGING
    if CHALLENGING in values and SUPPORTIVE not in values:
        return MIXED
    if SUPPORTIVE in values and CHALLENGING not in values:
        return SUPPORTIVE
    return MIXED


# ---------------------------------------------------------------------------
# Owner's BINARY scoring.
#
# Every factor with a maximum explicitly assigned by the supplied decks either
# MATCHES the owner's favourable rule (full allocated points) or does not
# (zero). There are no partial points: never 1/3, 2/3 or 3/6.
#
# The match condition is read from the SAME engine result that drives the
# interpretation - one source of truth. No scoring rule of its own is invented.
# ---------------------------------------------------------------------------
BINARY_SCORING: Dict[str, Dict[str, Any]] = {
    # source: "Dina Kuta (Tara gun milaan) (3 points)"
    "tara": {"maximum": 3, "match": ("Supportive",)},
    # source: "Gana gun milaan ... sanctioned 6 points" (same/acceptable direction)
    "gana": {"maximum": 6, "match": ("Strong alignment", "Supportive")},
    # source: "Rashi Kuta - 7 points are allocated"
    "rashi": {"maximum": 7, "match": ("Strong alignment", "Supportive")},
    # source: "Rashiadhipathi or Graha Maitre (5 points)"
    "graha_maitri": {"maximum": 5, "match": ("Strong alignment",)},
    # source: "Vasya Kuta (2 points)"
    "vasya": {"maximum": 2, "match": ("Supportive",)},
    # source: "Yoni Kuta" matrix; owner rule: a matrix score of 3 or 4 is a MATCH
    # (full 4), 0-2 is no match. The asymmetric MALE-row/FEMALE-column matrix is
    # unchanged - only the binary award threshold is defined here.
    "yoni": {"maximum": 4, "match": ("Strong alignment", "Supportive")},
}

# Factors with NO safely establishable binary rule. They keep their working and
# their qualitative state, but award no points.
UNSCORED_FACTORS: Dict[str, str] = {
    "nadi": "The supplied deck assigns no points to Nadi, so no maximum exists.",
}


def _matched(key: str, status: str) -> Optional[bool]:
    rule = BINARY_SCORING.get(key)
    if not rule:
        return None
    return status in rule["match"]


def _award(key: str, status: str) -> Optional[int]:
    matched = _matched(key, status)
    if matched is None:
        return None
    return BINARY_SCORING[key]["maximum"] if matched else 0


def build_total_score(kuta_results: Sequence[Any]) -> Dict[str, Any]:
    """TOTAL = the exact sum of the binary awards and their established maxima."""
    rows: List[Dict[str, Any]] = []
    awarded = 0
    maximum = 0
    for result in kuta_results:
        rule = BINARY_SCORING.get(result.key)
        if not rule:
            continue
        matched = _matched(result.key, result.status) or False
        points = rule["maximum"] if matched else 0
        awarded += points
        maximum += rule["maximum"]
        rows.append({
            "factor": WORKING_DISPLAY[result.key][0],
            "matched": matched,
            "points": points,
            "maximum": rule["maximum"],
        })
    return {
        "awarded": awarded,
        "maximum": maximum,
        "factors": rows,
        # Only labelled /36 when the configured maxima genuinely total 36.
        "outOf36": maximum == 36,
        "unscored": [
            {"factor": WORKING_DISPLAY[key][0], "reason": reason}
            for key, reason in UNSCORED_FACTORS.items()
        ],
    }


def build_interpreted(
    kuta_results: Sequence[Any],
    deep_results: Sequence[Any],
    names: Dict[str, str],
) -> Dict[str, Any]:
    """Deterministic public report from internal evidence."""
    status_by_key: Dict[str, str] = {}
    prose_by_key: Dict[str, str] = {}
    for result in list(kuta_results) + list(deep_results):
        status_by_key[result.key] = result.status
        # Kuta factors carry `summary`; deep factors carry `prose`.
        prose_by_key[result.key] = getattr(result, "prose", "") or getattr(result, "summary", "")

    at_a_glance: List[Dict[str, str]] = []
    in_depth: List[Dict[str, str]] = []
    strengths: List[str] = []
    attention: List[str] = []

    for label, sources in PUBLIC_THEMES:
        present = [status_by_key[s] for s in sources if s in status_by_key]
        if not present:
            continue
        state = _merge_state(present)
        at_a_glance.append({"category": label, "status": state, "interpretation": _GLANCE[label]})
        in_depth.append({"category": label, "interpretation": _IN_DEPTH[state]})
        if state == SUPPORTIVE:
            strengths.append(_STRENGTHS[label])
        elif state in (MIXED, CHALLENGING):
            attention.append(_ATTENTION[label])

    # PRIMARY overall status is driven by the Kuta Match Score ratio. The deep
    # analysis stays SECONDARY/contextual and never overwrites this status; its
    # vote counts are still reported for transparency.
    total = build_total_score(kuta_results)
    state = score_state(total["awarded"], total["maximum"])
    eligible = [status_by_key.get(key) for key in _eligible_keys()]
    deep = overall_state([s for s in eligible if s])
    overall = {"state": state, "counts": deep["counts"], "net": deep["net"], "total": deep["total"]}

    kavach_view = _kavach_view(overall["state"], len(strengths), len(attention))

    return {
        "overall": {"state": overall["state"], "summary": STATE_SUMMARY[overall["state"]]},
        "atAGlance": at_a_glance,
        "strengths": strengths[:4],
        "attentionAreas": attention[:4],
        "inDepth": in_depth,
        "kavachView": kavach_view,
        "people": {"bride": names.get("bride", ""), "groom": names.get("groom", "")},
        # Layer 2: the astrological working, openly shown. Built ONLY from the
        # results the engine already produced - never recalculated here.
        "technicalAnalysis": build_technical_analysis(kuta_results, deep_results),
        "overallWorking": build_overall_working(kuta_results, deep_results, overall),
        "totalScore": total,
    }


# ---------------------------------------------------------------------------
# Layer 2: the deliberate public working model.
# ---------------------------------------------------------------------------
# Only these astrology fields are ever published, and each is read from the
# result the engine already computed (one source of truth).
WORKING_DISPLAY: Dict[str, Any] = {
    "tara": ("Tara / Dina Kuta", "facts",
             ("brideMoonNakshatra", "groomMoonNakshatra", "remainder")),
    "gana": ("Gana", "facts",
             ("brideNakshatra", "brideGana", "groomNakshatra", "groomGana")),
    "nadi": ("Nadi", "facts",
             ("brideNakshatra", "brideNadi", "groomNakshatra", "groomNadi")),
    "rashi": ("Rashi Kuta", "facts",
              ("brideMoonSign", "groomMoonSign", "positionFromGroom", "mitigationApplied",
               "sameRuler", "rulersAreFriends")),
    "graha_maitri": ("Graha Maitri", "facts",
                     ("brideMoonRuler", "groomMoonRuler", "brideViewOfGroom", "groomViewOfBride")),
    "vasya": ("Vasya Kuta", "facts",
              ("brideMoonSign", "groomMoonSign", "brideInfluencesGroom", "groomInfluencesBride")),
    "yoni": ("Yoni Kuta", "facts",
             ("brideAnimal", "brideYoniGender", "groomAnimal", "groomYoniGender",
              "matrixOrientation", "score")),
    "personality_fit": ("Ascendant compatibility", "evidence",
                        ("brideLagna", "groomLagna", "brideRuler", "groomRuler",
                         "brideViewOfGroom", "groomViewOfBride")),
    "foundation": ("Partnership foundation (7th house)", "evidence",
                   ("brideRuler", "brideRulerHouse", "groomRuler", "groomRulerHouse", "flags")),
    "foundation_context": ("Partnership influences (contextual)", "evidence",
                           ("brideSeventh", "groomSeventh")),
    "deep_partnership": ("Deep partnership (8th house)", "evidence",
                         ("brideEighth", "brideEighthOccupants", "groomEighth",
                          "groomEighthOccupants")),
    "timing": ("Relationship timing (Dasha)", "evidence",
               ("currentLords", "friendlyCount")),
    "communication": ("Communication (Mercury)", "evidence",
                      ("brideSign", "groomSign", "distance", "pair")),
    "energy_style": ("Conflict & energy (Mars)", "evidence",
                     ("brideSign", "groomSign", "distance", "pair")),
    "conflict_balance": ("Kuja Dosha balance", "evidence",
                         ("brideHouse", "groomHouse", "brideCondition", "groomCondition")),
}


def _meaning(result: Any) -> str:
    return getattr(result, "summary", "") or getattr(result, "prose", "")


def build_technical_analysis(
    kuta_results: Sequence[Any],
    deep_results: Sequence[Any],
) -> List[Dict[str, Any]]:
    """The openly displayed working, in a fixed order.

    Values are read from the engine's own results; nothing is recomputed.
    """
    by_key: Dict[str, Any] = {}
    for result in list(kuta_results) + list(deep_results):
        by_key[result.key] = result

    ordered = [key for key, _ in WORKING_DISPLAY.items()]
    working: List[Dict[str, Any]] = []
    for key in ordered:
        result = by_key.get(key)
        if result is None:
            continue
        name, source, fields = WORKING_DISPLAY[key]
        raw = getattr(result, source, {}) or {}
        entry: Dict[str, Any] = {
            "factor": name,
            "values": {field: raw.get(field) for field in fields if field in raw},
            "result": result.status,
            "meaning": _meaning(result),
        }
        if key in BINARY_SCORING:
            matched = _matched(key, result.status)
            entry["matched"] = bool(matched)
            entry["points"] = _award(key, result.status)
            entry["maximum"] = BINARY_SCORING[key]["maximum"]
        working.append(entry)
    return working


def build_overall_working(
    kuta_results: Sequence[Any],
    deep_results: Sequence[Any],
    overall: Dict[str, Any],
) -> Dict[str, Any]:
    """Which factors voted, and which are contextual only."""
    from .deep import CONTEXTUAL_FACTORS, ELIGIBLE_FACTORS

    by_key: Dict[str, Any] = {}
    for result in list(kuta_results) + list(deep_results):
        by_key[result.key] = result

    def rows(keys: Sequence[str]) -> List[Dict[str, str]]:
        return [
            {"factor": WORKING_DISPLAY[key][0], "result": by_key[key].status}
            for key in keys if key in by_key
        ]

    return {
        "state": overall["state"],
        "counts": overall["counts"],
        "eligible": rows(ELIGIBLE_FACTORS),
        "contextualOnly": rows(CONTEXTUAL_FACTORS),
        "note": (
            "The overall assessment counts only the factors whose source rules give "
            "enough direction to classify them. Factors marked contextual only are "
            "shown for completeness and do not affect the assessment."
        ),
    }


def _eligible_keys() -> Sequence[str]:
    from .deep import ELIGIBLE_FACTORS

    return ELIGIBLE_FACTORS


def _kavach_view(state: str, strength_count: int, attention_count: int) -> str:
    if state == "STRONG POTENTIAL":
        return (
            "This pairing shows a strong, workable foundation with support across most of the "
            "areas examined. The differences that do exist look manageable. The overall "
            "pattern suggests real potential, while the quality of the relationship will "
            "still depend on the choices both people make."
        )
    if state == "GENERALLY SUPPORTIVE":
        return (
            "This pairing shows a workable foundation with meaningful strengths. Some "
            "differences may require patience and deliberate communication. The overall "
            "pattern suggests potential, while the quality of the relationship will still "
            "depend on how both people handle those differences."
        )
    if state == "SIGNIFICANT CHALLENGES":
        return (
            "This pairing carries several areas that are likely to ask for patience and "
            "deliberate effort. Nothing here rules the relationship out, but it would benefit "
            "from honest communication and realistic expectations."
        )
    return (
        "There is meaningful potential in this pairing, but the relationship may need "
        "consistent effort in a few important areas. The overall pattern is mixed rather "
        "than fixed, so much will depend on how both people approach the differences."
    )
