"""Build the KAVACH question context: five channels plus the Prashna supplement.

System B: question moment -> five Panchang lords -> QUESTION-MOMENT D1
placements -> Graha-in-Bhava reading through the KAVACH channel lens.
"""

from __future__ import annotations

from typing import Any, Dict, List

from jyotish.classification import classify_question
from jyotish.houses import house_meaning
from jyotish.lords import resolve_five_lords
from jyotish.planets import dignity as compute_dignity
from kavach_core.lens import CHANNELS, interpret_placement

from .knowledge.kavach_custom import (
    EXTRA_CARE_HOUSES,
    safety_response,
)
from .knowledge.standard_prashna import STANDARD_RULES, rashi_lord
from .topics import HOUSE_SIGNIFICATIONS, ROUTER_PROVENANCE, route_question


def _planet(positions: List[Dict[str, Any]], name: str | None) -> Dict[str, Any] | None:
    if not name:
        return None
    return next((p for p in positions if p["planet"] == name), None)


def _placement(positions: List[Dict[str, Any]], name: str | None) -> Dict[str, Any] | None:
    found = _planet(positions, name)
    if not found:
        return None
    return {"planet": name, "rashi": found["sign"], "house": found["house"]}


def evaluate_prashna(question: str, moment: Dict[str, Any]) -> Dict[str, Any]:
    routing = route_question(question)
    classification = classify_question(question)
    primary_house = routing["primary_house"]

    chart = moment["chart"]
    positions = chart["positions"]
    lagna = chart["lagna"]
    nakshatra = moment["nakshatra"]

    lords = resolve_five_lords(moment)
    placements = {p["planet"]: {"rashi": p["sign"], "house": p["house"]} for p in positions}

    channels: Dict[str, Any] = {}
    for channel in CHANNELS:
        planet = lords.get(channel)
        placement = placements.get(planet or "", {})
        rashi = placement.get("rashi")
        channels[channel] = interpret_placement(
            planet=planet,
            house=placement.get("house"),
            rashi=rashi,
            dignity=compute_dignity(planet, rashi),
            channel=channel,
        )

    # Supplementary KAVACH day-pattern signal (Moon Nakshatra lord placement).
    moon_nak_lord = nakshatra["lord"]
    lord_placement = _placement(positions, moon_nak_lord)
    lord_house = lord_placement["house"] if lord_placement else None
    daily_moon_signal = (
        "extra_care" if lord_house in EXTRA_CARE_HOUSES
        else "supportive" if lord_house is not None
        else "unclear"
    )
    signals: List[Dict[str, Any]] = []
    if daily_moon_signal != "unclear":
        signals.append(
            {
                "rule_id": "KC_DAILY_MOON_001",
                "source_type": "kavach_custom",
                "role": "supplementary",
                "signal": daily_moon_signal,
                "reason": f"Question-moment Moon Nakshatra lord is placed in house {lord_house}.",
            }
        )

    question_house = next((h for h in chart["houses"] if h["house"] == primary_house), None)
    supplement = {
        "topic": routing["topic"],
        "primary_house": primary_house,
        "secondary_houses": routing["secondary_houses"],
        "house_signification": HOUSE_SIGNIFICATIONS.get(primary_house),
        "lagna": {"rashi": lagna["sign"], "lord": rashi_lord(lagna["sign"])},
        "moon": {"rashi": moment["moon"]["rashi"], "nakshatra": nakshatra["name"],
                 "nakshatra_lord": moon_nak_lord, "lord_placement": lord_placement},
        "question_house": {
            "house": primary_house,
            "rashi": question_house["sign"] if question_house else None,
            "lord": rashi_lord(question_house["sign"]) if question_house else None,
            "occupants": list(question_house["planets"]) if question_house else [],
        },
        "panchanga": {
            "vara": moment["vara"]["english"], "tithi": moment["tithi"]["name"],
            "karana": moment["karana"]["name"], "nakshatra": nakshatra["name"],
            "yoga": moment["yoga"]["name"],
        },
        "house_meaning": house_meaning(primary_house),
        "routing_provenance": ROUTER_PROVENANCE,
    }

    return {
        "topic": routing["topic"],
        "primary_house": primary_house,
        "house_signification": HOUSE_SIGNIFICATIONS.get(primary_house),
        "routing_provenance": ROUTER_PROVENANCE,
        "classification": classification,
        "safety": safety_response(question),
        "lords": lords,
        "channels": channels,
        "relevant_channels": {
            "primary": classification["primary_channel"],
            "supporting": classification["supporting_channels"],
        },
        "supplement": supplement,
        "context": {"moment": moment, "supplement": supplement},
        "daily_moon_signal": daily_moon_signal,
        "signals": signals,
        "standard_rules_applied": [rule["rule_id"] for rule in STANDARD_RULES],
        "kavach_rules_applied": [signal["rule_id"] for signal in signals],
        "overall_tone": (
            "caution" if daily_moon_signal == "extra_care"
            else "supportive" if daily_moon_signal == "supportive"
            else "unclear"
        ),
    }
