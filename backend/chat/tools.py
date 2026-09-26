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

# Used whenever Ask is asked to derive astrology for a person or birth date.
# The language model is never allowed to do that calculation.
DATE_GUARD_COPY = (
    "I can explain astrology concepts and anything from your chart, but I won't "
    "guess planetary placements from a date alone. KAVACH Kundli calculates those "
    "details properly."
)

# --- structural pre-provider detection ---------------------------------------
# Ask must never derive astrology for a person or a specific birth date from the
# model's own knowledge. Detection runs on EVERY message, independent of the
# sticky tool intent, before any provider call.

_ASTRO_TERMS = re.compile(
    r"\b(astrolog\w*|horoscope|zodiac|sun\s+sign|moon\s+sign|rising\s+sign"
    r"|ascendant|lagna|rashi|nakshatra|graha|dosha|manglik|kundli|janam\s*patri"
    r"|birth\s+chart|planet\w*|dasha|mahadasha|antardasha|pratyantardasha"
    r"|sookshma|prana|navtara|tithi|panchang|gochar|transit)\b",
    re.I,
)
_SIGNS = (r"aries|taurus|gemini|cancer|leo|virgo|libra|scorpio|sagittarius"
          r"|capricorn|aquarius|pisces")
_SIGNS_RE = re.compile(rf"\b(?:{_SIGNS})\b", re.I)
_PLANETS = (r"sun|moon|mercury|venus|mars|jupiter|saturn|rahu|ketu"
            r"|uranus|neptune|pluto")
_PLANETS_RE = re.compile(rf"\b(?:{_PLANETS})\b", re.I)
_CONCEPT_RE = re.compile(rf"\b(?:{_PLANETS}|{_SIGNS}|nakshatra|rashi|house"
                         r"|planet\w*|dasha|navtara|ascendant|lagna)\b", re.I)
_PERSONAL_ASTROLOGY = re.compile(
    r"\b(?:my|mine|our)\s+(?:kundli|birth\s*chart|chart|horoscope|planet\w*"
    r"|sun\s+sign|moon\s+sign|ascendant|lagna|rashi|nakshatra|dasha\w*"
    r"|mahadasha|antardasha|pratyantardasha|sookshma|prana|navtara"
    r"|janam\s*patri|placements?|houses?)\b",
    re.I,
)
_BIRTH_WORDS = re.compile(r"\b(born|birth|birthday|dob|d\.o\.b|date\s+of\s+birth|nativity)\b", re.I)
_DATE = re.compile(
    r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b"
    r"|\b\d{4}-\d{1,2}-\d{1,2}\b"
    r"|\b\d{1,2}(?:st|nd|rd|th)?\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?,?\s+\d{2,4}\b"
    r"|\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{2,4}\b"
    r"|\b(?:19|20)\d{2}\b",
    re.I,
)
_PERSONAL_INTENT = re.compile(r"\bmy\b|\bme\b|\bmine\b|\bmyself\b|personality|about\s+myself|about\s+me\b", re.I)
_GENERIC_ASK = re.compile(
    r"\b(?:tell\s+me\s+about|what\s+can\s+(?:you|u)\s+tell|tell\s+me\s+something"
    r"|describe|what\s+do\s+you\s+know\s+about)\b",
    re.I,
)
# Ordinary date questions that are never astrology.
_NON_ASTRO_EXEMPT = re.compile(
    r"\b(?:day\s+of\s+the\s+week|what\s+day|which\s+day|how\s+old|age\b|years\s+old"
    r"|in\s+words|in\s+numbers|convert|format|history|historical|world"
    r"|happened|weather|movie|film|song|lyrics|news|president|capital|population"
    r"|currency|died|passed\s+away|what\s+year|write|poem|essay|story|letter"
    r"|message|email|translate|summari[sz]e|spell|synonym|vocabulary)\b",
    re.I,
)
_INTERPRET = re.compile(
    r"\b(?:mean|means|meaning|explain|represent|represents|signify|signifies"
    r"|generally|traditionally|in\s+general|what\s+does|what\s+is|what\s+are)\b",
    re.I,
)
_SUPPLIED = re.compile(
    r"\b(?:says|says\s+that|shows|showed|tells\s+me|according\s+to|reports"
    r"|indicates|my\s+kundli|my\s+chart|my\s+reading)\b",
    re.I,
)
_FIRST_PERSON = re.compile(r"\bmy\b|\bme\b|\bmine\b|\bmyself\b", re.I)
_ASTRO_CONTEXT_TOOLS = ("kundli", "dasha", "navtara", "daily", "matchmaking",
                        "panchang", "life_summary", "yes_no")


def guard_for_tool(tool: str) -> Dict[str, Any]:
    """Controlled response + action for a blocked personal-calculation request."""
    if tool in ("dasha", "navtara"):
        return {"answer": TOOL_COPY[tool], "tool_action": _action(tool)}
    return {"answer": DATE_GUARD_COPY, "tool_action": _action("kundli")}


def is_interpretation_allowed(text: str) -> bool:
    """True for a concept question or an explicitly user-supplied placement.

    This is the only case where Ask may discuss a placement: a general/concept
    question, or a fact the user (or KAVACH) already supplied and asked to
    interpret. Ask must never establish the fact itself.
    """
    if not _INTERPRET.search(text):
        return False
    if not (_CONCEPT_RE.search(text) or _ASTRO_TERMS.search(text)):
        return False
    if _SUPPLIED.search(text):
        return True
    return not _FIRST_PERSON.search(text)


def personal_astrology_tool(question: str, context_tool: Optional[str] = None) -> Optional[str]:
    """Return a dedicated tool when a message requires deriving personal astrology.

    Independent of sticky intent: this runs on every message and recognises a
    birth/date reference combined with astrology or personal intent, personal
    chart phrasing, and Dasha/Navtara requests.
    """
    text = (question or "").strip().lower()
    if not text:
        return None
    if is_interpretation_allowed(text):
        return None

    if re.search(r"\b(?:my|mine|our)\b.*\b(?:mahadasha|antardasha|pratyantardasha|sookshma|prana)\b"
                 r"|\b(?:mahadasha|antardasha|pratyantardasha|sookshma|prana)\b.*\b(?:am i|i am|running|current)\b",
                 text):
        return "dasha"
    if re.search(r"\b(?:my|mine|our)\b.*\bnavtara\b|\bnavtara\b.*\b(?:am i|i am|my)\b", text):
        return "navtara"

    if _PERSONAL_ASTROLOGY.search(text):
        return "kundli"

    if _DATE.search(text) or _BIRTH_WORDS.search(text):
        exempt = bool(_NON_ASTRO_EXEMPT.search(text))
        astro = bool(_ASTRO_TERMS.search(text) or _CONCEPT_RE.search(text))
        personal = bool(_PERSONAL_INTENT.search(text))
        context_astro = context_tool in _ASTRO_CONTEXT_TOOLS and not exempt
        if astro or (personal and not exempt) or context_astro:
            return "kundli"
        # A bare date with a generic "tell me about" is treated as astrology in
        # this product unless it is clearly an ordinary date question.
        if _GENERIC_ASK.search(text) and not exempt:
            return "kundli"

    return None


def claims_derived_personal_placements(text: str) -> bool:
    """Post-provider failsafe: does this answer assert a personal placement?

    Secondary protection only. The primary protection is the pre-provider gate.
    """
    lowered = (text or "").lower()
    if not lowered:
        return False
    if re.search(r"\b(?:tropical|western|standard)\s+astrology\b", lowered):
        return True
    for sentence in re.split(r"(?<=[.!?])\s+|\n+", lowered):
        if _PLANETS_RE.search(sentence) and _SIGNS_RE.search(sentence) and re.search(
            r"\b(?:your|you|born|chart|horoscope|nativity|nakshatra)\b", sentence
        ):
            return True
        if re.search(rf"\b(?:your|the)\s+(?:{_PLANETS})\s+(?:sign\s+is|is|was|falls|sits|lies)\b",
                     sentence) and _SIGNS_RE.search(sentence):
            return True
    return False


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
