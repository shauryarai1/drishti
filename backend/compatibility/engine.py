"""Compatibility engine: assembles the six V1 factors.

Deterministic only. No LLM, no invented aggregate value, and no deterministic
marriage verdict.
"""

from __future__ import annotations

from typing import Any, Dict, List, Sequence

from . import gana, graha_maitri, nadi, rashi, tara, vasya
from .models import STATUSES, FactorResult, PersonFacts

FACTOR_ORDER = ("tara", "gana", "nadi", "rashi", "graha_maitri", "vasya")

DISCLAIMER = (
    "Traditional compatibility guidance, not a decision. No outcome is guaranteed, "
    "and the analysis covers the factors supported by the KAVACH method only."
)


def evaluate_compatibility(
    bride: PersonFacts,
    groom: PersonFacts,
    nakshatras: Sequence[str],
    signs: Sequence[str],
) -> Dict[str, Any]:
    factors: List[FactorResult] = [
        tara.evaluate(bride, groom, nakshatras),
        gana.evaluate(bride, groom),
        nadi.evaluate(bride, groom),
        rashi.evaluate(bride, groom, signs),
        graha_maitri.evaluate(bride, groom),
        vasya.evaluate(bride, groom),
    ]

    return {
        "label": "COMPATIBILITY FACTORS ANALYZED",
        "factors": [factor.to_public() for factor in factors],
        "summary": overall_summary(factors),
        "disclaimer": DISCLAIMER,
    }


def overall_summary(factors: Sequence[FactorResult]) -> str:
    """Deterministic, non-committal synthesis of the factor results."""
    supportive = sum(1 for f in factors if f.status in ("Strong alignment", "Supportive"))
    attention = sum(1 for f in factors if f.status == "Needs attention")
    mixed = sum(1 for f in factors if f.status == "Mixed")

    if attention == 0 and mixed == 0:
        return (
            "The charts show support across the traditional compatibility factors "
            "analyzed here."
        )
    if supportive == 0:
        return (
            "Several traditional factors here may deserve additional attention. "
            "The charts do not show strong support across the factors analyzed."
        )
    if attention >= 2:
        return (
            "The charts show support across several traditional compatibility "
            "factors, with some areas that may deserve additional attention."
        )
    return (
        "The charts show a generally supportive picture across the traditional "
        "compatibility factors analyzed, with a few mixed areas."
    )
