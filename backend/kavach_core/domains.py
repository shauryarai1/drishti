"""Structured domain tags for relevance filtering.

Concepts carry domains BEFORE prose generation. A concept may only reach the
composer when its life area intersects the question's allowed domains.
This is structured filtering, not string matching on sentences.
"""

from __future__ import annotations

from typing import Dict, Set

# Life areas a Bhava speaks about.
HOUSE_DOMAINS: Dict[int, Set[str]] = {
    1: {"self", "energy", "identity"},
    2: {"money", "family", "resources", "communication"},
    3: {"communication", "effort", "initiative", "learning"},
    4: {"home", "family", "emotion"},
    5: {"learning", "creativity"},
    6: {"obstacle", "service", "effort", "discipline"},
    7: {"relationship", "partnership", "social", "agreement"},
    8: {"change", "obstacle", "inner"},
    9: {"learning", "belief", "fortune"},
    10: {"career", "social", "discipline"},
    11: {"gains", "money", "social", "network"},
    12: {"release", "inner", "foreign", "expense"},
}

# General function of each KAVACH channel.
CHANNEL_DOMAINS: Dict[str, Set[str]] = {
    "vaar": {"self", "energy", "discipline"},
    "tithi": {"prosperity", "relationship"},
    "karana": {"career", "decision"},
    "nakshatra": {"inner", "emotion"},
    "yoga": {"obstacle", "support"},
}

# Allowed domains per question intent.
PERIOD_DOMAINS: Set[str] = {
    "self", "energy", "emotion", "inner", "obstacle", "support",
    "decision", "timing", "creativity", "discipline",
}

INTENT_DOMAINS: Dict[str, Set[str]] = {
    "period": PERIOD_DOMAINS,
    "general": PERIOD_DOMAINS,
    "decision": {"decision", "timing", "obstacle", "support", "discipline",
                 "inner", "energy", "self", "effort"},
    "outcome": {"career", "decision", "communication", "social", "obstacle",
                "support", "discipline", "effort", "self", "timing"},
    "career": {"career", "decision", "communication", "social", "obstacle",
               "support", "discipline", "effort", "self"},
    "money": {"money", "prosperity", "resources", "gains", "career", "decision",
              "obstacle", "support", "timing", "discipline"},
    "relationship": {"relationship", "partnership", "emotion", "inner", "social",
                     "support", "obstacle"},
    "home": {"home", "family", "emotion", "support", "obstacle", "resources"},
    "education": {"learning", "effort", "decision", "obstacle", "support", "self"},
}

# Channel-level general reading, used when every placement concept is filtered out.
GENERAL_CHANNEL_TEXT: Dict[str, str] = {
    "vaar": "Your own energy and approach set the tone in this period.",
    "tithi": "The emphasis falls on how you handle comfort, resources and dealings with people.",
    "karana": "This is best read as guidance for decisions and how you act on them.",
    "nakshatra": "The deeper pattern here concerns your inner habits and reactions.",
    "yoga": "The useful question is where support and caution may come from.",
}

GENERAL_CHANNEL_GUIDANCE: Dict[str, str] = {
    "vaar": "keep your reactions steady and avoid rushing",
    "tithi": "keep dealings balanced and unhurried",
    "karana": "decide deliberately rather than on impulse",
    "nakshatra": "notice the habit before reacting from it",
    "yoga": "leave room for plans to change",
}


def house_allowed(house: int, allowed: Set[str]) -> bool:
    return bool(HOUSE_DOMAINS.get(house, set()) & allowed)


def concept_allowed(house: int, channel: str, allowed: Set[str]) -> bool:
    """A concept may be used only if its life area is relevant to the question."""
    if not allowed:
        return True
    if house_allowed(house, allowed):
        return True
    # Otherwise the channel's general function must be explicitly allowed.
    return bool(CHANNEL_DOMAINS.get(channel, set()) & allowed)
