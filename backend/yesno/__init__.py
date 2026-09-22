"""KAVACH YES / NO - a deterministic time-based astrology engine.

A NEW, isolated feature. It is NOT Ask KAVACH, not Tarot and not the reading
router: nothing here is imported by, or wired into, any existing KAVACH system.

The exact LOCAL time at which a question is asked determines two planetary
numbers (hour digits and minute digits, reduced separately). Those two planets
determine a verdict through the project's approved directional BNN relationship
registry:

    FRIEND  -> YES
    ENEMY   -> NO
    NEUTRAL -> 50/50

The verdict is computed by plain deterministic code. No language model ever
decides it. The interpretation is a deterministic template.

    evaluate_yes_no(question, local_datetime) -> YesNoResult | SafetyRefusal
"""

from .engine import evaluate_yes_no, verdict_for_time
from .interpretation import CERTAINTY_DISCLAIMER, build_interpretation
from .numbers import (
    ZERO_HANDLING,
    hour_number,
    minute_number,
    reduce_to_single_digit,
)
from .planets import NUMBER_TO_PLANET, PLANET_THEMES, planet_for_number
from .relationships import (
    EVEN,
    NO,
    RELATIONSHIP_VERDICTS,
    RELATIONSHIP_MATRIX,
    YES,
    planet_relationship,
    verdict_for_relationship,
)
from .safety import SAFE_MESSAGE, sensitive_refusal
from .timezone import local_datetime_for, resolve_local_datetime, resolve_timezone
from .types import SafetyRefusal, YesNoResult

__all__ = [
    "evaluate_yes_no",
    "verdict_for_time",
    "build_interpretation",
    "CERTAINTY_DISCLAIMER",
    "reduce_to_single_digit",
    "hour_number",
    "minute_number",
    "ZERO_HANDLING",
    "NUMBER_TO_PLANET",
    "PLANET_THEMES",
    "planet_for_number",
    "planet_relationship",
    "verdict_for_relationship",
    "RELATIONSHIP_MATRIX",
    "RELATIONSHIP_VERDICTS",
    "YES",
    "NO",
    "EVEN",
    "sensitive_refusal",
    "SAFE_MESSAGE",
    "resolve_timezone",
    "local_datetime_for",
    "resolve_local_datetime",
    "YesNoResult",
    "SafetyRefusal",
]
