"""Compatibility layer: Life Summary now lives in the dedicated life_summary package."""

from __future__ import annotations

from life_summary.engine import (  # noqa: F401
    LIFE_SUMMARY_SECTIONS,
    READING_ERROR_MESSAGE,
    build_channel_interpretations,
    build_life_summary,
)

__all__ = [
    "LIFE_SUMMARY_SECTIONS",
    "READING_ERROR_MESSAGE",
    "build_channel_interpretations",
    "build_life_summary",
]
