"""Allowlisted KAVACH tool recommendations for Ask KAVACH.

Ask remains a conversational assistant. This module only handles requests
whose answer requires a dedicated deterministic KAVACH product. It never
calculates a chart, Dasha, compatibility result or daily result itself.

The returned route is selected from this registry, never from model output.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional

TOOL_REGISTRY: Dict[str, Dict[str, str]] = {
    "kundli": {"label": "Open Kundli", "href": "/kundli"},
    "dasha": {"label": "Open Kundli - Dasha", "href": "/kundli"},
    "navtara": {"label": "Open Kundli - Navtara", "href": "/kundli"},
    "daily": {"label": "Open Daily", "href": "/daily"},
    "matchmaking": {"label": "Open Matchmaking", "href": "/compatibility"},
    "yes_no": {"label": "Open Yes / No", "href": "/yes-no"},
    "panchang": {"label": "Open Panchang", "href": "/panchang"},
    "life_summary": {"label": "Open Life Summary", "href": "/life-summary"},
}

KUNDLI_ANSWER = (
    "For a complete chart analysis, KAVACH Kundli is the better tool. It "
    "shows your planetary placements, houses, Nakshatras, Dashas and other "
    "chart details."
)

TOOL_COPY = {
    "dasha": "Your current Dasha needs the dedicated Kundli calculation. KAVACH Kundli has the full Vimshottari Dasha section.",
    "navtara": "Your personal Navtara needs the dedicated Kundli calculation. KAVACH Kundli has the full Navtara section.",
    "daily": "A dedicated KAVACH Daily reading is the right place for a calculated prediction for today.",
    "matchmaking": "KAVACH Matchmaking is the better tool for a calculated compatibility analysis.",
    "yes_no": "KAVACH Yes / No is the dedicated tool for a focused yes-or-no reading.",
    "panchang": "KAVACH Panchang is the right tool for today's Tithi, Nakshatra, Yoga and Karana.",
    "life_summary": "KAVACH Life Summary is the dedicated experience for an overall life reading.",
}

FOLLOWUP_COPY = {
    "kundli": "I can explain astrology concepts and help you think through something here, but I won't guess your personal chart from a birth date - KAVACH Kundli calculates that properly. Open your Kundli first, then ask me about anything you see there.",
    "dasha": "I can explain what Dasha periods mean, but I won't guess your personal Dasha. Open Kundli to calculate it properly, then ask me about the result.",
    "navtara": "I can explain Navtara concepts, but I won't guess your personal cycle. Open Kundli to calculate your Navtara properly, then ask me about the result.",
}


def _action(tool: str) -> Dict[str, Any]:
    entry = TOOL_REGISTRY[tool]
    return {"tool": tool, "label": entry["label"], "href": entry["href"]}


def _personal(text: str, pattern: str) -> bool:
    return re.search(pattern, text, re.I) is not None


def tool_action_for(question: str) -> Optional[Dict[str, Any]]:
    """Return a deterministic action only for a personal dedicated-tool request."""
    text = (question or "").strip().lower()
    if not text:
        return None

    # Educational questions stay in Ask. Personal chart placement/reading
    # wording is the boundary that recommends Kundli.
    if _personal(text, r"\b(?:my|make my|read my|tell me about my)\s+(?:kundli|birth chart|chart)\b") \
            or _personal(text, r"\b(?:where is|what is|show me)\s+(?:my\s+)?(?:saturn|jupiter|mars|mercury|venus|sun|moon|rahu|ketu|ascendant|lagna)\s+(?:in my chart|in my kundli|doing)\b") \
            or _personal(text, r"\bwhat (?:is|are) my (?:\d+(?:st|nd|rd|th)\s+house|planets?|nakshatra|rashi|lagna|ascendant)\b") \
            or _personal(text, r"\bwhat planets? are in my (?:\d+(?:st|nd|rd|th)\s+house|chart|kundli)\b"):
        return {"answer": KUNDLI_ANSWER, "tool_action": _action("kundli")}

    if _personal(text, r"\bwhat (?:mahadasha|antardasha|pratyantardasha|sookshma|prana) am i (?:running|in)\b") \
            or _personal(text, r"\bshow my (?:mahadasha|antardasha|pratyantardasha|sookshma|prana)\b"):
        return {"answer": TOOL_COPY["dasha"], "tool_action": _action("dasha")}

    if _personal(text, r"\bwhat is my navtara\b|\bshow my .*\b(?:janma|sampat|vipat)\b"):
        return {"answer": TOOL_COPY["navtara"], "tool_action": _action("navtara")}

    if _personal(text, r"\b(?:how is|what is|what's) today(?:'s)? prediction for [a-z]+\b") \
            or _personal(text, r"\bhow is today for my moon sign\b"):
        return {"answer": TOOL_COPY["daily"], "tool_action": _action("daily")}

    if _personal(text, r"\b(?:compatible astrologically|match our charts|marriage compatibility|compatibility of (?:us|our))\b"):
        return {"answer": TOOL_COPY["matchmaking"], "tool_action": _action("matchmaking")}

    if _personal(text, r"\b(?:give me|do) (?:a )?yes(?:[ /-]?or)?[ /-]?no (?:reading|answer)\b"):
        return {"answer": TOOL_COPY["yes_no"], "tool_action": _action("yes_no")}

    if _personal(text, r"\b(?:panchang today|today's panchang|tithi.*nakshatra.*yoga|nakshatra.*tithi.*yoga)\b"):
        return {"answer": TOOL_COPY["panchang"], "tool_action": _action("panchang")}

    if _personal(text, r"\b(?:give me|show me) my overall life reading\b"):
        return {"answer": TOOL_COPY["life_summary"], "tool_action": _action("life_summary")}

    return None


def followup_tool_action_for(question: str, tool: str) -> Optional[Dict[str, Any]]:
    """Preserve a specialized-tool boundary across ambiguous follow-ups.

    Returns ``{"clear": True}`` when the user clearly changed topic. A
    normal ``None`` means the caller should clear the specialized context and
    let ordinary conversation proceed.
    """
    text = (question or "").strip().lower()
    if not text or tool not in TOOL_REGISTRY:
        return None

    educational = re.search(
        r"\b(generally|in astrology|as a concept|conceptually)\b"
        r"|^what is (?:an? )?(?:saturn|jupiter|mars|mercury|venus|sun|moon|"
        r"ascendant|lagna|mahadasha|antardasha|navtara)\b",
        text,
    )
    if educational:
        return {"clear": True}

    topic_change = re.search(r"\b(?:anyway|instead)\b", text) or re.search(
        r"\b(gravity|photosynthesis|code|coding|email|recipe)\b", text)
    if topic_change and not re.search(r"\b(?:chart|kundli|dasha|navtara|planet|saturn|jupiter)\b", text):
        return {"clear": True}

    ambiguous = re.search(
        r"^(?:so\s+)?(?:what can (?:you|u) tell me|tell me more|anything else|why|how|then|explain)\b"
        r"|\bwhat about\b|\bwhat does that mean\b|\bwhat does .* mean for me\b",
        text,
    )
    if not ambiguous and re.search(
        r"^and\s+(?:saturn|jupiter|mars|mercury|venus|sun|moon|rahu|ketu)\b",
        text,
    ):
        ambiguous = True
    if not ambiguous:
        return None

    return {
        "answer": FOLLOWUP_COPY.get(tool, FOLLOWUP_COPY["kundli"]),
        "tool_action": _action(tool),
    }


def is_allowed_action(action: Any) -> bool:
    """Validate an action before it crosses the public response boundary."""
    return (
        isinstance(action, dict)
        and action.get("tool") in TOOL_REGISTRY
        and action.get("href") == TOOL_REGISTRY[action["tool"]]["href"]
    )
