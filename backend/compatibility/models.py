"""Types for the compatibility report."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

# Restrained states. No aggregate value is invented anywhere in this feature.
STATUSES = ("Strong alignment", "Supportive", "Mixed", "Needs attention")


@dataclass(frozen=True)
class PersonFacts:
    """The chart facts this methodology needs, from the authoritative Kundli."""

    name: str
    role: str              # "bride" | "groom" - the source method is directional
    moon_sign: str
    moon_nakshatra: str
    moon_ruler: str


@dataclass(frozen=True)
class FactorResult:
    key: str
    label: str
    subtitle: str
    status: str
    summary: str
    facts: Dict[str, Any] = field(default_factory=dict)
    # Only ever set where the supplied deck gives a completely determinable
    # value. Never summed into a total.
    points_awarded: Optional[int] = None

    def to_public(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "key": self.key,
            "label": self.label,
            "subtitle": self.subtitle,
            "status": self.status,
            "summary": self.summary,
            "facts": self.facts,
        }
        if self.points_awarded is not None:
            payload["points"] = self.points_awarded
        return payload
