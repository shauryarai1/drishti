"""Deterministic prose renderer for Life Summary (no LLM available in this project).

The approved curated sentence is always used verbatim as the opening; this
module adds the approved strengths, cautions and guidance around it so each
card reads as a short paragraph rather than a single line.

The astrology is already decided: the Panchang lord and its approved curated
entry. This module ONLY expresses those approved facts in natural language.

It may not invent astrology: no planets, houses, signs, aspects, dashas,
predictions, remedies or traits beyond the supplied entry.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

CATEGORY_ORDER = ["personality", "relationships", "professional", "subconscious", "problems"]

STRENGTH_CONNECTORS = (
    "This tends to show itself as {items}.",
    "It usually comes out as {items}.",
    "People who know you well would describe this as {items}.",
    "In everyday terms this looks like {items}.",
)

WATCH_CONNECTORS = (
    "At the same time, the difficult side is {items}.",
    "The risk is {items}.",
    "This can tip into {items}.",
    "Left unmanaged, this becomes {items}.",
)


def _join(items: List[str]) -> str:
    items = [item.strip() for item in items if item]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f" and {items[-1]}"


def _seed(category: str, planet: Optional[str]) -> int:
    try:
        index = CATEGORY_ORDER.index(category)
    except ValueError:
        index = 0
    return (len(planet or "") * 7 + index * 3) % 4


def render(category: str, planet: Optional[str], entry: Dict[str, Any]) -> Optional[str]:
    summary = entry.get("summary")
    if not summary:
        return None

    seed = _seed(category, planet)
    parts: List[str] = [str(summary).strip()]

    strengths = list(entry.get("strengths") or [])[:3]
    watch = list(entry.get("watch_for") or [])[:2]
    guidance = entry.get("guidance")

    if strengths:
        parts.append(STRENGTH_CONNECTORS[seed].format(items=_join(strengths)))
    if watch:
        parts.append(WATCH_CONNECTORS[(seed + 1) % len(WATCH_CONNECTORS)].format(items=_join(watch)))
    if guidance:
        parts.append(str(guidance).strip())

    return " ".join(part for part in parts if part)


