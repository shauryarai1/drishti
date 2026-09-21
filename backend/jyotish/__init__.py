"""Shared Jyotish interpretation layer.

Standard Jyotish foundations (houses, planets, rulership, dignity, channel
domains) are kept separate from KAVACH astrologer rules.
"""

from .composition import interpret_channel, interpret_five_channels
from .houses import HOUSE_GROUPS, HOUSE_MEANINGS
from .planets import dignity, planet_signification
from .provenance import KAVACH_PROVENANCE, STANDARD_JYOTISH_PROVENANCE

__all__ = [
    "interpret_channel",
    "interpret_five_channels",
    "HOUSE_MEANINGS",
    "HOUSE_GROUPS",
    "dignity",
    "planet_signification",
    "STANDARD_JYOTISH_PROVENANCE",
    "KAVACH_PROVENANCE",
]
