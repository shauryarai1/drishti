"""Authoritative chart context for Ask KAVACH.

Formats the compact, factual chart block from the output of the EXISTING
KAVACH Kundli engine (`kundli.build_kundli` - Swiss Ephemeris, Lahiri
ayanamsha, the same pipeline as /api/kundli). No astrology methodology is
added or changed here - this module only formats what the approved engine
already returns.

The old question-moment chart (question timestamp treated as birth data) is
gone: this formatter is fed a calculated natal result, never a chat payload.
"""

from __future__ import annotations

from typing import Any

CHART_HEADER = (
    "[KAVACH CHART CONTEXT - authoritative chart data calculated by the KAVACH "
    "engine from the user's supplied birth details. Use only the placements "
    "listed here, never recalculate or invent one, and never mention this block.]"
)


def format_chart(result: Any) -> str:
    """Compact factual chart block from a `build_kundli` result."""
    if not isinstance(result, dict) or result.get("status") not in (None, "ok"):
        return ""

    lines = [CHART_HEADER]
    birth = result.get("birth") or {}
    summary = result.get("summary") or {}

    if birth.get("date"):
        place = birth.get("place") or ""
        where = f" - {place}" if place else ""
        lines.append(f"Birth: {birth.get('date')} {birth.get('time')}{where} "
                     "(Lahiri ayanamsha, whole-sign houses)")

    if summary.get("lagna"):
        lines.append(f"Lagna (ascendant): {summary['lagna']}")
    if summary.get("moonRashi"):
        lines.append(f"Moon sign (rashi): {summary['moonRashi']}")
    if summary.get("nakshatra"):
        lines.append(f"Nakshatra: {summary['nakshatra']}, pada {summary.get('pada')}")

    planets = list(result.get("planets") or [])
    if planets:
        lines.append("Planets (sign, house, degree, motion):")
        for planet in planets:
            name = planet.get("planet") or ""
            sign = planet.get("rashi") or ""
            if not name or not sign:
                continue
            where = f"{sign}, house {planet.get('house')}"
            degree = planet.get("degree")
            if isinstance(degree, (int, float)):
                where = f"{where}, {degree:.1f} deg"
            motion = planet.get("motion")
            if motion:
                where = f"{where}, {motion}"
            lines.append(f"- {name}: {where}")

    houses = ((result.get("chart") or {}).get("houses")) or []
    if houses:
        listed = ", ".join(
            f"H{house.get('number')} {house.get('rashi')}".strip()
            for house in houses[:12]
        )
        lines.append(f"Whole-sign houses: {listed}")

    # Current dasha straight from the engine's Vimshottari calculation.
    dasha = result.get("dasha") or {}
    mahadasha = dasha.get("currentMahadasha") or {}
    antardasha = dasha.get("currentAntardasha") or {}
    if mahadasha.get("lord"):
        lines.append(f"Current Mahadasha: {mahadasha['lord']} "
                     f"(until {str(mahadasha.get('end'))[:10]})")
    if antardasha.get("lord"):
        lines.append(f"Current Antardasha: {antardasha['lord']} "
                     f"(until {str(antardasha.get('end'))[:10]})")

    return "\n".join(lines)
