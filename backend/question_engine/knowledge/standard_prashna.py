"""STANDARD PRASHNA layer (common Vedic Prashna foundations).

Informational only in V1: these rules describe the chart, they do NOT
produce a tone or a prediction.
"""

from __future__ import annotations

from typing import Any, Dict, List

STANDARD_PROVENANCE: Dict[str, str] = {
    "source_type": "standard_prashna",
    "source": "common_prashna_foundations",
    "status": "approved",
}

RASHI_LORDS: Dict[str, str] = {
    "Mesha": "Mars", "Vrishabha": "Venus", "Mithuna": "Mercury",
    "Karka": "Moon", "Simha": "Sun", "Kanya": "Mercury",
    "Tula": "Venus", "Vrishchika": "Mars", "Dhanu": "Jupiter",
    "Makara": "Saturn", "Kumbha": "Saturn", "Meena": "Jupiter",
}

STANDARD_RULES: List[Dict[str, Any]] = [
    {
        "rule_id": "SP_CONTEXT_001",
        "kind": "informational",
        "description": "Lagna and Lagna lord describe the question's overall standing.",
        "provenance": STANDARD_PROVENANCE,
    },
    {
        "rule_id": "SP_CONTEXT_002",
        "kind": "informational",
        "description": "Moon and its Nakshatra describe the emotional/mental climate of the question.",
        "provenance": STANDARD_PROVENANCE,
    },
    {
        "rule_id": "SP_CONTEXT_003",
        "kind": "informational",
        "description": "The relevant Bhava and its lord describe the matter asked about.",
        "provenance": STANDARD_PROVENANCE,
    },
]


def rashi_lord(rashi: str) -> str | None:
    return RASHI_LORDS.get(rashi)
