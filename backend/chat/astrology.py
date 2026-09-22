"""Astrology context for Ask KAVACH.

Builds a compact, factual chart block from the birth details already present in
the Ask request, using the EXISTING KAVACH calculation engine (`calculator`) and
the existing current-dasha reader. No astrology methodology is added or changed
here - this module only formats what the approved engine already returns.

Returns "" when the birth details needed for a chart are not available, so the
caller can tell the model to ask for them instead of inventing a placement.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger("kavach.chat")

CHART_HEADER = (
    "[KAVACH CHART CONTEXT - factual chart data for your interpretation. Use only "
    "the placements listed here, never invent one, and never mention this block.]"
)


def _parse_local(timestamp: str):
    from datetime import datetime

    value = (timestamp or "").strip()
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        pass
    for pattern in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(value, pattern)
        except ValueError:
            continue
    return None


def _format_chart(chart: Any) -> list:
    lines: list = []
    ascendant = getattr(chart, "ascendant", None)
    if ascendant is not None:
        sign = getattr(ascendant, "sign", None)
        if sign:
            lines.append(f"Lagna (ascendant): {sign}")

    planets = list(getattr(chart, "planets", []) or [])
    moon = next((p for p in planets if getattr(p, "name", "") == "Moon"), None)
    if moon is not None and getattr(moon, "sign", None):
        lines.append(f"Moon sign (rashi): {moon.sign}")

    lines.append("Planets (sign, house, degree):")
    for planet in planets:
        name = getattr(planet, "name", "") or ""
        sign = getattr(planet, "sign", "") or ""
        house = getattr(planet, "house", None)
        degree = getattr(planet, "degree", None)
        if not name or not sign:
            continue
        where = f"{sign}, house {house}" if house else sign
        if isinstance(degree, (int, float)):
            where = f"{where}, {degree:.1f} deg"
        lines.append(f"- {name}: {where}")

    houses = list(getattr(chart, "houses", []) or [])
    if houses:
        listed = ", ".join(
            f"H{getattr(h, 'number', '?')} {getattr(h, 'sign', '')}".strip()
            for h in houses[:12]
        )
        lines.append(f"Whole-sign houses: {listed}")
    return lines


def _format_dasha(payload: Any) -> list:
    try:
        from dasha_reading import build_current_dasha_reading

        birth = {
            "date": _parse_local(getattr(payload, "timestamp", "")).strftime("%Y-%m-%d"),
            "time": _parse_local(getattr(payload, "timestamp", "")).strftime("%H:%M"),
            "place": getattr(payload, "location_label", "") or "",
            "latitude": getattr(payload, "latitude", None),
            "longitude": getattr(payload, "longitude", None),
            "timezone": getattr(payload, "timezone", "") or "Asia/Kolkata",
        }
        dasha = build_current_dasha_reading(birth)
    except Exception as exc:  # a dasha failure must never break the chart answer
        logger.warning("Dasha context skipped: %s", type(exc).__name__)
        return []

    lines: list = []
    mahadasha = (dasha or {}).get("mahadasha") or {}
    antardasha = (dasha or {}).get("antardasha") or {}
    if mahadasha.get("name"):
        lines.append(f"Current Mahadasha: {mahadasha['name']} (until {str(mahadasha.get('end'))[:10]})")
    if antardasha.get("name"):
        lines.append(f"Current Antardasha: {antardasha['name']} (until {str(antardasha.get('end'))[:10]})")
    return lines


def chart_context(payload: Any) -> str:
    """Compact factual chart block, or "" when birth details are unavailable."""
    latitude = getattr(payload, "latitude", None)
    longitude = getattr(payload, "longitude", None)
    local = _parse_local(getattr(payload, "timestamp", ""))
    if latitude is None or longitude is None or local is None:
        return ""

    try:
        from calculator import BirthData, generate_chart

        birth = BirthData(
            date=local.strftime("%Y-%m-%d"),
            time=local.strftime("%H:%M"),
            place=getattr(payload, "location_label", "") or "",
            latitude=float(latitude),
            longitude=float(longitude),
        )
        chart = generate_chart(birth)
    except Exception as exc:
        logger.warning("Chart context skipped: %s", type(exc).__name__)
        return ""

    if getattr(chart, "status", "") != "CALCULATED":
        return ""

    lines = [CHART_HEADER, *_format_chart(chart), *_format_dasha(payload)]
    return "\n".join(lines)
