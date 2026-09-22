"""DEV ONLY: Ask KAVACH inspector.

Runs the SAME pipeline as public /api/ask and returns the internal audit:
context, decision reason, draw, cards, contextual meanings, private context,
conversation history, model/fallback info and raw vs sanitised response.

Never returns credentials, headers or environment values. Reuses the public
reading engine (chat.reading / tarot) - there is no second implementation.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from chat import session
from chat.gemini import MODEL_PRIORITY, UNAVAILABLE_MESSAGE
from chat.reading import SPREAD_LABELS, build_reading, is_new_question, private_context
from tarot.context import DOMAINS, _matches
from tarot.knowledge import CARDS

CARD_TERMS = ("tarot", "card", "cards", "upright", "reversed", "spread", "arcana",
              "wands", "cups", "swords", "pentacles", "private kavach reading",
              "situation:", "influence:")

SECRET_FIELDS = ("api_key", "apikey", "gemini_api_key", "authorization", "x-goog-api-key",
                 "headers", "env", "environ", "secret", "token", "password", "credential")


def sanitise_public(text: str) -> str:
    """The same public sanitiser the live endpoint applies."""
    kept = []
    for sentence in re.split(r"(?<=[.!?])\s+", text or ""):
        lowered = sentence.lower()
        if any(term in lowered for term in CARD_TERMS):
            continue
        kept.append(sentence.strip())
    return " ".join(part for part in kept if part).strip()


def _keywords(text: str) -> set:
    lowered = (text or "").lower()
    return {keyword for _domain, keywords in DOMAINS for keyword in keywords if _matches(keyword, lowered)}


def decision_reason(question: str, active: Optional[Dict[str, Any]], is_new: bool) -> str:
    """Why the engine decided NEW vs REUSED - from the real conditions."""
    if not active:
        return "no active reading for this conversation"
    if is_new:
        new_keywords = _keywords(question) - set(active.get("keywords") or [])
        if new_keywords:
            return "new subject detected: " + ", ".join(sorted(new_keywords))
        return "no follow-up marker and message is longer than a contextual follow-up"
    lowered = (question or "").lower()
    from chat.reading import FOLLOW_UP_MARKERS

    marker = next((item for item in FOLLOW_UP_MARKERS if item in lowered), None)
    if marker:
        return f'explicit follow-up marker: "{marker.strip()}"'
    return "short contextual follow-up with no new subject"


def _card_payload(reading: Dict[str, Any]) -> List[Dict[str, Any]]:
    cards = []
    for index, (draw, item) in enumerate(zip(reading["cards"], reading["interpretations"])):
        card = CARDS.get(draw["card_id"], {})
        cards.append({
            "position": draw["position"],
            "position_label": SPREAD_LABELS[index] if index < len(SPREAD_LABELS) else draw["position"],
            "card_id": draw["card_id"],
            "name": draw["name"],
            "orientation": draw["orientation"],
            "valence": item.get("valence"),
            "core_meaning": item.get("core_meaning"),
            "contextual_meaning": item.get("reading"),
            "source": item.get("source"),
            "themes": card.get("themes", []),
            "available": item.get("available", True),
        })
    return cards


def _forced_reading(question: str, card_id: str, orientation: str) -> Dict[str, Any]:
    """DEV ONLY: inspect a chosen card without touching the random draw."""
    from tarot.context import classify
    from tarot.engine import interpret_card

    context = classify(question)
    draw = {
        "card_id": card_id,
        "name": CARDS[card_id]["name"],
        "orientation": orientation if orientation in ("upright", "reversed") else "upright",
        "position": "direction and guidance",
    }
    interpretation = interpret_card(draw, context)
    return {
        "draw_id": f"forced-{card_id}-{draw['orientation']}",
        "question": question,
        "context": context,
        "keywords": sorted(_keywords(question)),
        "cards": [draw],
        "interpretations": [interpretation],
        "forced": True,
        "contextual_meaning": interpretation.get("reading") or interpretation.get("core_meaning"),
    }


def inspect(conversation_id: str, question: str, mode: str = "local",
            force: Optional[List[str]] = None, orientation: str = "auto",
            generate: bool = False) -> Dict[str, Any]:
    """Run the real pipeline and return the inspector payload."""
    history = session.get_history(conversation_id)
    active = session.get_reading(conversation_id)
    before = active.get("draw_id") if active else None

    forced = bool(force)
    if forced:
        reading = _forced_reading(question, force[0], orientation)
        is_new = True
        reason = "dev forced-card inspection"
    else:
        is_new = mode == "redraw" or is_new_question(question, active)
        reason = ("manual dev redraw" if mode == "redraw"
                  else decision_reason(question, active, is_new))
        reading = build_reading(question) if is_new else active

    reused = (not is_new) and reading is active

    payload: Dict[str, Any] = {
        "mode": mode if not forced else "force",
        "question": question,
        "conversation_id": conversation_id,
        "request": {"type": "REUSED READING" if reused else "NEW READING", "reason": reason},
        "draw": {"before": before, "after": reading.get("draw_id"), "reused": reused},
        "context": reading.get("context"),
        "cards": _card_payload(reading),
        "private_context": private_context(reading),
        "history": history,
        "model": {
            "called": False,
            "status": "not_requested",
            "preferred": MODEL_PRIORITY[0],
            "actual": None,
            "attempts": [],
        },
        "response": {"raw": None, "public": None, "sanitised": False},
    }

    if forced:
        payload["cards"][0]["contextual_meaning"] = reading["contextual_meaning"]
        payload["model"]["status"] = "not_requested"

    if generate:
        from chat.gemini import generate_reply_detailed

        detail = generate_reply_detailed(question, history,
                                         private_context=payload["private_context"])
        raw = detail.get("text")
        public = sanitise_public(raw) if raw else None
        payload["model"] = {
            "called": True,
            "status": "ok" if raw else "unavailable",
            "preferred": detail.get("preferred", MODEL_PRIORITY[0]),
            "actual": detail.get("model"),
            "attempts": detail.get("attempts", []),
            # Mirrors the same rule as the public pipeline: true only when the
            # preferred model did not answer on its first attempt.
            "fallback": bool(detail.get("fallback")),
        }
        payload["response"] = {
            "raw": raw,
            "public": public,
            "sanitised": bool(raw and public != raw),
            "unavailable_message": None if public else UNAVAILABLE_MESSAGE,
        }
        if public:
            if not reused:
                session.set_reading(conversation_id, reading)
            session.append(conversation_id, "user", question)
            session.append(conversation_id, "assistant", public)
        payload["history"] = session.get_history(conversation_id)
    elif not forced and not reused:
        session.set_reading(conversation_id, reading)

    return payload
