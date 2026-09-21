"""Curated contextual application layer.

Composition model (per the KAVACH Tarot spec):
    CARD CORE  +  DOMAIN MEANING  +  SUBCONTEXT MEANING

The card keeps its traditional meaning; the domain decides which part of life
that meaning is applied to; the subcontext sharpens it. Card-specific curated
entries (knowledge.contexts) always win when present.
"""

from __future__ import annotations

from typing import Dict, Optional

# How a card's meaning applies inside each domain.
DOMAIN_RULES: Dict[str, str] = {
    "education": "On the study side, this shows up in how your preparation, focus and results are likely to go",
    "love": "In this connection, this shows up in how it develops and how you come across",
    "friendship": "In the friendship, this shows up in how you are with each other",
    "family": "At home, this shows up in how people are treating each other",
    "career": "In work terms, this shows up in the opportunity, your position and how you handle it",
    "money": "Financially, this shows up in earning, spending and how secure things feel",
    "communication": "In the exchange, this shows up in how things are said and how they land",
    "conflict": "In the disagreement, this shows up in what is really causing the friction",
    "general_period": "For the period ahead, this shows up in how it feels and what it asks of you",
    "growth": "For your own development, this shows up in the habits you are building",
    "general": "In your situation, this shows up in what is actually happening around you",
}

# Sharpens the domain application for the specific kind of question.
SUBCONTEXT_EMPHASIS: Dict[str, str] = {
    "education_exam": "with the exam itself in front of you",
    "study_strategy": "in how you study rather than how much you study",
    "study_general": "over the course of your studies",
    "love_attraction": "with the other person's response still unknown",
    "love_existing": "inside an existing relationship",
    "love_reconciliation": "where repairing something matters more than winning",
    "contact_reply": "while you are waiting for a reply",
    "friendship_communication": "in how you reach out to each other",
    "friendship_reconciliation": "where the friendship can be repaired if handled well",
    "career_opportunity": "with the opportunity and where it could lead",
    "career_advancement": "in how your position or standing develops",
    "business_venture": "in the practical side of running or starting something",
    "money_outlook": "in the balance between what comes in and what goes out",
    "communication_outlook": "in how clearly things are being understood",
    "conflict_outlook": "in what would actually settle it",
    "general_period": "over the next stretch of time",
    "personal_growth": "in the pattern you are trying to change",
    "general": "in what is in front of you",
}

SOURCE_CURATED_CONTEXT = "curated_context"
SOURCE_CURATED_DOMAIN = "curated_domain"
SOURCE_FALLBACK = "fallback"


def compose(card_phrase: str, domain: str, subcontext: str) -> Optional[str]:
    """Card phrase applied through domain + subcontext. None if unsupported."""
    rule = DOMAIN_RULES.get(domain)
    if not rule:
        return None
    emphasis = SUBCONTEXT_EMPHASIS.get(subcontext) or SUBCONTEXT_EMPHASIS["general"]
    phrase = card_phrase.strip().rstrip(".")
    phrase = phrase[0].upper() + phrase[1:]
    return f"{phrase}. {rule}, {emphasis}."


def is_supported(domain: str, subcontext: str) -> bool:
    return domain in DOMAIN_RULES
