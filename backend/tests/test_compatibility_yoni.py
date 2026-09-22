"""Yoni Kuta: exhaustive source-data tests.

Source of truth: the owner-supplied image `source-material/yoni-nakshatra.jpeg`
(27 Nakshatra -> animal + Yoni gender) and the Class 2 matrix (slides 9-10).
The image's personality descriptions are not part of this feature.
"""

from __future__ import annotations

import pathlib

import pytest

from compatibility import yoni
from compatibility.models import PersonFacts
from compatibility.yoni import MATRIX_ORDER, YONI_BY_NAKSHATRA, matrix_value, yoni_of
from kundli.analysis.signs import SIGN_LORD
from navtara.constants import NAKSHATRAS

REPO = pathlib.Path(__file__).resolve().parents[2]
IMAGE = REPO / "source-material" / "yoni-nakshatra.jpeg"

# Transcribed from the image and verified against it (animal, gender).
EXPECTED = {
    "Ashwini": ("Horse", "Male"),
    "Bharani": ("Elephant", "Male"),
    "Krittika": ("Goat", "Female"),
    "Rohini": ("Serpent", "Male"),
    "Mrigashira": ("Serpent", "Female"),
    "Ardra": ("Dog", "Female"),
    "Punarvasu": ("Cat", "Female"),
    "Pushya": ("Goat", "Male"),
    "Ashlesha": ("Cat", "Male"),
    "Magha": ("Rat", "Male"),
    "Purva Phalguni": ("Rat", "Female"),
    "Uttara Phalguni": ("Cow", "Male"),
    "Hasta": ("Buffalo", "Female"),
    "Chitra": ("Tiger", "Female"),
    "Swati": ("Buffalo", "Male"),
    "Vishakha": ("Tiger", "Male"),
    "Anuradha": ("Deer", "Female"),
    "Jyeshtha": ("Deer", "Male"),
    "Mula": ("Dog", "Male"),
    "Purva Ashadha": ("Monkey", "Male"),
    "Uttara Ashadha": ("Mongoose", "Male"),
    "Shravana": ("Monkey", "Female"),
    "Dhanishta": ("Lion", "Female"),
    "Shatabhisha": ("Horse", "Female"),
    "Purva Bhadrapada": ("Lion", "Male"),
    "Uttara Bhadrapada": ("Cow", "Female"),
    "Revati": ("Elephant", "Female"),
}


def person(name, role, nakshatra):
    return PersonFacts(name=name, role=role, moon_sign="Aries",
                       moon_nakshatra=nakshatra, moon_ruler=SIGN_LORD["Aries"])


def test_source_image_is_present():
    assert IMAGE.exists(), "the owner-supplied Yoni image must be present"


def test_mapping_has_exactly_27_one_per_nakshatra():
    assert len(YONI_BY_NAKSHATRA) == 27
    assert set(YONI_BY_NAKSHATRA) == set(NAKSHATRAS)


def test_every_animal_and_gender_matches_the_source_image():
    for nakshatra, expected in EXPECTED.items():
        assert YONI_BY_NAKSHATRA[nakshatra] == expected, nakshatra


def test_fourteen_distinct_animals_are_represented():
    animals = {animal for animal, _ in YONI_BY_NAKSHATRA.values()}
    assert len(animals) == 14


def test_both_yoni_genders_occur_in_the_mapping():
    genders = {gender for _, gender in YONI_BY_NAKSHATRA.values()}
    assert genders == {"Male", "Female"}


def test_matrix_is_fourteen_by_fourteen_with_a_four_diagonal():
    assert len(MATRIX_ORDER) == 14
    for animal in MATRIX_ORDER:
        row = yoni.YONI_MATRIX[animal]
        assert len(row) == 14
        assert row[animal] == 4, animal
        assert set(row.values()) <= {0, 1, 2, 3, 4}


def test_matrix_orientation_is_male_row_female_column():
    """Owner ruling: rows = MALE, columns = FEMALE. Documented and enforced."""
    source = (REPO / "backend" / "compatibility" / "yoni.py").read_text(encoding="utf-8")
    assert "ROWS    = MALE" in source
    assert "COLUMNS = FEMALE" in source
    assert '"matrixOrientation": "male_row_female_column"' in source


def test_worked_example_from_the_deck():
    """Groom Ashlesha = Cat, bride Ashwini = Horse -> 2."""
    assert yoni_of("Ashlesha") == ("Cat", "Male")
    assert yoni_of("Ashwini") == ("Horse", "Male")
    assert matrix_value("Cat", "Horse") == 2

    result = yoni.evaluate(person("A", "bride", "Ashwini"), person("B", "groom", "Ashlesha"))
    assert result.facts["score"] == 2


def test_asymmetric_pair_proves_the_orientation_is_not_transposed():
    """Horse/Deer is asymmetric: male Horse x female Deer = 3, the reverse = 1."""
    assert matrix_value("Horse", "Deer") == 3
    assert matrix_value("Deer", "Horse") == 1

    male_horse = yoni.evaluate(person("A", "bride", "Anuradha"),    # Deer
                               person("B", "groom", "Ashwini"))     # Horse
    male_deer = yoni.evaluate(person("A", "bride", "Ashwini"),      # Horse
                              person("B", "groom", "Anuradha"))     # Deer
    assert male_horse.facts["score"] == 3
    assert male_deer.facts["score"] == 1
    assert male_horse.facts["score"] != male_deer.facts["score"]


def test_swapping_roles_changes_the_value_where_the_matrix_is_asymmetric():
    forward = yoni.evaluate(person("A", "bride", "Ashwini"), person("B", "groom", "Anuradha"))
    reverse = yoni.evaluate(person("A", "bride", "Anuradha"), person("B", "groom", "Ashwini"))
    assert forward.facts["score"] != reverse.facts["score"]


def test_yoni_gender_is_independent_of_the_bride_groom_role():
    """A bride with a Male-yoni Nakshatra keeps that gender; roles never swap it."""
    result = yoni.evaluate(person("A", "bride", "Ashwini"),    # Male yoni, bride
                           person("B", "groom", "Anuradha"))   # Female yoni, groom
    assert result.facts["brideYoniGender"] == "Male"
    assert result.facts["groomYoniGender"] == "Female"
    # ...and the axis is still groom-row/bride-column, not gender-based.
    assert result.facts["score"] == matrix_value("Deer", "Horse") == 1


def test_status_bands_and_no_invented_values():
    pairs = [("Ashwini", "Ashwini"), ("Ashwini", "Anuradha"), ("Anuradha", "Ashwini"),
             ("Ashlesha", "Ashwini")]
    for bride_nak, groom_nak in pairs:
        result = yoni.evaluate(person("A", "bride", bride_nak), person("B", "groom", groom_nak))
        assert 0 <= result.points_awarded <= 4
        assert result.status in ("Strong alignment", "Supportive", "Mixed", "Needs attention")


def test_yoni_never_exposes_an_animal_in_public_text():
    result = yoni.evaluate(person("A", "bride", "Ashwini"), person("B", "groom", "Ashlesha"))
    # Internal evidence stays server-side...
    assert result.facts["brideAnimal"] == "Horse"
    assert result.facts["score"] == 2
    # ...and never crosses the public serialization boundary.
    public = result.to_public()
    assert "facts" not in public and "points" not in public
    blob = f"{public['label']} {public['subtitle']} {public['summary']} {public['status']}".lower()
    for animal in ("horse", "cat", "elephant", "serpent", "deer", "lion", "mongoose",
                   "monkey", "buffalo", "tiger", "rat", "cow", "dog", "goat", "sheep"):
        assert animal not in blob, animal
    assert "yoni" not in blob
    assert "male" not in blob and "female" not in blob
    assert "score" not in blob and "matrix" not in blob
