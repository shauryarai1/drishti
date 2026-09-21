"""AUTHORITATIVE Panchang lord mappings (single source of truth).

Consumed by System A (birth moment) and System B (question moment) through
jyotish.lords. These are the astrologer's KAVACH rules, NOT generic
assumptions. Edit here only.

The five Panchang channel meanings and the Daily Moon 6/8/12 rule are KAVACH
custom rules (see question_engine/knowledge/kavach_custom.py).

source_type = kavach_custom
source      = kavach_astrologer_rule
status      = approved
"""

from __future__ import annotations

from typing import Dict, List

MAPPING_PROVENANCE: Dict[str, str] = {
    "source_type": "kavach_custom",
    "source": "kavach_astrologer_rule",
    "status": "approved",
}

# --- 1. Vaar (weekday, Monday=0 .. Sunday=6) -------------------------------
VAAR_LORDS: Dict[int, str] = {
    0: "Moon",     # Monday
    1: "Mars",     # Tuesday
    2: "Mercury",  # Wednesday
    3: "Jupiter",  # Thursday
    4: "Venus",    # Friday
    5: "Saturn",   # Saturday
    6: "Sun",      # Sunday
}

# --- 2. Tithi, by number within paksha (1..15) ----------------------------
# Paksha is preserved; no separate Shukla/Krishna lord rules.
TITHI_LORDS: Dict[int, str] = {
    1: "Sun", 2: "Moon", 3: "Mars", 4: "Mercury", 5: "Jupiter",
    6: "Venus", 7: "Saturn", 8: "Rahu", 9: "Sun", 10: "Moon",
    11: "Mars", 12: "Mercury", 13: "Jupiter", 14: "Venus",
    15: "Saturn",  # Purnima (Shukla) and Amavasya (Krishna) both -> Saturn
}

# --- 3. Karana ------------------------------------------------------------
KARANA_LORDS: Dict[str, str] = {
    "Bava": "Sun",
    "Balava": "Moon",
    "Kaulava": "Mars",
    "Taitila": "Mercury",
    "Garaja": "Jupiter",
    "Vanija": "Venus",
    "Vishti": "Saturn",
    "Bhadra": "Saturn",
    "Shakuni": "Rahu",
    "Chatushpada": "Ketu",
    "Naga": "Rahu",
    "Kimstughna": "Ketu",
}

# --- 4. Nakshatra ---------------------------------------------------------
NAKSHATRA_LORDS: Dict[str, List[str]] = {
    "Ketu": ["Ashvini", "Magha", "Mula"],
    "Venus": ["Bharani", "Purva Phalguni", "Purva Ashadha"],
    "Sun": ["Krittika", "Uttara Phalguni", "Uttara Ashadha"],
    "Moon": ["Rohini", "Hasta", "Shravana"],
    "Mars": ["Mrigashira", "Chitra", "Dhanishta"],
    "Rahu": ["Ardra", "Swati", "Shatabhisha"],
    "Jupiter": ["Punarvasu", "Vishakha", "Purva Bhadrapada"],
    "Saturn": ["Pushya", "Anuradha", "Uttara Bhadrapada"],
    "Mercury": ["Ashlesha", "Jyeshtha", "Revati"],
}

# --- 5. Yoga, by classic order 1..27 -------------------------------------
YOGA_LORDS: Dict[int, str] = {
    1: "Ketu", 2: "Venus", 3: "Sun", 4: "Moon", 5: "Mars",
    6: "Rahu", 7: "Jupiter", 8: "Saturn", 9: "Mercury",
    10: "Ketu", 11: "Venus", 12: "Sun", 13: "Moon", 14: "Mars",
    15: "Rahu", 16: "Jupiter", 17: "Saturn", 18: "Mercury",
    19: "Ketu", 20: "Venus", 21: "Sun", 22: "Moon", 23: "Mars",
    24: "Rahu", 25: "Jupiter", 26: "Saturn", 27: "Mercury",
}

# --- Interpretation domains per channel (KAVACH custom, not per planet) ---
LIMB_PURPOSES: Dict[str, List[str]] = {
    "vaar": ["life_force", "vitality", "personality"],
    "tithi": ["marital_bliss", "relationship_wellbeing", "prosperity"],
    "karana": ["professional_success", "career_behaviour", "decision_making", "acting_on_opportunities"],
    "nakshatra": ["subconscious_patterns", "instinctive_reactions", "past_habit_tendencies"],
    "yoga": ["protection", "overcoming_obstacles", "support_in_difficulty", "handling_resistance"],
}

PANCHANG_LORD_MAPPINGS: Dict[str, object] = {
    "vara": VAAR_LORDS,
    "tithi": TITHI_LORDS,
    "karana": KARANA_LORDS,
    "nakshatra": NAKSHATRA_LORDS,
    "yoga": YOGA_LORDS,
}
