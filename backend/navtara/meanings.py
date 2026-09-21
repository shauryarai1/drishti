"""PRIVATE Navtara meanings - structured knowledge only, no astrology invented.

Planet rules, aspect logic and house overlays are deliberately absent: those
rules have not been supplied. Public wording rules live here too so future
renderers cannot accidentally expose the mechanism.
"""

from __future__ import annotations

from typing import Dict, List

# Tara -> structured meaning used by future interpretation layers.
TARA_MEANINGS: Dict[str, Dict[str, object]] = {
    "Janma": {
        "nature": "caution",
        "about": "the native themself",
        "themes": ["self", "health", "mind", "identity", "personality",
                   "habits", "thoughts", "personal state", "natural behaviour"],
        "public_tone": ["personal condition", "your own state", "how you feel and respond"],
    },
    "Sampat": {
        "nature": "supportive",
        "about": "resources and prosperity",
        "themes": ["wealth", "prosperity", "resources", "financial gains",
                   "comforts", "sources of benefit"],
        "public_tone": ["resources", "material support", "comfort and gain"],
    },
    "Vipat": {
        "nature": "caution",
        "about": "friction and disruption",
        "themes": ["challenges", "clashes", "misunderstandings", "frustration",
                   "difficulties", "disruption", "obstacles"],
        "public_tone": ["patience", "checking details", "avoiding haste",
                        "avoiding unnecessary confrontation"],
    },
    "Kshema": {
        "nature": "supportive",
        "about": "security and wellbeing",
        "themes": ["happiness", "security", "wellbeing", "comfort",
                   "supportive activity", "children", "personal happiness"],
        "public_tone": ["support and security", "wellbeing", "comfort"],
    },
    "Pratyari": {
        "nature": "caution",
        "about": "resistance and opposition",
        "themes": ["opposition", "resistance", "opponents", "disagreement",
                   "opinion clashes", "expectations not met", "mental strain"],
        "public_tone": ["resistance from people or circumstances", "delay",
                        "a need to stay patient with others"],
    },
    "Sadhaka": {
        "nature": "supportive",
        "about": "effort and achievement",
        "themes": ["effort", "achievement", "accomplishment", "decisions",
                   "partnerships", "progress", "productive action"],
        "public_tone": ["focused effort", "progress through your own work",
                        "steady accomplishment"],
        "note": "effort is part of the result; not effortless luck",
    },
    "Vadha": {
        "nature": "strong_caution",
        "about": "heavy resistance",
        "themes": ["strong difficulties", "frustrating experiences", "deprivation",
                   "major resistance", "difficult lessons", "areas needing care"],
        "public_tone": ["strong caution", "a more demanding period",
                        "greater resistance", "additional care for new beginnings"],
        "note": "never read literally; no death, fatality or lifespan meaning",
    },
    "Mitra": {
        "nature": "supportive",
        "about": "what the native gives to others",
        "themes": ["support given", "cooperation offered", "nourishment provided",
                   "constructive interaction", "contribution to others"],
        "direction": "native_to_others",
        "public_tone": ["how you come across to people", "what you offer others",
                        "cooperative contact you initiate"],
    },
    "AtiMitra": {
        "nature": "strongly_supportive",
        "about": "what the native receives from others",
        "themes": ["cooperation received", "help received", "support from people",
                   "favourable responses", "assistance from relationships and networks"],
        "direction": "others_to_native",
        "public_tone": ["support arriving from others", "cooperation you receive",
                        "help from people around you"],
    },
}

# Special Nakshatra layer (independent of the Tara classification).
SPECIAL_MEANINGS: Dict[str, Dict[str, object]] = {
    "Jati": {"themes": ["social lineage", "peer group", "like-minded people",
                        "natural community fit", "community identity", "family circle"]},
    "Karma": {"themes": ["work", "profession", "career condition", "professional functioning"]},
    "Desha": {"themes": ["place of living", "relocation", "foreign travel", "immigration",
                         "residence matters", "change of location", "adjustment",
                         "displacement", "location stability"]},
    "Abhisheka": {"themes": ["public honour", "admiration", "appreciation", "recognition",
                             "promotion", "leadership", "authority", "high achievement"]},
    "Sanghatika": {"themes": ["social ties", "social activities", "inner circle",
                              "close network", "people immediately around the native"]},
    "Samudaya": {"themes": ["broader community", "wider network", "outer social circle",
                            "public reputation", "public success", "larger groups"]},
    "Adhana": {"themes": ["foundation", "long-term settlement", "underlying life base",
                          "domestic stability", "family wellbeing", "long-term foundation"]},
}

# Wording rules future renderers must respect.
FORBIDDEN_PUBLIC_TERMS = (
    "navtara", "navatara", "janma tara", "sampat tara", "vipat tara", "kshema tara",
    "pratyari tara", "sadhaka tara", "vadha tara", "mitra tara", "ati-mitra", "atimitra",
    "tara number", "relative position", "1/10/19", "2/11/20", "3/12/21",
    "jati nakshatra", "karma nakshatra", "desha nakshatra", "abhisheka nakshatra",
    "sanghatika nakshatra", "samudaya nakshatra", "adhana nakshatra",
)

FORBIDDEN_PUBLIC_CLAIMS = ("death", "die", "fatal", "lifespan", "killed", "killing",
                           "guaranteed", "will definitely")


def tara_meaning(tara: str) -> Dict[str, object]:
    return TARA_MEANINGS.get(tara, {})


def special_meaning(role: str) -> Dict[str, object]:
    return SPECIAL_MEANINGS.get(role, {})


def public_tone(tara: str) -> List[str]:
    return list(TARA_MEANINGS.get(tara, {}).get("public_tone", []))  # type: ignore[arg-type]
