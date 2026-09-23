"""KAVACH Nakshatra knowledge layer (transit mode).

Additive interpretation only. It does not calculate astronomy: the transit
Nakshatra comes from the existing Daily/Panchang sunrise Moon longitude via
`kundli.nakshatra.nakshatra_of`, and the personal tone reuses the existing
Navtara engine unchanged.

House supplies WHERE the day's influence operates; the Nakshatra supplies HOW
it tends to express itself. Composition is deterministic templates over those
two supplied concept sets - there is no 27x12 hardcoded prediction table and no
LLM dependency.
"""

from .profiles import NAKSHATRA_PROFILES, PROFILE_FIELDS, profile_for

__all__ = [
    "NAKSHATRA_PROFILES",
    "PROFILE_FIELDS",
    "profile_for",
]
