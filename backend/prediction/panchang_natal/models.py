"""Structured output containers for the Panchang natal significator engine."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PanchangLimb:
    limb: str
    value: str
    lord: str
    purpose: List[str]
    context: Dict[str, Any] = field(default_factory=dict)
    natal_placement: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "limb": self.limb,
            "value": self.value,
            "context": self.context,
            "selected_lord": self.lord,
            "interpretation_domain": self.purpose,
            "natal_placement": self.natal_placement,
        }
