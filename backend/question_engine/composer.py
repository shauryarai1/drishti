"""Compose ONE natural Ask KAVACH answer from the synthesis.

The answer is written, not concatenated: an assessment, the main theme, at
most one caution, and one piece of guidance. Public text is passed through the
public language filter before it leaves the engine.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .invalid import GREETING_MESSAGE, INVALID_MESSAGE
from .public_safety import filter_public

OPENERS: Dict[str, str] = {
    "supportive": "On {topic}, the indication looks manageable.",
    "mixed": "On {topic}, there is real support here, though it asks for care in places.",
    "extra_care": "On {topic}, this is a period that rewards a careful, deliberate approach.",
    "unclear": "On {topic}, the picture is not clear enough to say more than this.",
}

CAUTION_LEAD = "One caution worth respecting:"
GUIDANCE_LEAD = "In practice:"
DAILY_EXTRA = (
    "There is also a mild extra-care signal around this moment, so leaving room "
    "for plans to change is wise."
)
CLOSING = "Treat this as general astrological guidance rather than a guaranteed outcome."


def _sentence(text: Any) -> str:
    cleaned = " ".join(str(text or "").split())
    if cleaned and not cleaned.endswith((".", "!", "?")):
        cleaned += "."
    return cleaned


def compose_answer(evaluation: Dict[str, Any], synthesis: Dict[str, Any]) -> Dict[str, Any]:
    if evaluation.get("safety"):
        return {"answered": True, "answer": evaluation["safety"], "tone": "refusal"}

    assessment = synthesis.get("assessment", "unclear")
    opener = OPENERS.get(assessment, OPENERS["unclear"]).format(topic=synthesis["topic_label"])

    parts: List[str] = [opener]
    if synthesis.get("main_theme"):
        parts.append(_sentence(synthesis["main_theme"])[0].upper() + _sentence(synthesis["main_theme"])[1:])

    if assessment in ("mixed", "extra_care") and synthesis.get("caution"):
        parts.append(f"{CAUTION_LEAD} {_sentence(synthesis['caution'])}")

    if synthesis.get("guidance"):
        parts.append(f"{GUIDANCE_LEAD} {_sentence(synthesis['guidance'])}")

    if assessment == "extra_care":
        parts.append(DAILY_EXTRA)

    if len(parts) <= 4:
        parts.append(CLOSING)

    answer = filter_public(" ".join(parts))
    tone = {"extra_care": "caution", "mixed": "mixed"}.get(assessment, assessment)
    return {"answered": True, "answer": answer, "tone": tone}


def compose_greeting() -> Dict[str, Any]:
    return {"answered": False, "answer": GREETING_MESSAGE, "tone": "greeting"}


def compose_invalid() -> Dict[str, Any]:
    return {"answered": False, "answer": INVALID_MESSAGE, "tone": "invalid_input"}
