"""Nakshatra knowledge layer tests (owner-approved transit profiles).

Astronomy and methodology are NOT re-tested here: the layer reuses the existing
authoritative sunrise Moon longitude and the existing Navtara engine.
"""

from __future__ import annotations

import pathlib

import pytest

from navtara.constants import NAKSHATRAS, canonical_nakshatra
from navtara.engine import classify_transit_nakshatra
from nakshatra_knowledge import NAKSHATRA_PROFILES, PROFILE_FIELDS, profile_for
from nakshatra_knowledge.modes import (
    NAVTARA_DAILY_TONE, compose_guidance, navtara_tone, transit_mode_line,
)

REPO = pathlib.Path(__file__).resolve().parents[2]
PKG = REPO / "backend" / "nakshatra_knowledge"


# --- data --------------------------------------------------------------------
def test_all_27_profiles_exist_exactly_once():
    assert len(NAKSHATRA_PROFILES) == 27
    assert set(NAKSHATRA_PROFILES) == set(NAKSHATRAS)
    assert list(NAKSHATRA_PROFILES) == list(NAKSHATRAS), "canonical order preserved"


def test_every_profile_has_the_approved_concept_sets():
    for name, profile in NAKSHATRA_PROFILES.items():
        assert set(profile) == set(PROFILE_FIELDS), name
        for field in PROFILE_FIELDS:
            assert profile[field], (name, field)


def test_no_good_bad_labels_and_no_unsupported_metadata():
    """Profiles describe a MODE: no good/bad flags, no deity/guna invented."""
    banned = ("good", "bad", "auspicious", "inauspicious", "lucky", "unlucky",
              "gemstone", "bird", "tree", "colour", "color", "remedy", "number")
    for name, profile in NAKSHATRA_PROFILES.items():
        for field, values in profile.items():
            for value in values:
                for word in banned:
                    assert word not in value.lower(), (name, field, value)


def test_profile_lookup_is_spelling_tolerant_and_safe():
    assert profile_for("Ashwini")["mode"]
    assert profile_for("ashvini")["mode"] == profile_for("Ashwini")["mode"]
    with pytest.raises(ValueError):
        profile_for("NotANakshatra")


def test_nakshatra_boundaries_and_wraparound():
    """Boundaries come from the existing authoritative helper, not a new one."""
    from kundli.nakshatra import nakshatra_of

    assert nakshatra_of(0.0)["name"] == "Ashwini"
    assert nakshatra_of(13.0)["name"] == "Ashwini"
    assert nakshatra_of(13.34)["name"] == "Bharani"
    # Last nakshatra, then the wrap back to Ashwini.
    assert nakshatra_of(359.9)["name"] == "Revati"
    assert nakshatra_of(360.0 % 360.0)["name"] == "Ashwini"
    assert canonical_nakshatra("Revati") == "Revati"


# --- composition -------------------------------------------------------------
def test_every_nakshatra_composes_with_every_house():
    """27 x 12 reachable, never crashing, and never a hardcoded table."""
    from daily.config import HOUSE_PATTERNS

    seen = 0
    for nakshatra in NAKSHATRAS:
        for house, entry in HOUSE_PATTERNS.items():
            text = compose_guidance(str(entry["theme"]), nakshatra)
            assert text
            assert str(entry["theme"]) in text, "house context must remain present"
            seen += 1
    assert seen == 27 * 12


def test_composition_is_deterministic():
    first = compose_guidance("Career and public role", "Mrigashira")
    assert first == compose_guidance("Career and public role", "Mrigashira")


def test_house_context_is_modified_not_replaced():
    """The same Nakshatra yields different guidance for different houses."""
    career = compose_guidance("Career and public role", "Mrigashira")
    partnership = compose_guidance("Relationships and partnership", "Mrigashira")
    assert career != partnership
    assert "Career and public role" in career
    assert "Relationships and partnership" in partnership
    # Both carry the same Nakshatra mode (the HOW is shared, the WHERE differs).
    assert "search" in career and "search" in partnership


def test_no_hardcoded_prediction_table():
    for path in PKG.glob("*.py"):
        source = path.read_text(encoding="utf-8")
        # 324 = 27 x 12: a hardcoded full matrix would need that many entries.
        assert "324" not in source, path.name
        for banned in ("Ashwini_H1", "predictions[", "PREDICTION_TABLE"):
            assert banned not in source, (path.name, banned)


def test_mode_line_uses_today_language_not_natal_personality():
    line = transit_mode_line("Hasta")
    assert line.startswith("Today's lunar pattern")
    for banned in ("people", "natives", "person born", "you are"):
        assert banned not in line.lower(), banned


# --- personal Navtara --------------------------------------------------------
def test_nine_navtara_tones_exist_and_do_not_change_the_engine():
    from navtara.constants import TARA_SEQUENCE

    assert set(NAVTARA_DAILY_TONE) == set(TARA_SEQUENCE)
    assert len(NAVTARA_DAILY_TONE) == 9
    assert navtara_tone(None) is None
    assert navtara_tone("NotATara") is None
    assert navtara_tone("AtiMitra")["tone"]


def test_personal_tone_reuses_the_existing_navtara_engine():
    result = classify_transit_nakshatra("Ashwini", "Hasta")
    assert result is not None
    tara = result.get("tara") or result.get("name")
    assert tara in NAVTARA_DAILY_TONE
    text = compose_guidance("Career and public role", "Hasta", navtara=tara)
    assert "Personally" in text


def test_personal_tone_only_appears_when_a_natal_nakshatra_is_supplied():
    generic = compose_guidance("Career and public role", "Hasta")
    assert "Personally" not in generic


def test_navtara_wraparound_is_the_existing_engines():
    """Revati -> Ashwini is position 2 (Sampat) in the existing engine."""
    result = classify_transit_nakshatra("Revati", "Ashwini")
    tara = result.get("tara") or result.get("name")
    assert tara == "Sampat"


def test_natal_moon_is_never_treated_as_a_nakshatra():
    """A Rashi name must not be accepted as a Janma Nakshatra."""
    source = (PKG / "modes.py").read_text(encoding="utf-8")
    for banned in ("natal_moon", "rashi_to_nakshatra", "RASHI_NAKSHATRA"):
        assert banned not in source, banned
    for rashi in ("Aries", "Taurus", "Gemini"):
        with pytest.raises(ValueError):
            profile_for(rashi)
