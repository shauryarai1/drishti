"""Question classification -> relevant Panchang channels.

KAVACH does not dump all five channels into every answer; only the relevant
primary and supporting channels are used.
"""

from __future__ import annotations

from typing import Any, Dict, List

CLASSIFICATION_PROVENANCE: Dict[str, str] = {
    "source_type": "kavach_custom",
    "source": "kavach_astrologer_rule",
    "status": "approved",
}

CATEGORIES: List[Dict[str, Any]] = [
    {
        "category": "career",
        "keywords": ["interview", "job", "career", "profession", "promotion", "business",
                     "work", "boss", "office", "appraisal", "company", "employment"],
        "primary": "karana",
        "supporting": ["yoga", "vaar"],
    },
    {
        "category": "relationship",
        "keywords": ["relationship", "marriage", "partner", "love", "girlfriend", "boyfriend",
                     "wife", "husband", "engagement", "match", "romance"],
        "primary": "tithi",
        "supporting": ["nakshatra", "yoga"],
    },
    {
        "category": "decision",
        "keywords": ["should i", "decide", "decision", "choose", "choice", "option", "whether"],
        "primary": "karana",
        "supporting": ["nakshatra", "yoga"],
    },
    {
        "category": "money",
        "keywords": ["money", "finance", "financial", "wealth", "savings", "income",
                     "salary", "loan", "debt", "profit", "gain"],
        "primary": "tithi",
        "supporting": ["karana"],
    },
    {
        "category": "emotional",
        "keywords": ["feel", "feeling", "emotion", "emotional", "peace", "anxiety",
                     "mind", "mental", "inside", "inner"],
        "primary": "nakshatra",
        "supporting": ["vaar"],
    },
    {
        "category": "obstacle",
        "keywords": ["obstacle", "difficulty", "problem", "stuck", "blocked", "delay",
                     "trouble", "struggle", "hurdle", "resistance"],
        "primary": "yoga",
        "supporting": ["karana", "nakshatra"],
    },
    {
        "category": "home",
        "keywords": ["home", "house", "property", "flat", "apartment", "land", "rent", "family"],
        "primary": "tithi",
        "supporting": ["vaar", "nakshatra"],
    },
    {
        "category": "education",
        "keywords": ["exam", "study", "education", "learning", "course", "college",
                     "school", "degree", "result", "teacher"],
        "primary": "karana",
        "supporting": ["nakshatra", "yoga"],
    },
    {
        "category": "personal",
        "keywords": ["evening", "today", "tonight", "period", "moment", "generally",
                     "overall", "myself", "personality", "life"],
        "primary": "vaar",
        "supporting": ["nakshatra", "yoga"],
    },
]

DEFAULT = {"category": "general", "primary": "vaar", "supporting": ["nakshatra", "yoga"]}


def classify_question(question: str) -> Dict[str, Any]:
    lowered = (question or "").lower()
    best = None
    best_score = 0
    for entry in CATEGORIES:
        score = sum(len(keyword) for keyword in entry["keywords"] if keyword in lowered)
        if score > best_score:
            best, best_score = entry, score
    chosen = best or DEFAULT
    return {
        "category": chosen["category"],
        "primary_channel": chosen["primary"],
        "supporting_channels": list(chosen["supporting"]),
        "provenance": dict(CLASSIFICATION_PROVENANCE),
    }
