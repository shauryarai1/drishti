"""The interpreted, customer-facing compatibility report.

Builds the public model from internal evidence. Nothing here serializes a rule
name, a planet, a house, a sign distance, an animal, a gender, a matrix value,
a point or a reason code - only categories, states and prose.
"""

from __future__ import annotations

from typing import Any, Dict, List, Sequence

from .deep import (
    CHALLENGING, CONTEXTUAL, MIXED, SUPPORTIVE, STATE_SUMMARY, overall_state,
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

    # Overall classification uses only the verdict-eligible statuses.
    eligible = [status_by_key.get(key) for key in _eligible_keys()]
    overall = overall_state([s for s in eligible if s])

    kavach_view = _kavach_view(overall["state"], len(strengths), len(attention))

    return {
        "overall": {"state": overall["state"], "summary": STATE_SUMMARY[overall["state"]]},
        "atAGlance": at_a_glance,
        "strengths": strengths[:4],
        "attentionAreas": attention[:4],
        "inDepth": in_depth,
        "kavachView": kavach_view,
        "people": {"bride": names.get("bride", ""), "groom": names.get("groom", "")},
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
