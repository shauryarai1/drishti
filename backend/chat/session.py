"""Conversation memory + active hidden reading for Ask KAVACH."""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

MAX_MESSAGES = 14
# Bound the number of conversations held in memory: conversation ids are
# client-supplied, so an unbounded dict would be a memory-exhaustion vector.
MAX_CONVERSATIONS = 2000

_CONVERSATIONS: Dict[str, List[Dict[str, str]]] = {}
_READINGS: Dict[str, Dict[str, Any]] = {}
_MODES: Dict[str, str] = {}


def new_conversation_id() -> str:
    return uuid.uuid4().hex


def _evict_oldest(keep: str) -> None:
    """Dicts preserve insertion order, so the first key is the oldest."""
    if len(_CONVERSATIONS) <= MAX_CONVERSATIONS:
        return
    for oldest in list(_CONVERSATIONS):
        if oldest != keep:
            _CONVERSATIONS.pop(oldest, None)
            _READINGS.pop(oldest, None)
            _MODES.pop(oldest, None)
            return


def get_history(conversation_id: str, limit: int = MAX_MESSAGES) -> List[Dict[str, str]]:
    return list(_CONVERSATIONS.get(conversation_id, []))[-limit:]


def append(conversation_id: str, role: str, content: str) -> None:
    if not conversation_id or not content:
        return
    messages = _CONVERSATIONS.setdefault(conversation_id, [])
    messages.append({"role": role, "content": content})
    if len(messages) > MAX_MESSAGES:
        del messages[:-MAX_MESSAGES]
    _evict_oldest(keep=conversation_id)


def set_reading(conversation_id: str, reading: Dict[str, Any]) -> None:
    if conversation_id and reading:
        _READINGS[conversation_id] = reading


def get_reading(conversation_id: str) -> Optional[Dict[str, Any]]:
    return _READINGS.get(conversation_id)


def set_mode(conversation_id: str, mode: str) -> None:
    """Remember the last KAVACH mode so follow-ups stay in the right context."""
    if conversation_id and mode:
        _MODES[conversation_id] = mode


def get_mode(conversation_id: str) -> Optional[str]:
    return _MODES.get(conversation_id)


def reset(conversation_id: str) -> None:
    _CONVERSATIONS.pop(conversation_id, None)
    _READINGS.pop(conversation_id, None)
    _MODES.pop(conversation_id, None)


def stats() -> Dict[str, Any]:
    return {"conversations": len(_CONVERSATIONS),
            "active_readings": len(_READINGS),
            "messages": sum(len(items) for items in _CONVERSATIONS.values()),
            "max_messages_per_conversation": MAX_MESSAGES}
