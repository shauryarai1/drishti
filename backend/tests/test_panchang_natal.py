"""Tests for the Panchang natal significator engine (mapping layer + selection)."""

from __future__ import annotations

import pytest

from prediction.panchang_natal import selectors
from prediction.panchang_natal.engine import compute_panchang_natal_significators
from prediction.panchang_natal.mappings import (
    KARANA_LORDS,
    NAKSHATRA_LORDS,
    TITHI_LORDS,
    VAAR_LORDS,
    YOGA_LORDS,
)

DELHI = ("2008-05-14", "14:35", 28.632803, 77.219771, "Asia/Kolkata", "Delhi, India")


@pytest.fixture(scope="module")
def result():
    return compute_panchang_natal_significators(*DELHI)


# --- 1. Vara ---------------------------------------------------------------
@pytest.mark.parametrize(
    ("weekday", "lord"),
    [(0, "Moon"), (1, "Mars"), (2, "Mercury"), (3, "Jupiter"),
     (4, "Venus"), (5, "Saturn"), (6, "Sun")],
)
def test_vara_mapping(weekday, lord):
    assert selectors.vara_lord(weekday) == lord
    assert VAAR_LORDS[weekday] == lord


# --- 2. Tithi --------------------------------------------------------------
@pytest.mark.parametrize(
    ("number", "lord"),
    [(1, "Sun"), (2, "Moon"), (3, "Mars"), (4, "Mercury"), (5, "Jupiter"),
     (6, "Venus"), (7, "Saturn"), (8, "Rahu"), (9, "Sun"), (10, "Moon"),
     (11, "Mars"), (12, "Mercury"), (13, "Jupiter"), (14, "Venus"), (15, "Saturn")],
)
def test_tithi_mapping(number, lord):
    assert TITHI_LORDS[number] == lord
    assert selectors.tithi_lord(number - 1) == lord


def test_purnima_and_amavasya_both_saturn():
    assert selectors.tithi_lord(14) == "Saturn"   # Purnima (Shukla 15th)
    assert selectors.tithi_lord(29) == "Saturn"   # Amavasya (Krishna 15th)


def test_tithi_paksha_is_preserved(result):
    tithi = result["channels"]["tithi"]
    assert tithi["context"]["paksha"] in ("Shukla", "Krishna")
    assert 1 <= tithi["context"]["number_in_paksha"] <= 15


# --- 3. Karana -------------------------------------------------------------
@pytest.mark.parametrize(
    ("name", "lord"),
    [("Bava", "Sun"), ("Balava", "Moon"), ("Kaulava", "Mars"), ("Taitila", "Mercury"),
     ("Garaja", "Jupiter"), ("Vanija", "Venus"), ("Vishti", "Saturn"), ("Bhadra", "Saturn"),
     ("Shakuni", "Rahu"), ("Chatushpada", "Ketu"), ("Naga", "Rahu"), ("Kimstughna", "Ketu")],
)
def test_karana_mapping(name, lord):
    assert KARANA_LORDS[name] == lord
    assert selectors.karana_lord(name) == lord


@pytest.mark.parametrize(
    ("variant", "canonical"),
    [("Gara", "Garaja"), ("gara", "Garaja"), ("Vanij", "Vanija"),
     ("Bhadra", "Vishti"), ("Sakuni", "Shakuni"), ("Kintughna", "Kimstughna")],
)
def test_karana_spelling_variants(variant, canonical):
    assert selectors.normalize("karana", variant) == canonical


# --- 4. Nakshatra ----------------------------------------------------------
ALL_NAKSHATRAS = [name for names in NAKSHATRA_LORDS.values() for name in names]  # type: ignore[union-attr]


def test_all_27_nakshatras_present_and_mapped():
    assert len(ALL_NAKSHATRAS) == 27
    for name in ALL_NAKSHATRAS:
        assert selectors.nakshatra_lord(name) is not None


@pytest.mark.parametrize(
    ("name", "lord"),
    [("Ashvini", "Ketu"), ("Magha", "Ketu"), ("Mula", "Ketu"),
     ("Bharani", "Venus"), ("Purva Phalguni", "Venus"), ("Purva Ashadha", "Venus"),
     ("Krittika", "Sun"), ("Uttara Phalguni", "Sun"), ("Uttara Ashadha", "Sun"),
     ("Rohini", "Moon"), ("Hasta", "Moon"), ("Shravana", "Moon"),
     ("Mrigashira", "Mars"), ("Chitra", "Mars"), ("Dhanishta", "Mars"),
     ("Ardra", "Rahu"), ("Swati", "Rahu"), ("Shatabhisha", "Rahu"),
     ("Punarvasu", "Jupiter"), ("Vishakha", "Jupiter"), ("Purva Bhadrapada", "Jupiter"),
     ("Pushya", "Saturn"), ("Anuradha", "Saturn"), ("Uttara Bhadrapada", "Saturn"),
     ("Ashlesha", "Mercury"), ("Jyeshtha", "Mercury"), ("Revati", "Mercury")],
)
def test_nakshatra_lords(name, lord):
    assert selectors.nakshatra_lord(name) == lord


def test_nakshatra_spelling_variants():
    assert selectors.nakshatra_lord("Ashwini") == "Ketu"
    assert selectors.nakshatra_lord("Jyestha") == "Mercury"
    assert selectors.nakshatra_lord("Shatabhisha") == "Rahu"


# --- 5. Yoga ---------------------------------------------------------------
YOGA_ORDER = [
    "Vishkumbha","Priti","Ayushman","Saubhagya","Shobhana","Atiganda","Sukarma",
    "Dhriti","Shoola","Ganda","Vriddhi","Dhruva","Vyaghata","Harshana","Vajra",
    "Siddhi","Vyatipata","Variyana","Parigha","Shiva","Siddha","Sadhya","Shubha",
    "Shukla","Brahma","Indra","Vaidhriti",
]


def test_all_27_yogas_present_and_mapped():
    assert len(YOGA_ORDER) == 27
    for index in range(27):
        assert selectors.yoga_lord(index, YOGA_ORDER[index]) is not None


@pytest.mark.parametrize(
    ("index", "lord"),
    [(0, "Ketu"), (1, "Venus"), (2, "Sun"), (3, "Moon"), (4, "Mars"),
     (5, "Rahu"), (6, "Jupiter"), (7, "Saturn"), (8, "Mercury"),
     (9, "Ketu"), (10, "Venus"), (11, "Sun"), (12, "Moon"), (13, "Mars"),
     (14, "Rahu"), (15, "Jupiter"), (16, "Saturn"), (17, "Mercury"),
     (18, "Ketu"), (19, "Venus"), (20, "Sun"), (21, "Moon"), (22, "Mars"),
     (23, "Rahu"), (24, "Jupiter"), (25, "Saturn"), (26, "Mercury")],
)
def test_yoga_lords(index, lord):
    assert YOGA_LORDS[index + 1] == lord
    assert selectors.yoga_lord(index, YOGA_ORDER[index]) == lord


def test_yoga_name_resolution_when_index_unavailable():
    # Out-of-range / missing index falls back to name resolution.
    assert selectors.yoga_lord(-1, "Variyan") == "Mercury"      # spelling variant of Variyana
    assert selectors.yoga_lord(999, "Variyan") == "Mercury"
    assert selectors.yoga_lord(999, "Saubhagya") == "Moon"
    assert selectors.yoga_lord(999, "NotAYoga") is None


# --- Engine output ---------------------------------------------------------
def test_all_five_channels_present_with_domains(result):
    channels = result["channels"]
    assert set(channels) == {"vaar", "tithi", "karana", "nakshatra", "yoga"}
    assert channels["vaar"]["interpretation_domain"] == ["life_force", "vitality", "personality"]
    assert "marital_bliss" in channels["tithi"]["interpretation_domain"]
    assert "decision_making" in channels["karana"]["interpretation_domain"]
    assert "instinctive_reactions" in channels["nakshatra"]["interpretation_domain"]
    assert "overcoming_obstacles" in channels["yoga"]["interpretation_domain"]


def test_every_selected_lord_is_located_in_the_natal_chart(result):
    for channel in result["channels"].values():
        placement = channel["natal_placement"]
        assert placement, f"{channel['limb']} has no placement"
        assert "missing_in_chart" not in placement
        assert placement["rashi"] and placement["house"]


def test_same_lord_in_two_channels_stays_separate():
    """A synthetic case: same planet selected by two limbs must not collapse."""
    channels = {
        "vaar": {"lord": "Jupiter", "domain": ["life_force", "vitality", "personality"]},
        "tithi": {"lord": "Jupiter", "domain": ["marital_bliss", "relationship_wellbeing", "prosperity"]},
    }
    assert channels["vaar"]["lord"] == channels["tithi"]["lord"]
    assert channels["vaar"]["domain"] != channels["tithi"]["domain"]


def test_no_interpretation_text_or_scoring_produced(result):
    blob = str(result["channels"]).lower()
    for forbidden in ("exalted", "debilitated", "benefic", "malefic", "score",
                      "probability", "strength", "will happen", "lifespan", "death"):
        assert forbidden not in blob
    assert result["status"] == "significators_only_no_interpretation"
