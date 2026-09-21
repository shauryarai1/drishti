"""KAVACH CUSTOM layer — astrologer-supplied rules. NOT classical Jyotish."""

from __future__ import annotations

from typing import Any, Dict

KAVACH_PROVENANCE: Dict[str, str] = {
    "source_type": "kavach_custom",
    "source": "kavach_astrologer_rule",
    "status": "approved",
}

# Astrologer's supplied rule, applied here to the QUESTION-MOMENT D1.
KAVACH_RULES: Dict[str, Dict[str, Any]] = {
    "KC_DAILY_MOON_001": {
        "rule_id": "KC_DAILY_MOON_001",
        "kind": "tone",
        "description": (
            "Question-moment Moon Nakshatra lord placed in house 6, 8 or 12 "
            "gives an extra-care indication; any other house is supportive."
        ),
        "provenance": KAVACH_PROVENANCE,
    },
}

EXTRA_CARE_HOUSES = frozenset({6, 8, 12})

SUPPORTIVE_TEMPLATE = (
    "The overall indication for the period is supportive. There is no extra-care "
    "signal from KAVACH's current day-pattern check. Treat this as general "
    "astrological guidance rather than a guaranteed outcome."
)

EXTRA_CARE_TEMPLATE = (
    "The period carries an extra-care indication. It may be better to move more "
    "deliberately, avoid unnecessary pressure, and leave room for plans to change. "
    "This is a caution signal rather than a prediction that something bad will happen."
)

SAFETY_REFUSALS: Dict[str, str] = {
    "lifespan": (
        "KAVACH does not answer questions about lifespan, death or fatal events. "
        "If this concerns you, please speak with someone you trust."
    ),
    "medical": (
        "KAVACH does not provide medical diagnoses. Please consult a qualified "
        "medical professional for health concerns."
    ),
}

SAFETY_TOPICS: Dict[str, list] = {
    "lifespan": ["die", "death", "how long will i live", "lifespan", "when will i die", "shorten my life"],
    "medical": ["diagnose", "diagnosis", "cure my", "what disease", "is it cancer", "medical condition"],
}


def safety_response(question: str) -> str | None:
    lowered = (question or "").lower()
    for topic, phrases in SAFETY_TOPICS.items():
        if any(phrase in lowered for phrase in phrases):
            return SAFETY_REFUSALS[topic]
    return None
