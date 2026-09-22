"""Safety gate for KAVACH YES / NO.

Some questions must never receive an astrological YES / NO. They get a short
supportive message instead. This runs BEFORE any calculation, so the verdict is
never even computed for those questions.

Word-boundary matching is used for short tokens so ordinary words such as
"deadline" or "diet" are not caught by "dead" or "die".
"""

from __future__ import annotations

import re
from typing import Optional, Tuple

SAFE_MESSAGE = (
    "This is something that deserves real-world support rather than an astrological "
    "yes or no. Please speak to a qualified professional, or to someone you trust who "
    "can help you directly."
)

# (category, patterns). Categories are internal only; the user sees SAFE_MESSAGE.
_UNSAFE_PATTERNS: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    ("death", (
        r"\bdeath\b", r"\bdie\b", r"\bdying\b", r"\bdied\b", r"\bdead\b",
        r"\bwhen will i die\b", r"\bhow long will i live\b", r"\blifespan\b",
        r"\blife expectancy\b",
    )),
    ("illness", (
        r"\bserious illness\b", r"\bterminal illness\b", r"\blife[- ]threatening\b",
        r"\bam i going to survive\b", r"\bwill i survive\b", r"\bfatal\b", r"\btumou?r\b",
    )),
    ("self_harm", (
        r"\bsuicide\b", r"\bsuicidal\b", r"\bself[- ]harm\b", r"\bkill myself\b",
        r"\bend my life\b", r"\bhurt myself\b", r"\boverdose\b",
    )),
    ("emergency", (
        r"\bmedical emergency\b", r"\bemergency room\b", r"\bambulance\b",
        r"\bemergency surgery\b", r"\bhospital right now\b", r"\boverdosing\b",
    )),
    ("dangerous", (
        r"\billegal\b", r"\bcommit a crime\b", r"\bdangerous activity\b",
        r"\bweapon\b", r"\bhurt someone\b", r"\bharm someone\b",
    )),
)

_COMPILED = tuple(
    (category, tuple(re.compile(pattern) for pattern in patterns))
    for category, patterns in _UNSAFE_PATTERNS
)


def unsafe_category(question: str) -> Optional[str]:
    """The matched unsafe category, or None when the question is safe to answer."""
    text = (question or "").lower()
    if not text:
        return None
    for category, patterns in _COMPILED:
        if any(pattern.search(text) for pattern in patterns):
            return category
    return None


def sensitive_refusal(question: str) -> Optional[str]:
    """The safe message when the question must not receive a verdict, else None."""
    if unsafe_category(question):
        return SAFE_MESSAGE
    return None
