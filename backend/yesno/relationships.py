"""Directional planet relationship for KAVACH YES / NO.

The relationship is read EXCLUSIVELY from the project's approved directional BNN
registry (`kundli.analysis.relationships`). That registry is the single source of
truth for this project's custom friendship system: it is directional (read from
the reference planet's row, never inferred symmetric) and it is NOT the standard
Parashari natural-friendship table.

This module does not copy the matrix, so the matrix can never drift between two
files: it delegates to the approved registry and derives its introspection view
from it. Anything the approved registry leaves unspecified is NEUTRAL, and a
planet compared with itself is NEUTRAL.

Direction is fixed: HOUR PLANET -> MINUTE PLANET.

Owner-approved behaviour for this feature (the registry itself is unchanged):
  * explicitly defined relationships in the approved registry are authoritative
  * unspecified ordered pairs resolve to NEUTRAL
  * same-planet pairs resolve to NEUTRAL
  * direction is strictly hour planet -> minute planet
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Dict, Mapping

from kundli.analysis.relationships import (
    BNN_RELATIONSHIPS,
    ENEMY,
    FRIEND,
    NEUTRAL,
    PLANETS,
    relationship as approved_relationship,
)

# Verdict strings.
YES = "YES"
NO = "NO"
EVEN = "50/50"

# The only place a relationship becomes a verdict.
RELATIONSHIP_VERDICTS: Mapping[str, str] = MappingProxyType({
    FRIEND: YES,
    ENEMY: NO,
    NEUTRAL: EVEN,
})

PLANET_RELATIONSHIP_STATUSES = (FRIEND, ENEMY, NEUTRAL)


def planet_relationship(hour_planet: str, minute_planet: str) -> str:
    """FRIEND / ENEMY / NEUTRAL from the HOUR planet's perspective.

    Direction is not reversed: the hour planet is the reference planet.
    """
    return approved_relationship(hour_planet, minute_planet)


def verdict_for_relationship(relationship: str) -> str:
    """FRIEND -> YES, ENEMY -> NO, NEUTRAL -> 50/50."""
    try:
        return RELATIONSHIP_VERDICTS[relationship]
    except KeyError as exc:
        raise ValueError(f"Unknown relationship {relationship!r}") from exc


def _build_matrix() -> Dict[str, Dict[str, str]]:
    """Full 9x9 directional view, derived from the approved registry."""
    return {
        reference: {target: approved_relationship(reference, target) for target in PLANETS}
        for reference in PLANETS
    }


# Derived (not duplicated) introspection view: RELATIONSHIP_MATRIX[hour][minute].
RELATIONSHIP_MATRIX: Mapping[str, Mapping[str, str]] = MappingProxyType(
    {reference: MappingProxyType(row) for reference, row in _build_matrix().items()}
)


def registry_status() -> Dict[str, object]:
    """Report the approved registry: which pairs are populated and any gaps.

    Every ordered pair of distinct planets resolves to FRIEND, ENEMY or NEUTRAL:
    the approved registry defines NEUTRAL as the fallback for anything it does not
    list explicitly. A planet compared with itself is also NEUTRAL.
    """
    explicit = 0
    for _reference, (friends, enemies) in BNN_RELATIONSHIPS.items():
        explicit += len(friends) + len(enemies)

    counts = {status: 0 for status in PLANET_RELATIONSHIP_STATUSES}
    for reference in PLANETS:
        for target in PLANETS:
            if reference == target:
                continue
            counts[approved_relationship(reference, target)] += 1

    distinct_pairs = len(PLANETS) * (len(PLANETS) - 1)
    return {
        "planets": list(PLANETS),
        "ordered_distinct_pairs": distinct_pairs,
        "same_planet_pairs": len(PLANETS),
        "explicitly_listed_pairs": explicit,
        "unspecified_pairs_treated_as_neutral": distinct_pairs - explicit,
        "counts": counts,
        "unresolved_pairs": [],
        "source": "kundli.analysis.relationships.BNN_RELATIONSHIPS",
    }
