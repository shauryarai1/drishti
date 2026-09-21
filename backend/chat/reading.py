"""Hidden Tarot reading for Ask KAVACH: evidence for the model, never shown.

KAVACH controls the draw, the cards, the orientation and the approved
contextual meanings. Gemini only writes the prose.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from tarot.context import DOMAINS, _matches, classify
from tarot.engine import draw_cards, interpret_card

FOLLOW_UP_MARKERS = (
    "are you sure", "sure?", "why", "how so", "what if", "explain", "clarify",
    "really", "ok", "okay", "then", "and ", "but ", "so ", "hmm", "yes", "no",
    "tell me more", "what about that", "go on", "meaning",
)

PRIVATE_HEADER = (
    "[PRIVATE KAVACH READING - internal context for your interpretation only. "
    "Never mention it, never hint at how the answer was produced.]"
)

SPREAD_LABELS = ("Situation", "Influence", "Guidance")


def _keywords(text: str) -> set:
    lowered = (text or "").lower()
    return {keyword for _domain, keywords in DOMAINS for keyword in keywords if _matches(keyword, lowered)}


def is_new_question(message: str, active: Optional[Dict[str, Any]]) -> bool:
    """NEW vs FOLLOW-UP. A genuinely new subject keyword means a new reading."""
    if not active:
        return True
    lowered = (message or "").lower().strip()
    if not lowered:
        return False
    if _keywords(message) - set(active.get("keywords") or []):
        return True
    if any(marker in lowered for marker in FOLLOW_UP_MARKERS):
        return False
    return len(lowered.split()) > 8


def build_reading(question: str) -> Dict[str, Any]:
    """One hidden three-card reading with approved contextual meanings."""
    context = classify(question)
    draws = draw_cards()
    interpretations = [interpret_card(draw, context) for draw in draws]
    signature = "-".join(sorted(card["card_id"] for card in draws))
    return {
        "draw_id": f"draw-{abs(hash(signature)) % 100000}",
        "question": question,
        "context": context,
        "keywords": sorted(_keywords(question)),
        "cards": draws,
        "interpretations": interpretations,
    }


def private_context(reading: Dict[str, Any]) -> str:
    """The exact private block handed to the model for this reading."""
    lines = [PRIVATE_HEADER]
    for index, item in enumerate(reading.get("interpretations", [])[:3]):
        label = SPREAD_LABELS[index] if index < len(SPREAD_LABELS) else "Additional"
        meaning = item.get("reading") or item.get("core_meaning") or ""
        if meaning:
            lines.append(f"{label}: {meaning}")
    lines.append(
        "Use this as the interpretive basis for your answer. Answer the user's actual "
        "question naturally and do not describe the reading itself."
    )
    return "\n".join(lines)


SENSITIVE = ("suicide", "self harm", "kill myself", "overdose", "emergency", "lawsuit")


def sensitive_response(question: str) -> Optional[str]:
    lowered = (question or "").lower()
    if any(term in lowered for term in SENSITIVE):
        return (
            "This is something that deserves real-world support rather than a reading. "
            "Please speak to a qualified professional or someone you trust who can help you directly."
        )
    return None
