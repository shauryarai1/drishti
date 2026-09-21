"""Containers for a question turn's calculation context."""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class QuestionTurn:
    question: str
    question_timestamp: str
    timezone: str
    latitude: float
    longitude: float
    location_label: str = ""
    is_follow_up: bool = False
    rules_matched: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "question_timestamp": self.question_timestamp,
            "timezone": self.timezone,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "location_label": self.location_label,
            "is_follow_up": self.is_follow_up,
            "rules_matched": self.rules_matched,
        }
