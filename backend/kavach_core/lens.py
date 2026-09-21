"""Channel lens: Graha-in-Bhava first, KAVACH channel second.

The base reading comes from the researched placement (kavach_core.knowledge
.graha_bhava). The lens then selects only the aspects of that placement that
belong to the requested KAVACH channel and reframes them in that channel's
language. It never concatenates planet keywords with house keywords.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from kavach_core.knowledge.graha_bhava import GRAHA_BHAVA

CHANNELS = ("vaar", "tithi", "karana", "nakshatra", "yoga")

CHANNEL_LENS: Dict[str, Dict[str, Any]] = {
    "vaar": {
        "domain": "Personality & Vitality",
        "tag": "personality",
        "closer": "This is the pattern in how you carry yourself and direct your energy.",
        "fallback_tags": ["inner", "personality"],
    },
    "tithi": {
        "domain": "Relationships & Prosperity",
        "tag": "relationships",
        "closer": "In closeness and material wellbeing, this tends to shape your experience.",
        "fallback_tags": ["challenges", "personality"],
    },
    "karana": {
        "domain": "Career & Decisions",
        "tag": "career",
        "closer": "Professionally, this is the pattern behind how you decide and act.",
        "fallback_tags": ["challenges", "inner", "personality"],
    },
    "nakshatra": {
        "domain": "Inner Patterns",
        "tag": "inner",
        "closer": "Underneath, this is one of your recurring inner habits.",
        "fallback_tags": ["personality", "inner"],
    },
    "yoga": {
        "domain": "Challenges & Support",
        "tag": "challenges",
        "closer": "When difficulties arise, this is where your support tends to come from.",
        "fallback_tags": ["relationships", "career", "inner"],
    },
}

PAST_LIFE_NOTE = (
    "Traditionally this area is also read as a past-life habit; that is a "
    "traditional framing rather than an established fact."
)

PUBLIC_DIGNITY: Dict[str, str] = {
    "own_sign": "This side of you tends to come naturally.",
    "exalted": "Here the quality tends to flow with particular ease.",
    "debilitated": "This is an area that rewards patient, deliberate development.",
}
INTERNAL_DIGNITY: Dict[str, str] = {
    "own_sign": "Planet in own sign.",
    "exalted": "Planet exalted.",
    "debilitated": "Planet debilitated: themes need conscious management.",
    "not_assigned": "Node: no classical dignity assigned.",
    "neutral": "No special dignity.",
}

SUPPORTIVE_RULE = "supportive"
CAUTION_RULE = "caution"
NEUTRAL_RULE = "neutral"

DUSTHANA = {6, 8, 12}
KENDRA_TRIKONA = {1, 4, 5, 7, 9, 10}


def _pick(items: List[str], seed: int) -> str:
    return items[seed % len(items)]


def channel_assessment(planet: str, house: Optional[int], dignity: str) -> str:
    """Deterministic evidence tag. No scoring, no numbers."""
    if dignity == "debilitated" or (house in DUSTHANA):
        return CAUTION_RULE
    if dignity in ("own_sign", "exalted") or (house in KENDRA_TRIKONA):
        return SUPPORTIVE_RULE
    return NEUTRAL_RULE


def interpret_placement(
    planet: Optional[str],
    house: Optional[int],
    rashi: Optional[str],
    dignity: str,
    channel: str,
) -> Dict[str, Any]:
    """Research base + channel lens. Returns structured, conditional language."""
    entry = (GRAHA_BHAVA.get(planet or "") or {}).get(house or 0)
    lens = CHANNEL_LENS.get(channel, CHANNEL_LENS["vaar"])

    themes: List[str] = []
    if entry:
        tag = lens["tag"]
        themes = [text for text, tags in entry["themes"] if tag in tags]
        if not themes:
            for fallback in lens["fallback_tags"]:
                themes = [text for text, tags in entry["themes"] if fallback in tags]
                if themes:
                    break

    if entry and not themes:
        # Last resort: the placement's core theme, reframed by the channel closer.
        themes = [entry["themes"][0][0]]

    if not entry or not themes:
        return {
            "channel": channel,
            "domain": lens["domain"],
            "selected_planet": planet,
            "planet_house": house,
            "planet_rashi": rashi,
            "dignity": dignity,
            "base_interpretation": None,
            "channel_interpretation": None,
            "public_text": None,
            "guidance": [],
            "watch_for": [],
            "assessment": NEUTRAL_RULE,
            "provenance": {"source_type": "standard_jyotish"},
            "available": False,
        }

    theme = themes[0]
    theme = theme[0].upper() + theme[1:]
    sentences = [theme + "." if not theme.endswith(".") else theme]

    second = None
    for fallback in lens["fallback_tags"]:
        for text, tags in entry["themes"]:
            if fallback in tags and text != theme[0].lower() + theme[1:] and text not in sentences:
                second = text
                break
        if second:
            break
    if second:
        second = second[0].upper() + second[1:]
        sentences.append(second + "." if not second.endswith(".") else second)

    sentences.append(str(lens["closer"]))

    strength_pool = entry["constructive"] if dignity in ("own_sign", "exalted") else (
        entry["challenging"] if dignity == "debilitated" else entry["constructive"]
    )
    if strength_pool:
        lead = "A natural strength here:" if strength_pool is entry["constructive"] else "The caution here:"
        sentences.append(f"{lead} {strength_pool[0]}.")

    guidance = list(entry["guidance"])
    if guidance:
        phrase = guidance[0]
        if phrase.lower().startswith("in "):
            phrase = phrase[3:]
        sentences.append(f"In practice: {phrase}.")

    if channel == "nakshatra":
        sentences.append(PAST_LIFE_NOTE)

    public_text = " ".join(sentences)
    return {
        "channel": channel,
        "domain": lens["domain"],
        "selected_planet": planet,
        "planet_house": house,
        "planet_rashi": rashi,
        "dignity": dignity,
        "base_interpretation": list(entry["themes"]),
        "channel_interpretation": themes[0],
        "public_text": public_text,
        "guidance": guidance,
        "watch_for": list(entry["challenging"]),
        "assessment": channel_assessment(planet or "", house, dignity),
        "provenance": {"source_type": "standard_jyotish", "channel_rule": {"source_type": "kavach_custom"}},
        "available": True,
    }
