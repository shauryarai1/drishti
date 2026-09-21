"""PRIVATE 7-day weekly forecast engine.

Astrology inputs are ONLY the native's Janma Moon Nakshatra and the transit
Moon Nakshatra through the forecast window. No planets, houses, aspects,
dignity, Dasha or Panchang limbs are consulted.
"""

from __future__ import annotations

from datetime import date as date_type, datetime, time, timedelta
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from navtara import get_navtara, get_special_roles
from navtara.engine import get_janma_nakshatra_from_birth_details

from .models import DayForecast, MoonPeriod, WeeklyForecast
from .moon_transits import moon_nakshatra_at, moon_periods

METHODOLOGY_VERSION = "weekly-navtara-v1"
DEFAULT_DAYS = 7


def get_janma_moon_nakshatra(birth: Dict[str, Any]) -> Dict[str, Any]:
    """Janma Moon Nakshatra from the EXISTING birth-chart calculator."""
    return get_janma_nakshatra_from_birth_details(
        date=str(birth["date"]), time=str(birth["time"]),
        place=birth.get("place") or "", latitude=float(birth["latitude"]),
        longitude=float(birth["longitude"]),
    )


def _classify(janma_nakshatra: str, nakshatra: str) -> Dict[str, Any]:
    info = get_navtara(janma_nakshatra, nakshatra)
    return {
        "relative_position": info["position"],
        "tara": info["tara"],
        "tara_number": info["taraNumber"],
        "nature": info["nature"],
        "special_roles": list(info["specialRoles"]) or get_special_roles(info["position"]),
    }


def build_week(
    janma_nakshatra: str,
    forecast_date: date_type,
    latitude: float,
    longitude: float,
    timezone_name: str = "Asia/Kolkata",
    days: int = DEFAULT_DAYS,
) -> WeeklyForecast:
    """PRIVATE weekly forecast: Janma Nakshatra vs transit Moon Nakshatras."""
    tz = ZoneInfo(timezone_name)
    day_forecasts: List[DayForecast] = []

    for offset in range(days):
        on_date = forecast_date + timedelta(days=offset)
        day_start = datetime.combine(on_date, time(0, 0), tzinfo=tz)
        day_end = day_start + timedelta(days=1)

        periods: List[MoonPeriod] = []
        for start, end in moon_periods(day_start, day_end):
            nakshatra = moon_nakshatra_at(start + (end - start) / 2)
            classification = _classify(janma_nakshatra, nakshatra)
            periods.append(MoonPeriod(
                start=start.isoformat(),
                end=end.isoformat(),
                nakshatra=nakshatra,
                relative_position=classification["relative_position"],
                tara=classification["tara"],
                tara_number=classification["tara_number"],
                nature=str(classification["nature"]),
                special_roles=classification["special_roles"],
            ))
        day_forecasts.append(DayForecast(date=on_date.isoformat(), periods=periods))

    return WeeklyForecast(
        janma_nakshatra=janma_nakshatra,
        start_date=forecast_date.isoformat(),
        timezone=timezone_name,
        days=day_forecasts,
    )


def build_weekly_forecast(
    birth: Dict[str, Any],
    forecast_start: str,
    forecast_latitude: float,
    forecast_longitude: float,
    forecast_timezone: str = "Asia/Kolkata",
    days: int = DEFAULT_DAYS,
    janma_nakshatra: Optional[str] = None,
) -> WeeklyForecast:
    """Full flow: birth details -> Janma Moon Nakshatra -> private week.

    Birth location and forecast location are separate on purpose: transition
    times are presented in the FORECAST location's local timezone.
    """
    if not janma_nakshatra:
        janma_nakshatra = str(get_janma_moon_nakshatra(birth)["nakshatra"])
    return build_week(
        janma_nakshatra=janma_nakshatra,
        forecast_date=date_type.fromisoformat(forecast_start),
        latitude=float(forecast_latitude),
        longitude=float(forecast_longitude),
        timezone_name=forecast_timezone,
        days=days,
    )
