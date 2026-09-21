"""Question understanding for Ask KAVACH (Tarot is never mentioned publicly).

Determines domain, subcontext, intent, subject and timeframe from the user's
own words. The reading is interpreted through this context, never the reverse.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

DOMAINS: List[Tuple[str, List[str]]] = [
    ("education", ["exam", "study", "studying", "revision", "revise", "test", "result",
                   "admission", "college", "school", "university", "marks", "grades",
                   "syllabus", "study strategy", "engineer", "engineering", "degree"]),
    ("love", ["girl", "boy", "she", "accept me", "love", "romantic",
              "proposal", "propose", "crush", "likes me", "like me", "reject", "reply",
              "relationship", "marriage", "partner"]),
    ("friendship", ["friend", "friends", "friendship", "mate"]),
    ("family", ["family", "mother", "father", "parents", "brother", "sister"]),
    ("career", ["job", "offer", "interview", "promotion", "career", "work", "company",
                "boss", "resign", "business", "profession", "appraisal"]),
    ("money", ["money", "earn", "salary", "income", "finance", "finances", "financial",
               "loan", "savings", "invest", "profit", "wealth", "afford"]),
    ("communication", ["talk", "communication", "communicate", "message", "call",
                       "speak", "conversation"]),
    ("conflict", ["argument", "fight", "conflict", "upset", "angry", "dispute"]),
    ("general_period", ["evening", "tonight", "today", "tomorrow", "week", "period",
                        "coming days", "day go"]),
    ("growth", ["improve", "better", "grow", "develop", "confidence", "discipline",
                "habit", "focus"]),
]

INTENTS = {
    "education": "outcome_guidance",
    "love": "response_from_other_person",
    "friendship": "relationship_outlook",
    "family": "relationship_outlook",
    "career": "decision",
    "money": "outcome_guidance",
    "communication": "communication_outlook",
    "conflict": "conflict_outlook",
    "general_period": "short_term_outlook",
    "growth": "self_development",
    "general": "general_guidance",
}

SUBJECTS = {
    "education": "your studies",
    "love": "this connection",
    "friendship": "this friendship",
    "family": "the situation at home",
    "career": "this opportunity",
    "money": "your finances",
    "communication": "the communication between you",
    "conflict": "the tension between you",
    "general_period": "the coming period",
    "growth": "your own development",
    "general": "your situation",
}

DOMAIN_CONCERN = {
    "education": "study, preparation and results",
    "love": "romantic interest and how the situation develops",
    "friendship": "the friendship and how you are with each other",
    "family": "family relationships",
    "career": "work, opportunity and the decision in front of you",
    "money": "earning, resources and financial security",
    "communication": "talking things through and being understood",
    "conflict": "the disagreement and how it resolves",
    "general_period": "the period ahead and how it is likely to feel",
    "growth": "your own habits and development",
    "general": "the situation you are asking about",
}

REFUSALS = ("death", "die", "cancer", "pregnan", "diagnos")

_CLEAN = re.compile(r"[^a-z0-9\s]")


DOMAIN_WEIGHT = {"career": 1.3, "education": 1.3, "money": 1.2, "general_period": 1.2}


def _matches(keyword: str, text: str) -> bool:
    if " " in keyword:
        return keyword in text
    return re.search(r"\b" + re.escape(keyword) + r"\b", text) is not None


def classify(question: str) -> Dict[str, Any]:
    lowered = _CLEAN.sub(" ", (question or "").lower())
    best_domain, best_score = "general", 0.0
    for domain, keywords in DOMAINS:
        score = float(sum(len(word) for word in keywords if _matches(word, lowered)))
        score *= DOMAIN_WEIGHT.get(domain, 1.0)
        if score > best_score:
            best_domain, best_score = domain, score

    timeframe: Optional[str] = None
    for word in ("tomorrow", "tonight", "evening", "today", "this week", "soon", "now"):
        if word in lowered:
            timeframe = word
            break

    return {
        "domain": best_domain,
        "subcontext": resolve_subcontext(best_domain, lowered),
        "intent": INTENTS.get(best_domain, "general_guidance"),
        "subject": SUBJECTS.get(best_domain, "your situation"),
        "concern": DOMAIN_CONCERN.get(best_domain, "the situation you are asking about"),
        "timeframe": timeframe,
        "refusal": next((word for word in REFUSALS if word in lowered), None),
    }


def resolve_subcontext(domain: str, lowered: str) -> str:
    if domain == "education":
        if any(word in lowered for word in ("strategy", "how should i study", "improve my study", "study plan", "concentrate")):
            return "study_strategy"
        if any(word in lowered for word in ("exam", "test", "revision", "revise", "paper", "marks", "grades", "result")):
            return "education_exam"
        return "study_general"
    if domain == "love":
        if any(word in lowered for word in ("reconcile", "back together", "again", "forgive")):
            return "love_reconciliation"
        if any(word in lowered for word in ("married", "marriage", "long term", "partner", "husband", "wife")):
            return "love_existing"
        if any(word in lowered for word in ("reply", "respond", "message", "text")):
            return "contact_reply"
        return "love_attraction"
    if domain == "career":
        if "business" in lowered or "startup" in lowered or "venture" in lowered:
            return "business_venture"
        if "promotion" in lowered or "raise" in lowered or "appraisal" in lowered:
            return "career_advancement"
        return "career_opportunity"
    if domain == "friendship":
        if any(word in lowered for word in ("again", "talk to me", "forgive", "reconcile", "stopped")):
            return "friendship_reconciliation"
        return "friendship_communication"
    if domain == "money":
        return "money_outlook"
    if domain == "general_period":
        return "general_period"
    if domain == "growth":
        return "personal_growth"
    if domain == "conflict":
        return "conflict_outlook"
    if domain == "communication":
        return "communication_outlook"
    return "general"


DOMAIN_OPENERS = {
    "education": "On the exam and study side, this {tone}.",
    "love": "On this connection, the picture {tone}.",
    "friendship": "With the friendship, this {tone}.",
    "family": "At home, the situation {tone}.",
    "career": "On the work opportunity, this {tone}.",
    "money": "On the financial side, this {tone}.",
    "communication": "On the communication, this {tone}.",
    "conflict": "On the tension between you, this {tone}.",
    "general_period": "The {scope} {tone}.",
    "growth": "On your own habits, this {tone}.",
    "general": "Looking at your situation, this {tone}.",
}

TONE = {
    "encouraging": "looks reasonably encouraging",
    "mixed": "looks mixed rather than settled",
    "cautious": "looks like it needs some care right now",
}
