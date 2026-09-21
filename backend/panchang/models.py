"""Input/result containers for the standalone Panchang engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time
from typing import Optional


@dataclass(frozen=True)
class PanchangRequest:
    """Everything the engine needs. Fully independent of KAVACH."""

    on_date: date
    latitude: float
    longitude: float
    timezone_name: str
    label: str = ""
    at_time: Optional[time] = None  # optional reference time; defaults to sunrise


@dataclass
class Location:
    label: str
    latitude: float
    longitude: float
    timezone_name: str

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "timezone": self.timezone_name,
        }
