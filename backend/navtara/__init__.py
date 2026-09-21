"""PRIVATE KAVACH Navtara foundation (premium personalised forecast basis).

Not customer-facing. Public output must never expose the mechanism.
"""

from .constants import (
    CAUTION_TARAS,
    NAKSHATRAS,
    NAKSHATRA_COUNT,
    SPECIAL_ROLES,
    TARA_SEQUENCE,
)
from .engine import (
    NavtaraPosition,
    NavtaraProfile,
    build_navtara_profile,
    classify_transit_nakshatra,
    get_janma_nakshatra_from_birth_details,
    get_navtara,
    get_special_roles,
    get_tara_from_position,
    relative_nakshatra_position,
    summarise_profile,
)
from .meanings import (
    FORBIDDEN_PUBLIC_CLAIMS,
    FORBIDDEN_PUBLIC_TERMS,
    SPECIAL_MEANINGS,
    TARA_MEANINGS,
)

__all__ = [
    "CAUTION_TARAS",
    "NAKSHATRAS",
    "NAKSHATRA_COUNT",
    "SPECIAL_ROLES",
    "TARA_SEQUENCE",
    "TARA_MEANINGS",
    "SPECIAL_MEANINGS",
    "FORBIDDEN_PUBLIC_TERMS",
    "FORBIDDEN_PUBLIC_CLAIMS",
    "NavtaraPosition",
    "NavtaraProfile",
    "build_navtara_profile",
    "classify_transit_nakshatra",
    "get_janma_nakshatra_from_birth_details",
    "get_navtara",
    "get_special_roles",
    "get_tara_from_position",
    "relative_nakshatra_position",
    "summarise_profile",
]
