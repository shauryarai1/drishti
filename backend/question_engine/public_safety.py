"""Public language filter.

Public readings never expose Jyotish or calculation internals. If a composed
sentence somehow contains one, it is replaced with a single graceful message.
"""

from __future__ import annotations

import re
from typing import Tuple

FORBIDDEN: Tuple[str, ...] = (
    "vaar", "tithi", "karana", "nakshatra", "yoga", "bhava", "lagna", "rashi",
    "house", "channel", "rule_id", "source_type", "selected planet", "dignity",
    "sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu",
    "could not be composed", "interpretation rule", "significator", "chart",
    "card", "cards", "tarot", "spread", "upright", "reversed", "arcana",
    "wands", "cups", "swords", "pentacles",
)

FALLBACK = (
    "A reading for this moment is available, but it could not be phrased clearly. "
    "Please send the question once more."
)


def filter_public(text: str) -> str:
    if not text:
        return text
    lowered = text.lower()
    if re.search(r"\d", text):
        return FALLBACK
    if any(token in lowered for token in FORBIDDEN):
        return FALLBACK
    return text
