"""Editable KAVACH question-rule registry.

The astrologer has not yet supplied the question-answering methodology, so no
rules are registered. Do not add generic astrology rules here.
"""

from __future__ import annotations

from typing import Any, Dict, List

KAVACH_QUESTION_RULES: List[Dict[str, Any]] = []

NO_RULE_MESSAGE = (
    "Question moment calculated successfully. "
    "No approved KAVACH interpretation rule matched this question yet."
)
