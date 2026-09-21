"""The five KAVACH Panchang channels and their interpretation domains.

The SAME planet in the SAME house means something different per channel, so
each channel has its own domain and its own sentence framing. Channels are
independent and never merged.
"""

from __future__ import annotations

from typing import Dict, List

CHANNELS = ("vaar", "tithi", "karana", "nakshatra", "yoga")

CHANNEL_DEFINITIONS: Dict[str, Dict[str, object]] = {
    "vaar": {
        "title": "Personality & Vitality",
        "domain": "Personality & Vitality",
        "areas": [
            "temperament", "personal expression", "vitality tendencies",
            "way energy is directed", "personal development",
        ],
        "guidance": "Personal direction develops through how this energy is expressed day to day.",
    },
    "tithi": {
        "title": "Relationships & Prosperity",
        "domain": "Relationships & Prosperity",
        "areas": [
            "relationships", "cooperation", "material wellbeing", "prosperity",
            "values", "relationship stability",
        ],
        "guidance": "Cooperation and balanced connection tend to support this area.",
    },
    "karana": {
        "title": "Career & Decisions",
        "domain": "Career & Decisions",
        "areas": [
            "professional behaviour", "work", "decision-making", "execution",
            "ability to act on opportunities", "practical judgment",
        ],
        "guidance": "Careful analysis followed by consistent action tends to support this area.",
    },
    "nakshatra": {
        "title": "Inner Patterns",
        "domain": "Inner Patterns",
        "areas": [
            "subconscious habits", "instinctive responses",
            "deep behavioural tendencies", "habitual tendencies",
        ],
        "guidance": "Recurring inner patterns become easier to work with when they are noticed.",
    },
    "yoga": {
        "title": "Challenges & Support",
        "domain": "Challenges & Support",
        "areas": [
            "resilience", "support during difficulty", "obstacle handling",
            "ability to recover", "protective and supportive tendencies",
        ],
        "guidance": "Support during difficulty tends to come through the area described here.",
    },
}

PAST_LIFE_NOTE = (
    "In the astrologer's tradition this channel is also read as past-habit "
    "tendencies; this is a traditional framing rather than an objective claim."
)

# Sentence framing per channel: how the planet's channel and the house combine.
CHANNEL_FRAMES: Dict[str, str] = {
    "vaar": "Personal energy and vitality tend to express through {planet}. This is channelled into {house}.",
    "tithi": "Relationships and material wellbeing are connected with {planet}, expressed through {house}.",
    "karana": "Professional behaviour and decision-making are connected with {planet}, expressed through {house}.",
    "nakshatra": "At an inner level, {planet} may shape recurring habits and instinctive responses around {house}.",
    "yoga": "During difficult periods, {planet} may become a source of support, expressed through {house}.",
}


def channel_title(channel: str) -> str:
    return str(CHANNEL_DEFINITIONS.get(channel, {}).get("title", channel))


def channel_areas(channel: str) -> List[str]:
    return list(CHANNEL_DEFINITIONS.get(channel, {}).get("areas", []))  # type: ignore[arg-type]
