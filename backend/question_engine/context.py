"""Deterministic question context: intent, subject, time scope, domains, channels.

The user's language controls routing. Astrological placements never decide
what the user was asking.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

from jyotish.classification import classify_question
from kavach_core.domains import INTENT_DOMAINS, PERIOD_DOMAINS

CONTEXT_PROVENANCE: Dict[str, str] = {
    "source_type": "kavach_custom",
    "source": "kavach_astrologer_rule",
    "status": "approved",
}

TIME_SCOPES = ("evening", "tonight", "today", "tomorrow", "morning", "week", "now")

# Subject patterns (user language first).
SUBJECT_PATTERNS: List[Dict[str, Any]] = [
    {"keywords": ["non veg", "non-veg", "nonveg", "eat", "eating", "food", "meal", "diet"],
     "subject": "eating non-vegetarian food", "intent": "decision",
     "opener": "The timing around this food choice looks", "sensitive": "food"},
    {"keywords": ["interview"], "subject": "the interview", "intent": "outcome",
     "opener": "The interview looks"},
    {"keywords": ["exam", "test", "result"], "subject": "your studies", "intent": "education",
     "opener": "Your studies look"},
    {"keywords": ["money", "earn", "salary", "income", "financial", "finance", "wealth"],
     "subject": "your earnings", "intent": "money", "opener": "The financial indication is"},
    {"keywords": ["relationship", "marriage", "partner", "love", "girlfriend", "boyfriend",
                  "wife", "husband"], "subject": "your relationship", "intent": "relationship",
     "opener": "The relationship indication is"},
    {"keywords": ["home", "house", "property", "flat", "rent"], "subject": "matters at home",
     "intent": "home", "opener": "The situation at home looks"},
    {"keywords": ["job", "career", "work", "business", "promotion", "office", "boss"],
     "subject": "your work situation", "intent": "career", "opener": "The work situation looks"},
    {"keywords": ["call", "buy", "go out", "travel", "start", "do it", "say yes", "accept"],
     "subject": "this decision", "intent": "decision", "opener": "The timing around this decision looks"},
]

PERIOD_KEYWORDS = ["evening", "tonight", "today", "tomorrow", "morning", "this week",
                   "coming period", "the period", "how will my day", "how is the coming"]

FOLLOW_UP_MARKERS = ["yea", "yeah", "yes", "no", "but", "why", "ok", "okay", "then",
                     "what about", "should i", "watch for", "really", "and", "so"]

SUBJECT_CHANGERS = {keyword for pattern in SUBJECT_PATTERNS for keyword in pattern["keywords"]}


def detect_time_scope(question: str) -> Optional[str]:
    lowered = question.lower()
    for scope in TIME_SCOPES:
        if scope in lowered:
            return scope
    return None


def _subject_from_topic(question: str) -> Dict[str, Any]:
    classification = classify_question(question)
    category = classification["category"]
    labels = {
        "career": ("your work situation", "career", "The work situation looks"),
        "relationship": ("your relationship", "relationship", "The relationship indication is"),
        "money": ("your resources", "money", "The financial indication is"),
        "decision": ("this decision", "decision", "The timing around this decision looks"),
        "emotional": ("how you are feeling", "period", "This period looks"),
        "obstacle": ("the current difficulty", "period", "The current situation looks"),
        "home": ("matters at home", "home", "The situation at home looks"),
        "education": ("your studies", "education", "Your studies look"),
        "personal": ("the coming period", "period", "This period looks"),
        "general": ("the coming period", "period", "This period looks"),
    }
    subject, intent, opener = labels.get(category, labels["general"])
    return {"subject": subject, "intent": intent, "opener": opener, "sensitive": None}


def detect_subject(question: str) -> Dict[str, Any]:
    lowered = question.lower()
    best = None
    best_score = 0
    for pattern in SUBJECT_PATTERNS:
        score = sum(len(keyword) for keyword in pattern["keywords"] if keyword in lowered)
        if score > best_score:
            best, best_score = pattern, score
    if best:
        return {"subject": best["subject"], "intent": best["intent"],
                "opener": best["opener"], "sensitive": best.get("sensitive")}
    return _subject_from_topic(question)


def is_period_question(question: str) -> bool:
    lowered = question.lower()
    return any(keyword in lowered for keyword in PERIOD_KEYWORDS)


def _has_new_subject(question: str, previous: Dict[str, Any]) -> bool:
    lowered = question.lower()
    previous_subject = (previous or {}).get("subject", "")
    previous_keywords = set()
    for pattern in SUBJECT_PATTERNS:
        if pattern["subject"] == previous_subject:
            previous_keywords = set(pattern["keywords"])
    found = {keyword for keyword in SUBJECT_CHANGERS if keyword in lowered}
    return bool(found - previous_keywords)


def is_follow_up(question: str, previous: Optional[Dict[str, Any]]) -> bool:
    if not previous or not previous.get("moment"):
        return False
    lowered = question.lower()
    if _has_new_subject(question, previous):
        return False
    if any(marker in lowered for marker in FOLLOW_UP_MARKERS):
        return True
    # A short message with no new subject continues the previous context.
    return len(lowered.split()) <= 4


def build_question_context(question: str, previous: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    follow_up = is_follow_up(question, previous)
    time_scope = detect_time_scope(question)

    if follow_up:
        subject = previous.get("subject")
        intent = previous.get("intent")
        opener = previous.get("opener")
        sensitive = previous.get("sensitive")
        resolved_question = f"{question.strip()}  ->  {previous.get('question')} ({subject})"
        scope = time_scope or previous.get("time_scope")
        scope_changed = bool(time_scope and time_scope != previous.get("time_scope"))
    else:
        detected = detect_subject(question)
        subject = detected["subject"]
        intent = detected["intent"]
        opener = detected["opener"]
        sensitive = detected["sensitive"]
        resolved_question = question.strip()
        scope = time_scope or ("now" if intent != "period" else "now")
        scope_changed = False

    if is_period_question(question) and not follow_up:
        intent = "period"
        subject = subject if subject != "the coming period" else "the coming period"

    allowed: Set[str] = set(INTENT_DOMAINS.get(intent or "general", PERIOD_DOMAINS))

    classification = classify_question(resolved_question)
    primary = classification["primary_channel"]
    supporting = list(classification["supporting_channels"])
    if intent == "decision":
        primary = "karana"
    if intent == "period":
        primary = "vaar"
        supporting = ["nakshatra", "yoga"]
    if intent == "money":
        primary = "tithi"
        supporting = ["karana", "yoga"]

    return {
        "question": question.strip(),
        "resolved_question": resolved_question,
        "intent": intent,
        "subject": subject,
        "sensitive": sensitive,
        "time_scope": scope,
        "scope_changed": scope_changed,
        "allowed_domains": sorted(allowed),
        "primary_channel": primary,
        "supporting_channels": supporting,
        "opener": opener,
        "follow_up": follow_up,
        "retained_subject": previous.get("subject") if follow_up and previous else None,
        "retained_intent": previous.get("intent") if follow_up and previous else None,
        "provenance": dict(CONTEXT_PROVENANCE),
    }
