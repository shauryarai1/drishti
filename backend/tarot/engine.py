"""Internal Tarot reading engine for Ask KAVACH.

Question context -> three drawn cards (current / influence / direction) ->
contextual interpretation of each card -> ONE natural answer.

Cards, orientations and spread positions are internal evidence and are never
returned in the public response.
"""

from __future__ import annotations

import secrets
from typing import Any, Dict, List, Optional

from .context import DOMAIN_CONCERN, DOMAIN_OPENERS, TONE, classify
from .contextual import SOURCE_CURATED_CONTEXT, SOURCE_CURATED_DOMAIN, SOURCE_FALLBACK, compose
from .knowledge import CARDS, contextual_entry

POSITIONS = ("current situation", "influence or challenge", "direction and guidance")
ORDER = sorted(CARDS)

CONTEXT_FRAMES = {
    "education": {
        "focus": "in terms of study, preparation and how the exam is likely to go",
        "advice": "the useful move is to keep your preparation steady and focused rather than changing everything at the last minute",
    },
    "love": {
        "focus": "in terms of how this connection develops and how you come across to the other person",
        "advice": "the useful move is patience and giving the situation room, rather than pushing for an answer",
    },
    "friendship": {
        "focus": "in terms of the friendship and how you are with each other",
        "advice": "the useful move is to reach out simply and honestly rather than waiting for the other person to guess",
    },
    "family": {
        "focus": "in terms of the situation at home and how people are treating each other",
        "advice": "the useful move is a calm, direct conversation rather than letting it build up",
    },
    "career": {
        "focus": "in terms of the opportunity, what it could lead to and how to decide",
        "advice": "the useful move is to weigh where this leads in a year or two rather than only the immediate benefit",
    },
    "money": {
        "focus": "in terms of earning, resources and financial security",
        "advice": "the useful move is to keep decisions practical and avoid acting on hope alone",
    },
    "communication": {
        "focus": "in terms of how you express things and how they land",
        "advice": "the useful move is to say the simple, honest version rather than the perfect one",
    },
    "conflict": {
        "focus": "in terms of the disagreement and what would actually settle it",
        "advice": "the useful move is to lower the temperature first and deal with the facts second",
    },
    "general_period": {
        "focus": "in terms of how the period is likely to feel and what it asks of you",
        "advice": "the useful move is to stay flexible and not force an outcome",
    },
    "growth": {
        "focus": "in terms of your own habits and how you develop them",
        "advice": "the useful move is consistency in small steps rather than a sudden overhaul",
    },
    "general": {
        "focus": "in terms of what is actually happening around you",
        "advice": "the useful move is to stay steady and deal with what is in front of you",
    },
}

DOMAIN_EXCLUSIVE = {
    "money": ("money", "salary", "financial", "wealth", "invest", "profit", "income"),
    "career": ("job", "boss", "promotion", "interview", "business", "career", "company"),
    "love": ("romantic", "marriage", "marry", "girlfriend", "boyfriend", "partner"),
    "education": ("exam", "study", "preparation", "revision", "grades", "marks"),
}


def _domain_safe(reading: str, domain: str) -> bool:
    """A fallback reading may not carry another question domain's concerns."""
    lowered = reading.lower()
    for other, words in DOMAIN_EXCLUSIVE.items():
        if other == domain:
            continue
        if any(word in lowered for word in words):
            return False
    return True


FORBIDDEN_PUBLIC = ("card", "cards", "tarot", "spread", "upright", "reversed",
                    "arcana", "wands", "cups", "swords", "pentacles")


SECURE_RNG = secrets.SystemRandom()
DECK = tuple(ORDER)


def _orientation(rng) -> str:
    return "upright" if rng.random() < 0.5 else "reversed"


def draw_cards(rng=None, force=None, orientation: str = "auto") -> List[Dict[str, Any]]:
    """Genuine random draw: full 78-card deck, no duplicates, 50/50 orientation.

    The question and its context never influence selection. `rng` may be
    injected by tests for reproducibility; production uses secrets.SystemRandom.
    """
    source = rng or SECURE_RNG

    if force:
        drawn = []
        for index, card_id in enumerate(force[:3]):
            drawn.append({
                "card_id": card_id,
                "name": CARDS[card_id]["name"],
                "orientation": orientation if orientation in ("upright", "reversed") else "upright",
                "position": POSITIONS[index],
            })
        return drawn

    deck = list(DECK)
    source.shuffle(deck)
    return [
        {
            "card_id": card_id,
            "name": CARDS[card_id]["name"],
            "orientation": _orientation(source),
            "position": POSITIONS[index],
        }
        for index, card_id in enumerate(deck[:3])
    ]


def interpret_card(draw: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Card meaning filtered through the question's domain and subcontext."""
    card = CARDS[draw["card_id"]]
    orientation = draw["orientation"]
    base = card["upright"] if orientation == "upright" else card["reversed"]

    curated = contextual_entry(draw["card_id"], context["subcontext"])
    if curated:
        reading = curated
        source = SOURCE_CURATED_CONTEXT
    else:
        reading = compose(base, context["domain"], context["subcontext"])
        source = SOURCE_CURATED_DOMAIN if reading else SOURCE_FALLBACK
        if reading is None:
            frame = CONTEXT_FRAMES.get(context["domain"], CONTEXT_FRAMES["general"])
            reading = f"{base.capitalize()}, {frame['focus']}."
            if not _domain_safe(reading, context["domain"]):
                reading = None

    # Context overrides irrelevant meaning: a card with nothing to say about this
    # domain is dropped rather than dragging the answer off-question.
    if reading and source != SOURCE_CURATED_CONTEXT and not _domain_safe(reading, context["domain"]):
        reading = None

    if reading and orientation == "reversed" and source != SOURCE_CURATED_CONTEXT:
        reading = f"{reading} As it stands, this is being held back or delayed."

    return {
        "card_id": draw["card_id"],
        "name": card["name"],
        "core_meaning": base,
        "orientation": orientation,
        "position": draw["position"],
        "valence": _oriented_valence(card["valence"], orientation),
        "source": source,
        "themes_used": card["themes"],
        "reading": reading,
    }


def _oriented_valence(valence: str, orientation: str) -> str:
    if orientation == "upright":
        return valence
    return {"positive": "mixed", "mixed": "challenging", "challenging": "mixed"}.get(valence, "mixed")


def _assessment(readings: List[Dict[str, Any]]) -> str:
    score = {"positive": 1, "mixed": 0, "challenging": -1}
    total = sum(score.get(item["valence"], 0) for item in readings)
    if total >= 2:
        return "encouraging"
    if total <= -2:
        return "cautious"
    return "mixed"


def synthesize(context: Dict[str, Any], readings: List[Dict[str, Any]]) -> Dict[str, Any]:
    assessment = _assessment(readings)
    scope = context.get("timeframe") or "period"
    opener = DOMAIN_OPENERS.get(context["domain"], DOMAIN_OPENERS["general"]).format(
        tone=TONE[assessment], scope=scope
    )
    frame = CONTEXT_FRAMES.get(context["domain"], CONTEXT_FRAMES["general"])

    available = []
    for index, item in enumerate(item for item in readings if item.get("reading")):
        text_value = item["reading"]
        if index:
            # keep the card's own sentence only; the domain frame is stated once
            text_value = text_value.split(". ")[0].rstrip(".") + "."
        available.append(text_value)
    body = [opener] + available[:2]
    body.append(f"For guidance, {frame['advice']}.")

    answer = " ".join(body)
    return {
        "assessment": assessment,
        "concern": DOMAIN_CONCERN.get(context["domain"], context["concern"]),
        "answer": answer,
    }


def _filter(text: str) -> str:
    lowered = text.lower()
    if any(word in lowered for word in FORBIDDEN_PUBLIC):
        return ("A reading for this question is available, but it could not be phrased clearly. "
                "Please send the question once more.")
    return text


def read_question(question: str, moment_iso: str = "", force: Optional[List[str]] = None,
                  previous: Optional[Dict[str, Any]] = None, rng=None,
                  orientation: str = "auto") -> Dict[str, Any]:
    context = classify(question)
    follow_up = False
    if previous and context["domain"] == "general":
        context.update({"domain": previous.get("domain") or "general",
                        "subcontext": previous.get("subcontext") or "general",
                        "timeframe": previous.get("timeframe"),
                        "intent": previous.get("intent") or context["intent"],
                        "subject": previous.get("subject") or context["subject"]})
        follow_up = True
    context["follow_up"] = follow_up
    if context.get("refusal"):
        return {"context": context, "cards": [], "readings": [], "synthesis": None, "answer": None}
    draws = draw_cards(rng=rng, force=force, orientation=orientation)
    readings = [interpret_card(draw, context) for draw in draws]
    synthesis = synthesize(context, readings)
    return {
        "question": question,
        "context": context,
        "cards": draws,
        "readings": readings,
        "synthesis_input": [item["reading"] for item in readings if item.get("reading")],
        "synthesis": synthesis,
        "final_answer": _filter(synthesis["answer"]),
        "answer": _filter(synthesis["answer"]),
        "coverage": [item["source"] for item in readings if item.get("reading")],
    }


def simulate_draws(iterations: int = 10000, rng=None) -> Dict[str, Any]:
    """Card-selection simulation only: counts, orientation split, duplicates."""
    source = rng or SECURE_RNG
    counts: Dict[str, int] = {card_id: 0 for card_id in DECK}
    upright = reversed_count = 0
    duplicates = 0
    for _ in range(iterations):
        drawn = draw_cards(rng=source)
        ids = [item["card_id"] for item in drawn]
        if len(set(ids)) != len(ids):
            duplicates += 1
        for item in drawn:
            counts[item["card_id"]] += 1
            if item["orientation"] == "upright":
                upright += 1
            else:
                reversed_count += 1
    total = iterations * 3
    return {
        "iterations": iterations,
        "total_cards": total,
        "per_card": counts,
        "upright": upright,
        "reversed": reversed_count,
        "upright_pct": round(upright * 100.0 / total, 2),
        "reversed_pct": round(reversed_count * 100.0 / total, 2),
        "duplicate_spreads": duplicates,
        "deck_size": len(DECK),
    }
