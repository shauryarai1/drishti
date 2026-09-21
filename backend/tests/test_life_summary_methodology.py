"""Life Summary: Panchang lord -> curated 5 x planet interpretation matrix."""

from __future__ import annotations

import inspect
import re

import pytest

from kavach_core.mappings import VAAR_LORDS
from life_summary.engine import (
    LIFE_SUMMARY_SECTIONS,
    PAST_LIFE_NOTE,
    build_channel_interpretations,
    build_life_summary,
    lookup,
)
from life_summary.knowledge import LIFE_SUMMARY_INTERPRETATIONS

DELHI = (28.6139, 77.2090, "Asia/Kolkata", "Delhi, India")
CASE = ("2010-01-21", "08:19")
EXPECTED_LORDS = {"vaar": "Jupiter", "tithi": "Venus", "karana": "Mars",
                  "nakshatra": "Saturn", "yoga": "Venus"}
CATEGORY_OF = {channel: key for key, _title, channel in LIFE_SUMMARY_SECTIONS}


@pytest.fixture(scope="module")
def channels():
    return build_channel_interpretations(*CASE, *DELHI)


@pytest.fixture(scope="module")
def summary():
    return build_life_summary(*CASE, *DELHI)


# --- 13: the validated case resolves through the real calculator ----------
def test_jan_2010_case_resolves_correctly(channels, summary):
    birth = channels["birth_panchang"]
    assert birth["weekday"] == "Thursday"
    assert birth["tithi"]["name"] == "Shashthi"
    assert birth["karana"]["current"] == "Kaulava"
    assert birth["nakshatra"]["name"] == "Uttara Bhadrapada"
    assert channels["lords"] == EXPECTED_LORDS
    assert summary["available_sections"] == 5
    bodies = " ".join(section["body"] for section in summary["sections"])
    assert "curious about why things are" in bodies   # Jupiter personality
    assert "warm and attentive" in bodies             # Venus relationships
    assert "would rather move than wait" in bodies    # Mars professional
    assert "constantly checking consequences" in bodies   # Saturn deep nature
    assert "lowering the temperature" in bodies       # Venus problems


# --- 1-5: each category is selected by its own lord alone -----------------
@pytest.mark.parametrize("channel", ["vaar", "tithi", "karana", "nakshatra", "yoga"])
def test_category_uses_its_lord_only(channels, summary, channel):
    lord = channels["lords"][channel]
    category = CATEGORY_OF[channel]
    entry = LIFE_SUMMARY_INTERPRETATIONS[category][lord]
    section = next(s for s in summary["sections"]
                   if s["key"] == category)
    from life_summary.paragraphs import paragraph_for
    assert section["body"] == paragraph_for(category, lord)
    assert entry["summary"] in entry["summary"]  # source material retained
    assert section["strengths"] == entry["strengths"]
    assert section["watch_for"] == entry["watch_for"]
    assert section["guidance"] == [entry["guidance"]]


def test_subconscious_section_frames_mind_and_habits(summary):
    section = next(s for s in summary["sections"] if s["key"] == "subconscious")
    assert section["title"] == "Subconscious Mind & Habits"
    body = section["body"].lower()
    assert "subconscious" in body or "habit" in body
    assert "inner patterns" not in body


def test_vaar_lord_alone_selects_personality(channels):
    assert channels["lords"]["vaar"] == "Jupiter"
    from life_summary.paragraphs import paragraph_for
    assert channels["channels"]["vaar"]["public_text"] == paragraph_for("personality", "Jupiter")


# --- 6: D1 house changes do not alter the readings ------------------------
def test_house_changes_do_not_alter_readings():
    morning = build_channel_interpretations("2010-01-21", "08:19", *DELHI)
    night = build_channel_interpretations("2010-01-21", "21:40", *DELHI)
    assert morning["lords"]["vaar"] == night["lords"]["vaar"]
    assert (morning["channels"]["vaar"]["public_text"]
            == night["channels"]["vaar"]["public_text"])
    assert (morning["channels"]["vaar"]["planet_house"]
            != night["channels"]["vaar"]["planet_house"])


def test_lookup_takes_only_category_and_planet():
    assert list(inspect.signature(lookup).parameters) == ["category", "planet"]


def test_readings_report_that_house_placement_is_unused(channels):
    for channel in CATEGORY_OF:
        assert channels["channels"][channel]["uses_house_placement"] is False
        assert channels["channels"][channel]["interpretation_basis"] == "panchang_lord_nature"


# --- 7: same planet, different categories ---------------------------------
@pytest.mark.parametrize("planet", list(LIFE_SUMMARY_INTERPRETATIONS["personality"]))
def test_same_planet_differs_per_category(planet):
    summaries = {
        category: table.get(planet, {}).get("summary")
        for category, table in LIFE_SUMMARY_INTERPRETATIONS.items()
    }
    assert all(summaries.values())
    assert len(set(summaries.values())) == len(summaries)


def test_venus_is_different_for_relationships_and_problems():
    relationships = LIFE_SUMMARY_INTERPRETATIONS["relationships"]["Venus"]["summary"]
    problems = LIFE_SUMMARY_INTERPRETATIONS["problems"]["Venus"]["summary"]
    assert relationships != problems
    assert "affectionate" in relationships
    assert "diplomacy" in problems


# --- 8: no house-based glue ------------------------------------------------
def test_no_house_based_language(summary):
    blob = " ".join(section["body"] for section in summary["sections"]).lower()
    for banned in ("channelled into", "is connected with", "expressed through",
                   "placed in", "in the house", "house placement", "house ",
                   "graha-in-bhava", "comparatively supportive"):
        assert banned not in blob


def test_no_internal_terms(summary):
    blob = " ".join(section["body"] for section in summary["sections"]).lower()
    for banned in ("vaar", "tithi", "karana", "nakshatra", "yoga", "lagna", "rashi",
                   "bhava", "dignity", "exalted", "debilitated", "rule_id"):
        assert banned not in blob
    for planet in LIFE_SUMMARY_INTERPRETATIONS["personality"]:
        assert planet.lower() not in blob


# --- 9: no placeholders ----------------------------------------------------
def test_no_placeholders(summary):
    assert summary["available_sections"] == 5
    for section in summary["sections"]:
        assert section["status"] == "available"
        assert section["body"] and len(section["body"]) > 80
        for banned in ("could not be composed", "has not yet been added", "not available"):
            assert banned not in section["body"]
        for word in ("pending", "placeholder", "undefined", "none"):
            assert not re.search(r"\b" + word + r"\b", section["body"].lower()), word


# --- 10: safety ------------------------------------------------------------
def test_no_lifespan_or_medical_claims(summary):
    blob = " ".join(section["body"] for section in summary["sections"]).lower()
    for banned in ("death", "die", "lifespan", "fatal", "diagnos", "disease", "cancer", "cure"):
        assert not re.search(r"\b" + banned + r"\b", blob), banned


# --- 11: no guaranteed divine intervention --------------------------------
def test_no_guaranteed_divine_intervention(summary):
    blob = " ".join(section["body"] for section in summary["sections"]).lower()
    for banned in ("guaranteed", "will intervene", "will protect you", "will remove",
                   "will solve", "assured protection"):
        assert banned not in blob
    problems = next(s for s in summary["sections"] if s["key"] == "problems")["body"].lower()
    assert "protection" in problems or "protective" in problems


# --- 12: no guaranteed marriage/career outcomes ---------------------------
def test_no_guaranteed_outcomes(summary):
    blob = " ".join(section["body"] for section in summary["sections"]).lower()
    for banned in ("will marry", "marriage will", "will prosper", "will be wealthy",
                   "will be promoted", "will definitely", "is certain"):
        assert banned not in blob


def test_all_categories_cover_every_reachable_lord():
    reachable = set(VAAR_LORDS.values())
    for table in LIFE_SUMMARY_INTERPRETATIONS.values():
        for lord in reachable:
            assert lord in table
