"""Typed results for the KAVACH YES / NO engine.

The public payload deliberately exposes only the verdict and the explanation.
The hour/minute numbers, the two planets and the relationship are engine
mechanics and stay internal (available on the result object for tests, tracing
and a future "Why?" panel, but never returned by default).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class YesNoResult:
    """One deterministic YES / NO / 50-50 evaluation."""

    verdict: str                      # YES | NO | 50/50
    interpretation: str
    question: str = ""
    local_time: str = ""              # "HH:MM" as used by the engine
    timezone: str = ""
    hour_number: int = 0              # 1-9
    minute_number: int = 0            # 1-9
    hour_planet: str = ""
    minute_planet: str = ""
    relationship: str = ""            # FRIEND | ENEMY | NEUTRAL

    def to_public(self) -> Dict[str, Any]:
        """Customer-facing payload: the verdict and the explanation only."""
        return {"verdict": self.verdict, "interpretation": self.interpretation}

    def metadata(self) -> Dict[str, Any]:
        """Internal mechanics, for tests, tracing or a future "Why?" panel."""
        return {
            "question": self.question,
            "local_time": self.local_time,
            "timezone": self.timezone,
            "hour_number": self.hour_number,
            "minute_number": self.minute_number,
            "hour_planet": self.hour_planet,
            "minute_planet": self.minute_planet,
            "relationship": self.relationship,
        }


@dataclass(frozen=True)
class SafetyRefusal:
    """Returned instead of a verdict for topics that must not be answered."""

    message: str
    reason: str = ""
    question: str = ""

    def to_public(self) -> Dict[str, Any]:
        return {"verdict": None, "interpretation": self.message}

    def metadata(self) -> Optional[Dict[str, Any]]:
        return {"question": self.question, "reason": self.reason}
