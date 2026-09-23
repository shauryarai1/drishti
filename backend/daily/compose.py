"""Daily composition: HOUSE (Nakshatra-agnostic) x CURRENT Nakshatra semantics.

The house establishes its life area, its generic NEEDS (concept relevance) and
its generic CONTEXT (active / relational / reflective / ...). The Nakshatra
supplies its own approved concepts from profiles.py. The concept's generic
behaviour is then expressed in the house context. Deterministic only.
"""

from __future__ import annotations

import re

from .house_semantics import HOUSE_SEMANTICS
from .nakshatra_semantics import behaviour_selection, role_phrase

# Neutral predicates used when the concept and the predicate would repeat the
# same idea (e.g. "patient" + "patience"). Language only, never per-Nakshatra.
NEUTRAL_PREDICATES = (
    "will help you handle things more smoothly.",
    "should make the day easier to manage.",
    "will keep things on an even keel.",
)

_SUFFIXES = ("ingly", "ation", "ness", "ment", "ity", "ion", "ive", "ous",
             "ance", "ence", "ing", "ly", "ed", "es", "e", "y")

# Function words carry no semantic idea, so they must never trigger the guard.
_STOPWORDS = {
    "through", "is", "are", "was", "were", "be", "been", "being", "what", "which", "who",
    "you", "your", "them", "they", "the", "a", "an", "and", "or", "of", "to", "in", "on",
    "at", "by", "as", "for", "with", "this", "that", "these", "those", "it", "its",
    "today", "here", "there", "more", "than", "then", "so", "not", "no", "will", "would",
    "can", "could", "may", "might", "should", "do", "does", "did", "help", "helps",
    "things", "really", "going", "keep", "keeps", "make", "makes", "worth", "day", "days",
}


def _stem(word: str) -> str:
    text = "".join(ch for ch in word.lower() if ch.isalpha())
    for suffix in _SUFFIXES:
        if len(text) > len(suffix) + 3 and text.endswith(suffix):
            return text[: -len(suffix)]
    return text


def _stems(text: str) -> set:
    return {_stem(word) for word in re.findall(r"[a-zA-Z]+", text)
            if word.lower() not in _STOPWORDS}


def _collision(first: str, second: str) -> bool:
    """True when the two fragments share a closely related word stem."""
    for a in _stems(first):
        for b in _stems(second):
            common = 0
            for char_a, char_b in zip(a, b):
                if char_a != char_b:
                    break
                common += 1
            if common >= 3 and max(len(a), len(b)) >= 5:
                return True
    return False


def _house(active_house: int) -> dict:
    return HOUSE_SEMANTICS.get(active_house, HOUSE_SEMANTICS[1])


def _cap(text: str) -> str:
    return text[:1].upper() + text[1:] if text else text


def _stable(text: str) -> int:
    """Deterministic (not random) index key from the selected concept."""
    return sum(ord(char) for char in text)


def _fill(template: str, nakshatra: str, house: dict) -> str:
    needs = house.get("needs", set())
    focus = role_phrase(nakshatra, "focus", needs)
    gift = role_phrase(nakshatra, "gift", needs)
    caution = role_phrase(nakshatra, "caution", needs)
    return template.format(
        focus=focus, Focus_cap=_cap(focus),
        gift=gift, Gift_cap=_cap(gift),
        caution=caution, Caution_cap=_cap(caution),
    )


def compose_daily_pattern(active_house: int, nakshatra: str) -> str:
    house = _house(active_house)
    needs = house.get("needs", set())
    _, picked, behaviour = behaviour_selection(nakshatra, needs, house.get("context", "active"))
    key = picked[0] if picked else house["area"]
    predicates = house["predicates"]
    predicate = predicates[_stable(key) % len(predicates)]
    if _collision(behaviour, predicate):
        predicate = NEUTRAL_PREDICATES[_stable(key) % len(NEUTRAL_PREDICATES)]
    return f"{house['area']}. {_cap(behaviour)} {predicate}"


def compose_daily_category(active_house: int, nakshatra: str, category: str) -> str:
    house = _house(active_house)
    return _fill(house[category], nakshatra, house)
