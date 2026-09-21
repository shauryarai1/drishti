"""DEV-ONLY trace of the readings that produced real public answers.

Bounded in-memory store: the last few events per conversation. Recording only
happens while dev tools are enabled, and it is FAIL-SAFE: a problem here can
never break a public Ask KAVACH answer. Retrieval never draws cards or calls a
model - it only reads what the real pipeline already produced.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from chat.inspector import _card_payload, decision_reason  # same presenter as the inspector

MAX_EVENTS_PER_CONVERSATION = 10

_TRACES: Dict[str, List[Dict[str, Any]]] = {}


def dev_tools_enabled() -> bool:
    if os.environ.get("KAVACH_ENV", "").lower() == "production":
        return False
    return os.environ.get("KAVACH_DEV_TOOLS", "1") != "0"


def record_event(conversation_id: str, question: str, reading: Dict[str, Any],
                 reused: bool, before: Optional[str], model: Optional[Dict[str, Any]],
                 raw: Optional[str], public: Optional[str],
                 pipeline: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Store one dev event. Never raises: tracing must not affect /api/ask."""
    try:
        from chat.reading import private_context

        reading = reading or {}
        events = _TRACES.setdefault(conversation_id, [])
        detail = model or {}
        event = {
            "event_id": f"{conversation_id[:8]}-{len(events) + 1}",
            "index": len(events) + 1,
            "question": question,
            "request": {
                "type": "REUSED READING" if reused else "NEW READING",
                "reason": "reused active reading" if reused else decision_reason(question, None, True),
            },
            "draw": {"before": before, "after": reading.get("draw_id") or None, "reused": reused},
            "context": reading.get("context"),
            "cards": _card_payload(reading) if reading.get("cards") else [],
            "private_context": private_context(reading) if reading else None,
            "model": {
                "called": bool(detail),
                "status": "ok" if detail.get("text") else ("unavailable" if detail else "unknown"),
                "preferred": detail.get("preferred"),
                "actual": detail.get("model"),
                "attempts": detail.get("attempts", []),
            },
            "response": {
                "raw": raw,
                "public": public,
                "sanitised": bool(raw and public and raw != public),
            },
            "pipeline": pipeline or {"status": "ok", "stage": "completed", "safe_error": None},
            "forced": bool(reading.get("forced")),
        }
        events.append(event)
        if len(events) > MAX_EVENTS_PER_CONVERSATION:
            del events[:-MAX_EVENTS_PER_CONVERSATION]
        return event
    except Exception:
        return None


def get_event(conversation_id: str, index: Optional[int] = None) -> Optional[Dict[str, Any]]:
    events = _TRACES.get(conversation_id) or []
    if not events:
        return None
    if index is None:
        return events[-1]
    if 1 <= index <= len(events):
        return events[index - 1]
    return None


def list_events(conversation_id: str) -> List[Dict[str, Any]]:
    return list(_TRACES.get(conversation_id) or [])


def clear(conversation_id: str) -> None:
    _TRACES.pop(conversation_id, None)


def stats() -> Dict[str, Any]:
    return {"conversations": len(_TRACES),
            "events": sum(len(items) for items in _TRACES.values()),
            "max_events_per_conversation": MAX_EVENTS_PER_CONVERSATION,
            "dev_tools_enabled": dev_tools_enabled()}
