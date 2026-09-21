"""Provenance for every interpretation table."""

from __future__ import annotations

from typing import Dict

STANDARD_JYOTISH_PROVENANCE: Dict[str, str] = {
    "source_type": "standard_jyotish",
    "source": "common_jyotish_foundations",
    "status": "approved",
}

KAVACH_LORD_PROVENANCE: Dict[str, str] = {
    "source_type": "kavach_custom",
    "source": "kavach_astrologer_rule",
    "status": "approved",
}

KAVACH_PROVENANCE: Dict[str, str] = KAVACH_LORD_PROVENANCE
