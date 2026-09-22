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
        """Customer-facing view.

        Internal evidence (`facts`), points and rule identity never cross this
        boundary: they stay on the server for tests, tracing and debugging. The
        customer receives a category, a state and plain-language interpretation
        only.
        """
        return {
            "label": self.label,
            "subtitle": self.subtitle,
            "status": self.status,
            "summary": self.summary,
        }
