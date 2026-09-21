"""Canonical Bhava (house) meanings and condition groups.

Standard Jyotish foundation layer. Paraphrased house themes, not copied prose.
House 8 is never a death prediction; astrology is never used for lifespan.
"""

from __future__ import annotations

from typing import Dict, List, Optional

HOUSE_MEANINGS: Dict[int, str] = {
    1: "self, body, identity, temperament, personal direction",
    2: "wealth, accumulated resources, family, speech, values",
    3: "effort, courage, communication, skills, siblings, initiative",
    4: "home, property, emotional foundations, inner security",
    5: "education, intelligence, creativity, judgment, children, romance",
    6: "competition, obstacles, service, routines, debts, conflict, health-related challenges",
    7: "marriage, partnerships, agreements, dealing with others",
    8: "transformation, vulnerability, shared matters, sudden change, hidden complications",
    9: "fortune, higher learning, teachers, beliefs, long journeys",
    10: "career, profession, responsibility, authority, reputation, public action",
    11: "gains, networks, friends, aspirations, fulfilment",
    12: "expenses, withdrawal, foreign places, isolation, release",
}


# Short composed phrases used to build readable sentences.
HOUSE_CORE: Dict[int, str] = {
    1: "self and personal direction",
    2: "resources and values",
    3: "effort and communication",
    4: "home and inner security",
    5: "learning, creativity and romance",
    6: "work routines and obstacles",
    7: "partnerships and agreements",
    8: "change and shared matters",
    9: "learning, beliefs and fortune",
    10: "career and responsibility",
    11: "gains and networks",
    12: "expenditure, boundaries and release",
}

HOUSE_GROUPS: Dict[str, List[int]] = {
    "kendra": [1, 4, 7, 10],
    "trikona": [1, 5, 9],
    "upachaya": [3, 6, 10, 11],
    "dusthana": [6, 8, 12],
}

# Nuanced, non-fatalistic wording. 6/8/12 are never "bad".
DUSTHANA_NOTES: Dict[int, str] = {
    6: "This area tends to require steady work, management and discipline, and may involve overcoming friction.",
    8: "This area may call for adjustment, resilience, and handling uncertainty or change.",
    12: "This area may call for clear boundaries, careful management of expenditure and energy, and sometimes withdrawal or release.",
}

UPACHAYA_NOTE = "This placement can emphasise gradual development through sustained effort over time."
STRUCTURAL_NOTE = "This is comparatively supportive structural context, though it still depends on the planet's condition."

WATCH_FOR: Dict[int, List[str]] = {
    6: ["overextension", "recurring friction", "uneven routines", "avoidable conflict"],
    8: ["resistance to change", "hidden complications", "reactive decisions"],
    12: ["unnecessary expenditure of time or resources", "withdrawal", "unclear boundaries"],
}


def house_meaning(house: Optional[int]) -> Optional[str]:
    if not house:
        return None
    return HOUSE_MEANINGS.get(house)


def house_conditions(house: Optional[int]) -> List[str]:
    if not house:
        return []
    names = [name for name, group in HOUSE_GROUPS.items() if house in group]
    return names


def condition_notes(house: Optional[int]) -> List[str]:
    if not house:
        return []
    notes: List[str] = []
    if house in DUSTHANA_NOTES:
        notes.append(DUSTHANA_NOTES[house])
    if house in HOUSE_GROUPS["upachaya"]:
        notes.append(UPACHAYA_NOTE)
    if house in HOUSE_GROUPS["kendra"] or house in HOUSE_GROUPS["trikona"]:
        notes.append(STRUCTURAL_NOTE)
    return notes


def watch_for(house: Optional[int]) -> List[str]:
    if not house:
        return []
    return list(WATCH_FOR.get(house, []))
