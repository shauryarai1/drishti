"""PRIVATE weekly forecast models. The customer-safe DTOs live in public.py."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class MoonPeriod:
    """One continuous chunk of a local day with a single transit Moon Nakshatra."""
    start: str                    # local ISO
    end: str                      # local ISO
    nakshatra: str
    relative_position: int = 0
    tara: str = ""
    tara_number: int = 0
    nature: str = ""
    special_roles: List[str] = field(default_factory=list)

    def to_private_dict(self) -> Dict[str, Any]:
        return {
            "start": self.start,
            "end": self.end,
            "moonNakshatra": self.nakshatra,
            "relativePosition": self.relative_position,
            "taraNumber": self.tara_number,
            "tara": self.tara,
            "nature": self.nature,
            "specialRoles": list(self.special_roles),
        }


@dataclass(frozen=True)
class DayForecast:
    date: str
    periods: List[MoonPeriod] = field(default_factory=list)

    def to_private_dict(self) -> Dict[str, Any]:
        return {"date": self.date, "periods": [item.to_private_dict() for item in self.periods]}


@dataclass(frozen=True)
class WeeklyForecast:
    janma_nakshatra: str
    start_date: str
    timezone: str
    days: List[DayForecast] = field(default_factory=list)

    def to_private_dict(self) -> Dict[str, Any]:
        return {
            "janmaNakshatra": self.janma_nakshatra,
            "startDate": self.start_date,
            "timezone": self.timezone,
            "days": [item.to_private_dict() for item in self.days],
        }

    def periods(self) -> List[MoonPeriod]:
        return [period for day in self.days for period in day.periods]
