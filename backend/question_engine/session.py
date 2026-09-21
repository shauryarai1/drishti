"""In-memory conversation context retention.

Keeps the last MEANINGFUL question so contextual follow-ups ("yea should i",
"why?", "what should I watch for?") resolve against it. Invalid messages and
greetings never overwrite the retained context.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

_STORE: Dict[str, Dict[str, Any]] = {}


def session_key(latitude: float, longitude: float, location_label: str = "") -> str:
    return (location_label or "").strip().lower() or f"{round(latitude, 2)},{round(longitude, 2)}"


def get_context(key: str) -> Optional[Dict[str, Any]]:
    return _STORE.get(key)


def remember(key: str, context: Dict[str, Any], moment_timestamp: str) -> None:
    _STORE[key] = {
        "question": context.get("resolved_question") or context.get("question"),
        "subject": context.get("subject"),
        "intent": context.get("intent"),
        "opener": context.get("opener"),
        "sensitive": context.get("sensitive"),
        "time_scope": context.get("time_scope"),
        "allowed_domains": context.get("allowed_domains"),
        "domain": context.get("domain"),
        "subcontext": context.get("subcontext"),
        "timeframe": context.get("timeframe"),
        "moment": moment_timestamp,
    }


def clear() -> None:
    _STORE.clear()
