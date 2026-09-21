"""Centralised KAVACH Daily Prediction content (configurable astrology content).

ONE editable structure for the 12 active-house patterns. The calculation code
never hardcodes wording, and nothing here uses the Ascendant.
"""

from __future__ import annotations

from typing import Dict, Tuple

GOOD = "GOOD"
NEUTRAL = "NEUTRAL"
CAUTION = "CAUTION"

# theme (short label) + pattern (2-4 sentences) + category status with reason.
HOUSE_PATTERNS: Dict[int, Dict[str, object]] = {
    1: {
        "theme": "Self, mood and personal needs",
        "pattern": (
            "Your attention settles on yourself today: your mood, your body and what you personally need. "
            "Plans that are about you rather than about others may move forward more easily. "
            "It is a good day to notice how you actually feel before deciding anything for someone else."
        ),
        "love": (NEUTRAL, "You may be more aware of your own needs than of your partner's."),
        "health": (GOOD, "Energy is directed toward your own wellbeing and appearance."),
        "career": (NEUTRAL, "Personal priorities may compete with work demands."),
    },
    2: {
        "theme": "Food, money, family and security",
        "pattern": (
            "Money, food, possessions and family matters take the foreground today. "
            "Things you value and the sense of security behind them may need attention. "
            "Speech carries more weight than usual, so what you say about resources and family tends to linger."
        ),
        "love": (NEUTRAL, "Family and comfort matter, and practical support counts as affection."),
        "health": (CAUTION, "Food and eating habits deserve more attention than usual."),
        "career": (GOOD, "Financial and resource-related work moves well."),
    },
    3: {
        "theme": "Communication, messages and short travel",
        "pattern": (
            "Messages, conversations and short journeys shape the day. "
            "Communication and self-effort are highlighted, and skills you have practised may get used. "
            "Siblings and neighbours may feature more than usual."
        ),
        "love": (NEUTRAL, "Conversation keeps the connection moving."),
        "health": (GOOD, "Restlessness is easily channelled into movement."),
        "career": (GOOD, "Communication and quick, practical tasks go well."),
    },
    4: {
        "theme": "Home, comfort and emotional peace",
        "pattern": (
            "Home, comfort and emotional steadiness are the centre of the day. "
            "You may prefer familiar surroundings and quieter company. "
            "Rest and the state of your immediate environment affect how the rest of the day feels."
        ),
        "love": (GOOD, "Warmth at home supports closeness."),
        "health": (GOOD, "Rest and comfort support recovery."),
        "career": (NEUTRAL, "Work may feel secondary to domestic matters."),
    },
    5: {
        "theme": "Creativity, enjoyment and romance",
        "pattern": (
            "Creativity, enjoyment and matters of the heart are highlighted. "
            "Children, hobbies, study or entertainment may draw your attention. "
            "Ideas come more easily, and there is a pull toward doing something you actually enjoy."
        ),
        "love": (GOOD, "Romance and affection are supported."),
        "health": (GOOD, "Enjoyment lifts energy."),
        "career": (NEUTRAL, "Creative work helps; routine duties may feel slow."),
    },
    6: {
        "theme": "Work, routine and pending tasks",
        "pattern": (
            "Work, routine, obligations and pending tasks dominate the day. "
            "Obstacles and competition may need managing rather than avoiding. "
            "It is a practical day: clearing obligations brings more relief than starting something new."
        ),
        "love": (CAUTION, "Work pressure can crowd out attention for a partner."),
        "health": (CAUTION, "Routine strain and overdoing things are worth watching."),
        "career": (GOOD, "Focused effort on tasks and obligations pays off."),
    },
    7: {
        "theme": "Relationships, partner and agreements",
        "pattern": (
            "Other people are central today: partners, clients, meetings and agreements. "
            "One-to-one interaction carries more weight than solitary effort. "
            "How you negotiate and cooperate shapes how the day goes."
        ),
        "love": (GOOD, "Partnership and one-to-one attention are highlighted."),
        "health": (NEUTRAL, "Wellbeing depends on balance with others."),
        "career": (GOOD, "Meetings, clients and agreements are favoured."),
    },
    8: {
        "theme": "Hidden matters, uncertainty and change",
        "pattern": (
            "Hidden matters, shared resources and unresolved issues may surface. "
            "Unexpected changes can appear, and not everything will be visible at once. "
            "It is a day for care and research rather than quick conclusions."
        ),
        "love": (CAUTION, "Unspoken matters may need patience rather than pressure."),
        "health": (CAUTION, "Uncertainty can be draining; pace yourself."),
        "career": (NEUTRAL, "Research and careful handling suit this day better than bold moves."),
    },
    9: {
        "theme": "Learning, beliefs and direction",
        "pattern": (
            "Your attention may move toward learning, guidance and the bigger picture. "
            "Teachers, beliefs, higher study or long-distance matters may occupy more of your mind. "
            "Perspective is easier to find than detail today."
        ),
        "love": (NEUTRAL, "Shared values matter more than daily details."),
        "health": (GOOD, "Perspective supports emotional balance."),
        "career": (GOOD, "Planning, learning and long-term direction are favoured."),
    },
    10: {
        "theme": "Career, responsibility and achievement",
        "pattern": (
            "Your attention is naturally directed toward work, responsibility and getting results. "
            "Achievement, authority and reputation are more visible today. "
            "It is a day when duties are hard to postpone and progress is measurable."
        ),
        "love": (NEUTRAL, "Work focus may leave less room for personal attention."),
        "health": (NEUTRAL, "Steady effort is fine; overwork is not."),
        "career": (GOOD, "Your attention is oriented toward results and responsibility."),
    },
    11: {
        "theme": "Friends, networks and gains",
        "pattern": (
            "Friends, groups and networks are highlighted today. "
            "Opportunities, gains and shared aspirations may move forward through other people. "
            "It is a social day where cooperation opens doors."
        ),
        "love": (NEUTRAL, "Social life is active; private time may be shorter."),
        "health": (GOOD, "Company and shared activity lift energy."),
        "career": (GOOD, "Networks and opportunities are favoured."),
    },
    12: {
        "theme": "Rest, privacy and release",
        "pattern": (
            "Rest, privacy and quiet matter more today than visibility. "
            "Expenses, remote or foreign matters and unfinished business may occupy the background. "
            "Withdrawal is useful here rather than a problem to fix."
        ),
        "love": (CAUTION, "You may need space rather than closeness today."),
        "health": (CAUTION, "Rest and sleep deserve real priority."),
        "career": (NEUTRAL, "Behind-the-scenes work suits the day better than public effort."),
    },
}

# DEPRECATED (not used, not exposed): one transit-lord colour for everybody was
# wrong for a personalised daily colour.
LEGACY_COLOUR_BY_LORD: Dict[str, str] = {
    "Sun": "Gold / Warm Orange",
    "Moon": "White / Silver",
    "Mars": "Red",
    "Mercury": "Green",
    "Jupiter": "Yellow",
    "Venus": "White / Soft Pink",
    "Saturn": "Deep Blue / Indigo",
    "Rahu": "Smoke Grey",
    "Ketu": "Earthy Brown",
}


def status(active_house: int, category: str) -> Tuple[str, str]:
    entry = HOUSE_PATTERNS.get(active_house) or HOUSE_PATTERNS[1]
    level, reason = entry[category]  # type: ignore[misc]
    return str(level), str(reason)


# ---------------------------------------------------------------------------
# PERSONALISED DAILY COLOUR MATRIX  (12 natal Moon signs x 12 Daily Moon rashis)
#
# The approved KAVACH colour methodology has NOT been supplied yet, so this
# matrix is intentionally EMPTY (all None). It is ONE editable structure: fill
# a value and that person/day immediately gets a Best Colour.
#
# Do not invent values here. Do not use the transit Moon lord alone. Do not use
# fixed natal-sign colours as a stand-in for a daily colour.
# ---------------------------------------------------------------------------
_RASHIS = ("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
           "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")

DAILY_COLOUR_MATRIX: Dict[str, Dict[str, str | None]] = {
    natal: {daily: None for daily in _RASHIS} for natal in _RASHIS
}


def colour_for(natal_moon_sign: str | None, daily_moon_rashi: str | None) -> str | None:
    """Best Colour for TODAY. Returns None while the matrix is pending."""
    if not natal_moon_sign or not daily_moon_rashi:
        return None
    row = DAILY_COLOUR_MATRIX.get(natal_moon_sign) or {}
    value = row.get(daily_moon_rashi)
    return value or None
