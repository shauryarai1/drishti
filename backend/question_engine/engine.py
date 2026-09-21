"""KAVACH question-answering engine (System B ? Ask Kavach).

Exact question moment -> five Panchang channels -> QUESTION-MOMENT D1 ->
Graha-in-Bhava reading through the KAVACH channel lens -> synthesis -> ONE
natural answer. Standard Prashna and the Daily Moon rule are supplementary.

No birth details. No natal chart. No System A dependency.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from .composer import compose_answer, compose_greeting, compose_invalid
from .evaluator import evaluate_prashna
from .interpretation.synthesizer import synthesize
from .invalid import classify_message
from .moment import build_question_moment_context
from . import session


def _parse_timestamp(value: str) -> datetime:
    if not value:
        raise ValueError("question_timestamp is required")
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError("question_timestamp must include a timezone offset")
    return parsed


def _shell(status: str, composed: Dict[str, Any], question: str, requested: str) -> Dict[str, Any]:
    return {
        "engine": "kavach_question",
        "system": "B",
        "question": question,
        "requested_timestamp": requested,
        "used_timestamp": None,
        "is_follow_up": False,
        "uses_birth_details": False,
        "uses_natal_chart": False,
        "context": None,
        "prashna": None,
        "channels": None,
        "synthesis": None,
        "classification": None,
        "rules_matched": [],
        "standard_rules": [],
        "overall_tone": None,
        "daily_moon_signal": None,
        "answer": composed["answer"],
        "answered": composed["answered"],
        "status": status,
    }


def answer_question(
    question: str,
    question_timestamp: str,
    latitude: float,
    longitude: float,
    timezone_name: str = "Asia/Kolkata",
    location_label: str = "",
    is_follow_up: bool = False,
    original_timestamp: Optional[str] = None,
) -> Dict[str, Any]:
    message_kind = classify_message(question)

    # Greetings and nonsense never produce a reading, regardless of history.
    if message_kind == "greeting":
        return _shell("greeting", compose_greeting(), question, question_timestamp)
    if message_kind == "invalid":
        return _shell("invalid_input", compose_invalid(), question, question_timestamp)

    effective_timestamp = (
        original_timestamp if (is_follow_up and original_timestamp) else question_timestamp
    )
    moment_time = _parse_timestamp(effective_timestamp)

    context = build_question_moment_context(
        question_timestamp=moment_time,
        latitude=latitude,
        longitude=longitude,
        timezone_name=timezone_name,
        label=location_label,
    )

    evaluation = evaluate_prashna(question, context["moment"])
    synthesis = synthesize(evaluation)
    composed = compose_answer(evaluation, synthesis)

    # Ask KAVACH is powered internally by Tarot. The user sees only the answer.
    from tarot.engine import read_question

    key = session.session_key(latitude, longitude, location_label)
    previous = session.get_context(key)
    tarot = read_question(
        question,
        moment_time.isoformat(),
        previous={"domain": previous.get("domain"), "subcontext": previous.get("subcontext"),
                  "timeframe": previous.get("timeframe"), "intent": previous.get("intent"),
                  "subject": previous.get("subject")} if previous else None,
    )
    if tarot.get("answer") and not evaluation.get("safety"):
        composed = {"answered": True, "answer": tarot["answer"], "tone": composed["tone"]}
        session.remember(key, {"question": question, **tarot["context"]}, moment_time.isoformat())

    return {
        "engine": "kavach_question",
        "system": "B",
        "question": question,
        "used_timestamp": moment_time.isoformat(),
        "requested_timestamp": question_timestamp,
        "is_follow_up": bool(is_follow_up and original_timestamp),
        "uses_birth_details": False,
        "uses_natal_chart": False,
        "context": context,
        "prashna": evaluation,
        "channels": evaluation["channels"],
        "synthesis": synthesis,
        "tarot": tarot,
        "classification": evaluation["classification"],
        "rules_matched": evaluation["kavach_rules_applied"],
        "standard_rules": evaluation["standard_rules_applied"],
        "overall_tone": evaluation["overall_tone"],
        "daily_moon_signal": evaluation["daily_moon_signal"],
        "answer": composed["answer"],
        "answered": composed["answered"],
        "status": composed["tone"],
    }
