"""Backwards-compatible re-export.

The authoritative mappings now live in kavach_core.mappings so that System A
and System B share one module. Edit kavach_core/mappings.py only.
"""

from __future__ import annotations

from kavach_core.mappings import (  # noqa: F401
    KARANA_LORDS,
    LIMB_PURPOSES,
    MAPPING_PROVENANCE,
    NAKSHATRA_LORDS,
    PANCHANG_LORD_MAPPINGS,
    TITHI_LORDS,
    VAAR_LORDS,
    YOGA_LORDS,
)
