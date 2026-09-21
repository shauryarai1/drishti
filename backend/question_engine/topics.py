"""Editable question -> Bhava router.

Standard Prashna foundation. Broad house significations only; no medical,
death or lifespan use. Base engine follows common Prashna principles.
"""

from __future__ import annotations

from typing import Any, Dict, List

ROUTER_PROVENANCE: Dict[str, str] = {
    "source_type": "standard_prashna",
    "source": "common_prashna_house_significations",
    "status": "approved",
}

# House significations used for routing (paraphrased common Prashna meanings).
HOUSE_SIGNIFICATIONS: Dict[int, str] = {
    1: "self, general condition, body, personal state, overall situation",
    2: "money, accumulated resources, family, speech, possessions",
    3: "communication, courage, efforts, skills, siblings, short journeys",
    4: "home, property, domestic matters, emotional foundations",
    5: "education and learning, creativity, romance, children, judgment",
    6: "obstacles, competition, disputes, service routines, debts, difficulties",
    7: "marriage, relationships, partnerships, agreements, another person",
    8: "sudden change, vulnerability, shared matters, hidden complications",
    9: "higher learning, teachers, beliefs, long journeys, fortune and support",
    10: "career, profession, authority, public responsibilities, professional outcome",
    11: "gains, fulfilment, networks, friendships, aspirations",
    12: "expenses, loss and release, isolation, foreign places, withdrawal",
}

# topic -> keywords, primary house, secondary houses
TOPICS: Dict[str, Dict[str, Any]] = {
    "career": {
        "keywords": ["interview", "job", "career", "profession", "promotion", "work", "boss", "office", "appraisal", "business"],
        "primary_house": 10,
        "secondary_houses": [6, 11],
    },
    "relationship": {
        "keywords": ["relationship", "marriage", "partner", "love", "girlfriend", "boyfriend", "wife", "husband", "engagement", "match"],
        "primary_house": 7,
        "secondary_houses": [2, 11],
    },
    "money": {
        "keywords": ["money", "finance", "financial", "wealth", "savings", "income", "salary", "loan", "debt"],
        "primary_house": 2,
        "secondary_houses": [11],
    },
    "home": {
        "keywords": ["home", "house", "property", "flat", "apartment", "land", "rent", "family situation"],
        "primary_house": 4,
        "secondary_houses": [2],
    },
    "education": {
        "keywords": ["exam", "study", "education", "learning", "course", "college", "school", "degree", "result"],
        "primary_house": 5,
        "secondary_houses": [9, 11],
    },
    "gains": {
        "keywords": ["gain", "profit", "benefit", "returns", "won", "win", "reward"],
        "primary_house": 11,
        "secondary_houses": [2, 10],
    },
    "health_routine": {
        "keywords": ["routine", "workload", "stress", "energy", "wellbeing"],
        "primary_house": 6,
        "secondary_houses": [1],
    },
    "travel": {
        "keywords": ["travel", "journey", "trip", "visa", "flight", "move abroad"],
        "primary_house": 9,
        "secondary_houses": [3, 12],
    },
    "general_period": {
        "keywords": ["evening", "tonight", "today", "period", "moment"],
        "primary_house": 1,
        "secondary_houses": [],
    },
}

DEFAULT_TOPIC = "general"
DEFAULT_PRIMARY_HOUSE = 1


def route_question(question: str) -> Dict[str, Any]:
    lowered = (question or "").lower()
    best: Dict[str, Any] | None = None
    best_score = 0
    for topic, config in TOPICS.items():
        # Longer keywords are more specific, so they win ties
        # (e.g. "relationship" must beat "work").
        score = sum(len(keyword) for keyword in config["keywords"] if keyword in lowered)
        if score > best_score:
            best, best_score = {**config, "topic": topic}, score
    if best is None:
        return {
            "topic": DEFAULT_TOPIC,
            "primary_house": DEFAULT_PRIMARY_HOUSE,
            "secondary_houses": [],
            "provenance": ROUTER_PROVENANCE,
        }
    return {
        "topic": best["topic"],
        "primary_house": best["primary_house"],
        "secondary_houses": best["secondary_houses"],
        "provenance": ROUTER_PROVENANCE,
    }
