"""BNN directional friend / enemy / neutral registry (owner-approved).

DIRECTIONAL: friendship is always read from the REFERENCE planet's row. No
symmetry is inferred, and Parashari natural friendship is not used.

Only the nine planets have rows; anything unspecified is NEUTRAL.
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

FRIEND = "FRIEND"
ENEMY = "ENEMY"
NEUTRAL = "NEUTRAL"

PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")

# reference planet -> (friends, enemies).  Anything else -> NEUTRAL.
BNN_RELATIONSHIPS: Dict[str, Tuple[Tuple[str, ...], Tuple[str, ...]]] = {
    "Sun": (("Moon", "Mars", "Mercury", "Jupiter"), ("Venus", "Saturn", "Rahu", "Ketu")),
    "Moon": (("Sun", "Mars", "Jupiter", "Mercury"), ("Venus", "Saturn", "Rahu", "Ketu")),
    "Mars": (("Moon", "Jupiter", "Venus", "Sun", "Ketu"), ("Mercury", "Rahu", "Saturn")),
    "Mercury": (("Venus", "Saturn", "Sun", "Rahu"), ("Mars", "Moon", "Jupiter")),
    "Jupiter": (("Sun", "Mars", "Saturn", "Rahu", "Ketu", "Moon"), ("Mercury", "Venus")),
    "Venus": (("Mars", "Mercury", "Saturn", "Rahu"), ("Sun", "Moon", "Ketu")),
    "Saturn": (("Mercury", "Jupiter", "Venus", "Rahu"), ("Sun", "Mars", "Moon")),
    "Rahu": (("Mercury", "Saturn", "Venus", "Jupiter"), ("Moon", "Mars", "Sun")),
    "Ketu": (("Mars", "Jupiter"), ("Venus", "Saturn", "Mercury", "Moon", "Sun")),
}


def relationship(reference_planet: str, target_planet: str) -> str:
    """Friendship FROM the reference planet's perspective."""
    entry = BNN_RELATIONSHIPS.get(reference_planet)
    if not entry or reference_planet == target_planet:
        return NEUTRAL
    friends, enemies = entry
    if target_planet in friends:
        return FRIEND
    if target_planet in enemies:
        return ENEMY
    return NEUTRAL


def is_directional() -> bool:
    """Guard for tests/readers: the table is not required to be symmetric."""
    return True


def friends_of(planet: str) -> Tuple[str, ...]:
    return BNN_RELATIONSHIPS.get(planet, ((), ()))[0]


def enemies_of(planet: str) -> Tuple[str, ...]:
    return BNN_RELATIONSHIPS.get(planet, ((), ()))[1]
