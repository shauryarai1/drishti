"""Natal grounding for Ask KAVACH: calculated chart or birth details.

A personal chart question may be answered in exactly ONE of two ways:

    1. authoritative context from the EXISTING KAVACH Kundli engine
       (`kundli.build_kundli` - Swiss Ephemeris, Lahiri ayanamsha, the same
       pipeline as /api/kundli), or
    2. a deterministic reply asking for the birth details that are missing.

There is never a third path: the model is never allowed to invent, derive or
"calculate" a placement itself. Birth details are collected conversationally
across turns and cached per conversation; the calculated chart is reused for
follow-ups and recalculated only when a detail changes.

This module collects inputs and formats what the approved engine returns.
It never adds, changes or reinterprets astrology methodology, and it never
touches the hidden reading, providers or safety handling.
"""

from __future__ import annotations

import re
from datetime import date as _date, datetime
from typing import Any, Dict, List, Optional, Tuple

# Bound the natal states the same way conversation memory is bounded:
# conversation ids are client-supplied, so an unbounded dict would be a
# memory-exhaustion vector.
MAX_STATES = 2000

_STATES: Dict[str, Dict[str, Any]] = {}

SIGNS = ("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
         "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")
SIGNS_LOWER = frozenset(sign.lower() for sign in SIGNS)

# A personal, possessive chart question: the user asking about THEIR chart.
# General astrology ("What is Saturn?", "Explain retrograde") never matches,
# so it is still answered as ordinary conversation with no chart context.
_NATAL_PATTERN = re.compile(
    r"\bmy\s+(?:\d{4}\s+)?(?:kundli|birth\s+chart|chart|lagna|ascendant"
    r"|moon\s+sign|sun\s+sign|nakshatra|rashi|dasha|dashas|planets?|planetary"
    r"|placements?|houses?)\b"
    r"|\bin\s+my\s+(?:kundli|chart)\b"
    r"|\bas\s+per\s+my\s+(?:kundli|chart)\b"
    r"|\baccording\s+to\s+my\s+(?:kundli|chart)\b"
    r"|\bmy\s+\d{1,2}(?:st|nd|rd|th)\s+house\b"
    r"|\bwhich\s+house\s+is\s+\w+\s+in\b"
)

# --- deterministic replies ---------------------------------------------------
ALL_DETAILS_REPLY = (
    "Sure - I'll need your date of birth, birth time and birth place to "
    "calculate your chart. Send all three and I'll read it for you."
)
PLACE_AND_TIME_REPLY = (
    "Thanks. What time were you born, and where (city and country)?"
)
PLACE_REPLY = "Thanks. Where were you born? A city and country is enough."
TIME_REPLY = (
    "And what time were you born? Even an approximate time helps - the "
    "ascendant depends on it."
)
DETAILS_REPLY = (
    "I still need your date of birth, birth time and birth place to "
    "calculate your chart."
)
GEOCODER_BUSY_REPLY = (
    "Location search is temporarily unavailable. Please try again in a moment."
)
CALCULATION_FAILED_REPLY = (
    "I couldn't calculate your chart right now. Please try again in a moment."
)
CHART_FALLBACK_REPLY = (
    "I can only state what your calculated chart shows. Ask me about a "
    "specific placement and I'll answer it directly."
)


def needs_natal(question: str) -> bool:
    """True only for an explicit personal chart question."""
    text = (question or "").lower()
    if not text:
        return False
    return _NATAL_PATTERN.search(text) is not None


# --- parsing -----------------------------------------------------------------
_MONTHS = {
    "january": 1, "jan": 1, "february": 2, "feb": 2, "march": 3, "mar": 3,
    "april": 4, "apr": 4, "may": 5, "june": 6, "jun": 6, "july": 7, "jul": 7,
    "august": 8, "aug": 8, "september": 9, "sept": 9, "sep": 9,
    "october": 10, "oct": 10, "november": 11, "nov": 11, "december": 12,
    "dec": 12,
}
_MONTH_NAMES = ("January", "February", "March", "April", "May", "June", "July",
                "August", "September", "October", "November", "December")

_DATE_NUMERIC = re.compile(r"\b(\d{1,2})[./-](\d{1,2})[./-](\d{4})\b")
_DATE_ISO = re.compile(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b")
_DATE_DAY_MONTH = re.compile(
    r"\b(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]{3,9})\.?,?\s+(\d{4})\b")
_DATE_MONTH_DAY = re.compile(
    r"\b([A-Za-z]{3,9})\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})\b")

_TIME_12H = re.compile(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b", re.I)
_TIME_24H = re.compile(r"\b([01]?\d|2[0-3]):([0-5]\d)\b")

_DATE_FINDER = (_DATE_NUMERIC, _DATE_ISO, _DATE_DAY_MONTH, _DATE_MONTH_DAY)
_TIME_FINDER = (_TIME_12H, _TIME_24H)

# Words that mean the leftover text is a question or instruction, not a place.
_PLACE_STOPWORDS = {
    "what", "what's", "whats", "when", "where", "why", "how", "which", "who",
    "tell", "mean", "means", "meaning", "does", "did", "do", "is", "are",
    "was", "were", "sign", "signs", "house", "houses", "planet", "planets",
    "dasha", "dashas", "kundli", "chart", "horoscope", "please", "thanks",
    "hello", "about", "read", "give", "show", "calculate", "mine", "really",
    "okay", "ok", "yes", "no", "sure", "fine", "hi", "bye",
    # detail-collection filler, so only the place words survive
    "my", "me", "i", "am", "the", "a", "an", "and", "or", "to", "of", "at",
    "on", "in", "born", "birth", "date", "time", "dob", "tob", "was",
}

_PLACE_CUE = re.compile(
    r"(?:born\s+in|birth\s*place\s*[:=-]*|birthplace\s*[:=-]*|place\s*[:=]\s*"
    r"|city\s*[:=]\s*|from\s+)([A-Za-z][A-Za-z .,'&()-]{1,60})",
    re.I)


def _valid_date(year: int, month: int, day: int) -> Optional[str]:
    try:
        return _date(year, month, day).isoformat()
    except ValueError:
        return None


def parse_date(text: str) -> Optional[str]:
    """A full birth date found in the text, normalised to YYYY-MM-DD."""
    match = _DATE_NUMERIC.search(text or "")
    if match:
        first, second, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
        if first > 12 >= second:
            day, month = first, second
        elif second > 12 >= first:
            month, day = first, second
        else:
            day, month = first, second  # KAVACH is an Indian product: dd/mm/yyyy
        return _valid_date(year, month, day)

    match = _DATE_ISO.search(text or "")
    if match:
        return _valid_date(int(match.group(1)), int(match.group(2)),
                           int(match.group(3)))

    match = _DATE_DAY_MONTH.search(text or "")
    if match:
        month = _MONTHS.get(match.group(2).lower())
        if month:
            return _valid_date(int(match.group(3)), month, int(match.group(1)))

    match = _DATE_MONTH_DAY.search(text or "")
    if match:
        month = _MONTHS.get(match.group(1).lower())
        if month:
            return _valid_date(int(match.group(3)), month, int(match.group(2)))
    return None


def parse_time(text: str) -> Optional[str]:
    """A birth time found in the text, normalised to 24h HH:MM."""
    match = _TIME_12H.search(text or "")
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2) or 0)
        if not 1 <= hour <= 12 or minute > 59:
            return None
        meridiem = match.group(3).lower()
        if hour == 12:
            hour = 0
        if meridiem == "pm":
            hour += 12
        return f"{hour:02d}:{minute:02d}"

    match = _TIME_24H.search(text or "")
    if match:
        hour, minute = int(match.group(1)), int(match.group(2))
        if hour > 23 or minute > 59:
            return None
        return f"{hour:02d}:{minute:02d}"
    return None


def _strip_known(text: str) -> str:
    """Remove recognised dates and times so only the leftover words remain."""
    leftover = text
    for pattern in _DATE_FINDER + _TIME_FINDER:
        leftover = pattern.sub(" ", leftover)
    return leftover


def parse_place(text: str) -> Optional[str]:
    """The birth place, only extracted from a detail-shaped message.

    Place extraction is deliberately conservative: it never geocodes a whole
    question, so ordinary chat can never spend Geoapify quota.
    """
    leftover = _strip_known(text or "")
    if "?" in leftover:
        return None

    cue = _PLACE_CUE.search(leftover)
    if cue:
        candidate = cue.group(1)
    else:
        words = []
        for word in leftover.split():
            core = word.strip(",.;:!?\"'()")
            if not core or core.lower() in _PLACE_STOPWORDS or core.isdigit():
                continue
            words.append(core)
        candidate = " ".join(words)
        if not candidate or len(candidate.split()) > 4:
            return None
    candidate = candidate.strip(" ,.;:!?'\"")
    return candidate or None


def display_date(iso: str) -> str:
    """Human form of an ISO date for the deterministic confirmation reply."""
    try:
        parsed = datetime.strptime(iso, "%Y-%m-%d")
    except (TypeError, ValueError):
        return iso or ""
    return f"{parsed.day} {_MONTH_NAMES[parsed.month - 1]} {parsed.year}"


# --- state -------------------------------------------------------------------
def _new_state(pending: str = "") -> Dict[str, Any]:
    return {"date": None, "time": None, "place": None, "latitude": None,
            "longitude": None, "timezone": None, "pending": pending,
            "chart": None, "context": None, "fingerprint": None}


def _evict(keep: str) -> None:
    """Dicts preserve insertion order, so the first key is the oldest."""
    if len(_STATES) <= MAX_STATES:
        return
    for oldest in list(_STATES):
        if oldest != keep:
            _STATES.pop(oldest, None)
            return


def get_state(conversation_id: str) -> Optional[Dict[str, Any]]:
    return _STATES.get(conversation_id)


def seed(conversation_id: str, details: Dict[str, Any]) -> None:
    """Store COMPLETE birth details for a conversation (tests, owner fixtures)."""
    if not conversation_id:
        return
    state = _new_state()
    state["date"] = details.get("date") or None
    state["time"] = details.get("time") or None
    state["place"] = details.get("place") or None
    state["latitude"] = details.get("latitude")
    state["longitude"] = details.get("longitude")
    state["timezone"] = details.get("timezone") or "Asia/Kolkata"
    _STATES[conversation_id] = state
    _evict(conversation_id)


def reset(conversation_id: str) -> None:
    _STATES.pop(conversation_id, None)


def clear() -> None:
    _STATES.clear()


def _missing(state: Dict[str, Any]) -> List[str]:
    missing = []
    if not state.get("date"):
        missing.append("date")
    if not state.get("time"):
        missing.append("time")
    if state.get("latitude") is None or state.get("longitude") is None:
        missing.append("place")
    return missing


def _missing_reply(state: Dict[str, Any]) -> str:
    has_date = bool(state.get("date"))
    has_time = bool(state.get("time"))
    has_place = bool(state.get("place"))
    if not has_date:
        return DETAILS_REPLY if (has_time or has_place) else ALL_DETAILS_REPLY
    if not has_time and not has_place:
        return PLACE_AND_TIME_REPLY
    if not has_time:
        return TIME_REPLY
    if not has_place:
        return PLACE_REPLY
    return DETAILS_REPLY


def _resolve_place(state: Dict[str, Any]) -> str:
    """Geocode the collected birth place. Returns "" on success."""
    try:
        from geocoding import resolve_coordinates

        try:
            coordinates = resolve_coordinates(state["place"])
        except Exception as exc:
            if type(exc).__name__ in ("GeocoderRateLimited", "ProviderRateLimited"):
                return GEOCODER_BUSY_REPLY
            raise
    except Exception as exc:  # a geocoder hiccup must never break the flow
        import logging

        logging.getLogger("kavach.chat").warning(
            "Natal place resolution skipped: %s", type(exc).__name__)
        return GEOCODER_BUSY_REPLY
    if coordinates is None:
        return (f"I couldn't find '{state['place']}'. Share the city and country "
                "(or the nearest bigger city) once more.")
    latitude, longitude = coordinates
    state["latitude"], state["longitude"] = float(latitude), float(longitude)
    try:
        from calculator import timezone_for

        state["timezone"] = timezone_for(state["latitude"], state["longitude"]) or "Asia/Kolkata"
    except Exception:
        state["timezone"] = state.get("timezone") or "Asia/Kolkata"
    return ""


def _fingerprint(state: Dict[str, Any]) -> Tuple:
    return (state.get("date"), state.get("time"), state.get("latitude"),
            state.get("longitude"), state.get("timezone"))


def _context(state: Dict[str, Any]) -> Optional[str]:
    """Authoritative chart context from the existing Kundli engine, cached."""
    fingerprint = _fingerprint(state)
    if state.get("chart") is not None and state.get("fingerprint") == fingerprint:
        return state.get("context")
    try:
        from kundli import build_kundli
        from chat.astrology import format_chart

        result = build_kundli({
            "date": state.get("date"),
            "time": state.get("time"),
            "place": state.get("place") or "",
            "latitude": state.get("latitude"),
            "longitude": state.get("longitude"),
            "timezone": state.get("timezone") or "Asia/Kolkata",
        })
        context = format_chart(result)
    except Exception as exc:  # a calculation failure never reaches the model
        import logging

        logging.getLogger("kavach.chat").warning(
            "Natal chart context failed: %s", type(exc).__name__)
        return None
    state["chart"] = result
    state["fingerprint"] = fingerprint
    state["context"] = context
    return context


# --- the gate ----------------------------------------------------------------
def gate(conversation_id: str, question: str, route: str) -> Tuple[str, str]:
    """Decide how a message may be answered: (kind, value).

    kind == "reply"    deterministic answer, no provider call, no model.
    kind == "context"  authoritative chart context for the model.
    kind == "continue" ordinary flow, no chart context.

    Readings, reading follow-ups and out-of-scope requests are never touched:
    their contexts stay exactly as they were.
    """
    from chat.router import (ASTROLOGY, CHIT_CHAT, GREETINGS, OUT_OF_SCOPE,
                             PERSONAL_READING, READING_FOLLOWUP,
                             has_astrology_signal)

    if route in (PERSONAL_READING, READING_FOLLOWUP, OUT_OF_SCOPE):
        return "continue", ""

    text = (question or "").strip()
    if not text:
        return "continue", ""
    low = text.lower()
    tokens = re.findall(r"[a-z']+", low)
    chit_chat = ((any(token in CHIT_CHAT for token in tokens) and len(tokens) <= 3)
                 or any(greeting in low for greeting in GREETINGS))

    parsed_date = parse_date(text)
    parsed_time = parse_time(text)
    natal_question = needs_natal(text) and not chit_chat

    state = _STATES.get(conversation_id)
    if state is None:
        if not natal_question:
            # A bare date or detail with no chart request stays ordinary chat
            # (the assistant acknowledges it without inventing anything).
            return "continue", ""
        state = _new_state(pending=text)
        _STATES[conversation_id] = state
        _evict(conversation_id)
    elif natal_question and not state.get("pending"):
        state["pending"] = text

    # The place is only read from a detail-shaped message once both other
    # details exist (in this message or earlier in this conversation).
    effective_date = parsed_date or state.get("date")
    effective_time = parsed_time or state.get("time")
    parsed_place = parse_place(text) if (effective_date and effective_time) else None

    changed = False
    for key, value in (("date", parsed_date), ("time", parsed_time),
                       ("place", parsed_place)):
        if value and value != state.get(key):
            state[key] = value
            changed = True
    if changed:
        # A corrected detail invalidates the cached chart.
        state["chart"] = None
        state["context"] = None
        state["fingerprint"] = None

    if (state.get("place") and state.get("latitude") is None
            and state.get("date") and state.get("time")):
        failure = _resolve_place(state)
        if failure:
            return "reply", failure

    if _missing(state):
        if parsed_date or parsed_time or parsed_place or natal_question:
            return "reply", _missing_reply(state)
        # Ordinary conversation while details are still being collected is
        # never interrupted with a nag.
        return "continue", ""

    # Chart context is supplied only when this message actually carries chart
    # intent: an explicit personal-chart question, an astrology question, or a
    # message genuinely supplying/correcting birth details. A calculated chart
    # is never attached to ordinary conversation just because it is cached.
    # Intent is checked FIRST: parse_place() can return leftover words from
    # ordinary prose, which is not evidence of chart intent.
    chart_intent = (natal_question or route == ASTROLOGY
                    or has_astrology_signal(text))
    supplies_details = bool(parsed_date or parsed_time) or (
        bool(parsed_place) and natal_question)
    if not chart_intent and not supplies_details:
        return "continue", ""

    context = _context(state)
    if context is None:
        return "reply", CALCULATION_FAILED_REPLY
    return "context", context


# --- output scrub ------------------------------------------------------------
def _segments(text: str) -> List[str]:
    """Sentence/newline segments WITH their separators, so formatting survives."""
    return re.split(r"([.!?][\s]+|\n+)", text or "")


def _signs_in(sentence: str) -> set:
    low = sentence.lower()
    return {sign for sign in SIGNS_LOWER if re.search(rf"\b{sign}\b", low)}


def _grounded(sentence: str, facts: Dict[str, Any]) -> bool:
    """True when the sentence claims no placement the calculated chart lacks."""
    from panchang.constants import NAKSHATRA_NAMES

    low = sentence.lower()
    signs = _signs_in(sentence)
    houses = {int(value) for value in
              re.findall(r"\b(\d{1,2})(?:st|nd|rd|th)\s+house\b", low)}

    # Ascendant / Lagna claims.
    if re.search(r"\b(ascendant|lagna)\b", low):
        if houses and not all(number == 1 for number in houses):
            return False
        if signs and (facts.get("lagna") or "").lower() not in signs:
            return False

    # Identity claims ("you are a Taurus").
    identity = re.search(r"\byou(?:'re| are)\s+(?:a|an)\s+([a-z]+)\b", low)
    if identity:
        claimed = identity.group(1).lower()
        if claimed in SIGNS_LOWER:
            if claimed not in ((facts.get("lagna") or "").lower(),
                               (facts.get("sun") or "").lower(),
                               (facts.get("moon") or "").lower()):
                return False

    # Moon sign / Rashi claims.
    if re.search(r"\bmoon\s+sign\b|\brashi\b", low):
        if signs and (facts.get("moon") or "").lower() not in signs:
            return False

    # Sun sign claims.
    if re.search(r"\bsun\s+sign\b", low):
        if signs and (facts.get("sun") or "").lower() not in signs:
            return False

    # Nakshatra claims.
    if "nakshatra" in low:
        actual = (facts.get("nakshatra") or "").lower()
        mentioned = {name.lower() for name in NAKSHATRA_NAMES if name.lower() in low}
        if mentioned and actual not in mentioned:
            return False

    planets = facts.get("planets") or {}
    for name, info in planets.items():
        key = name.lower()
        # "your Saturn is in Libra" / "your Moon in Taurus ...".
        if re.search(rf"\byour\s+{key}\b", low) and signs:
            if (info.get("sign") or "").lower() not in signs:
                return False
        # "Saturn is in Libra" / "Saturn occupies Libra".
        direct = re.search(
            rf"\b{key}\s+(?:is\s+|occupies\s+|sits\s+in\s+|lies\s+in\s+)?"
            rf"in\s+([a-z]+)\b", low)
        if direct and direct.group(1).lower() in SIGNS_LOWER:
            if direct.group(1).lower() != (info.get("sign") or "").lower():
                return False
        # "your Saturn in the 7th house" / "Saturn in the 7th house".
        house_claim = re.search(
            rf"\b(?:your\s+)?{key}\s+(?:is\s+)?in\s+(?:the\s+)?"
            rf"(\d{{1,2}})(?:st|nd|rd|th)\s+house\b", low)
        if house_claim and int(house_claim.group(1)) != info.get("house"):
            return False
    return True


def scrub(text: str, conversation_id: str) -> str:
    """Drop fabricated natal claims from a chart-context answer.

    Only sentences that assert a personal placement the calculated chart does
    not show are removed; everything else (formatting, general explanation)
    is preserved verbatim. Returns CHART_FALLBACK_REPLY when nothing grounded
    remains.
    """
    state = _STATES.get(conversation_id)
    if not state or not state.get("chart") or not text:
        return text

    summary = state["chart"].get("summary") or {}
    planet_rows = state["chart"].get("planets") or []
    facts = {
        "lagna": summary.get("lagnaRashi"),
        "moon": summary.get("moonRashi"),
        "sun": summary.get("sunRashi"),
        "nakshatra": summary.get("nakshatra"),
        "planets": {row.get("planet"): {"sign": row.get("rashi"),
                                        "house": row.get("house")}
                    for row in planet_rows if row.get("planet")},
    }

    segments = _segments(text)
    kept: List[str] = []
    for index in range(0, len(segments), 2):
        content = segments[index]
        separator = segments[index + 1] if index + 1 < len(segments) else ""
        if content.strip() and not _grounded(content, facts):
            continue
        kept.append(content + separator)
    result = "".join(kept).strip()
    return result if result else CHART_FALLBACK_REPLY
