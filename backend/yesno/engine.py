"""KAVACH YES / NO engine: time -> numbers -> planets -> relationship -> verdict.

The whole chain is deterministic code. No language model participates in it, and
no part of it can be overridden by the wording of the question.

    evaluate_yes_no(question, local_datetime) -> YesNoResult | SafetyRefusal

The question is used only to phrase the explanation. The verdict depends purely
on the local time.
"""

from __future__ import annotations

from datetime import datetime
from typing import Union

from .interpretation import build_interpretation
from .numbers import hour_number, minute_number
from .planets import planet_for_number
from .relationships import planet_relationship, verdict_for_relationship
from .safety import sensitive_refusal
from .types import SafetyRefusal, YesNoResult


def verdict_for_time(hour: int, minute: int) -> str:
    """The verdict for a local hour/minute, independent of any question."""
    hour_planet = planet_for_number(hour_number(hour))
    minute_planet = planet_for_number(minute_number(minute))
    return verdict_for_relationship(planet_relationship(hour_planet, minute_planet))


def evaluate_yes_no(question: str, local_datetime: datetime,
                    timezone_name: str = "") -> Union[YesNoResult, SafetyRefusal]:
    """Evaluate one YES / NO question from the exact local time it was asked.

    `local_datetime` must already be the user's local time (see
    yesno.timezone.resolve_local_datetime). It may be timezone-aware; the hour
    and minute are taken from the wall clock as given.
    """
    if not isinstance(local_datetime, datetime):
        raise ValueError("local_datetime must be a datetime")

    # Safety first: some questions never receive a verdict.
    refusal = sensitive_refusal(question)
    if refusal:
        from .safety import unsafe_category

        return SafetyRefusal(message=refusal, reason=unsafe_category(question) or "", question=question or "")

    hour = local_datetime.hour
    minute = local_datetime.minute

    h_number = hour_number(hour)
    m_number = minute_number(minute)
    hour_planet = planet_for_number(h_number)
    minute_planet = planet_for_number(m_number)

    # Direction is fixed: hour planet -> minute planet.
    relationship = planet_relationship(hour_planet, minute_planet)
    verdict = verdict_for_relationship(relationship)

    interpretation = build_interpretation(
        question=question,
        verdict=verdict,
        hour_planet=hour_planet,
        minute_planet=minute_planet,
        relationship=relationship,
        hour_number=h_number,
        minute_number=m_number,
    )

    return YesNoResult(
        verdict=verdict,
        interpretation=interpretation,
        question=question or "",
        local_time=f"{hour:02d}:{minute:02d}",
        timezone=timezone_name,
        hour_number=h_number,
        minute_number=m_number,
        hour_planet=hour_planet,
        minute_planet=minute_planet,
        relationship=relationship,
    )
