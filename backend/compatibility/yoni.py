"""Yoni Kuta (attraction & instinctive compatibility).

Source data: the owner-supplied image `source-material/yoni-nakshatra.jpeg`
(27 Nakshatra -> Yoni animal + Yoni gender), and the Yoni matrix in
"MARRIAGE COMAPABILITY - class 2.pptx" (slides 8-10).

The image's personality descriptions are deliberately NOT encoded.

Orientation (owner ruling, and the only reading that reproduces the deck's own
worked example):
    ROWS    = MALE
    COLUMNS = FEMALE
    the GROOM is the male row and the BRIDE is the female column.

The Nakshatra's Yoni GENDER is a separate attribute of the Nakshatra and is
never derived from, or used to override, the Bride/Groom role.
"""

from __future__ import annotations

from typing import Dict, Tuple

from .models import FactorResult, PersonFacts

MALE = "Male"
FEMALE = "Female"

# Nakshatra -> (animal, yoni gender), exactly as printed in the owner image.
YONI_BY_NAKSHATRA: Dict[str, Tuple[str, str]] = {
    "Ashwini": ("Horse", MALE),
    "Bharani": ("Elephant", MALE),
    "Krittika": ("Goat", FEMALE),
    "Rohini": ("Serpent", MALE),
    "Mrigashira": ("Serpent", FEMALE),
    "Ardra": ("Dog", FEMALE),
    "Punarvasu": ("Cat", FEMALE),
    "Pushya": ("Goat", MALE),
    "Ashlesha": ("Cat", MALE),
    "Magha": ("Rat", MALE),
    "Purva Phalguni": ("Rat", FEMALE),
    "Uttara Phalguni": ("Cow", MALE),
    "Hasta": ("Buffalo", FEMALE),
    "Chitra": ("Tiger", FEMALE),
    "Swati": ("Buffalo", MALE),
    "Vishakha": ("Tiger", MALE),
    "Anuradha": ("Deer", FEMALE),
    "Jyeshtha": ("Deer", MALE),
    "Mula": ("Dog", MALE),
    "Purva Ashadha": ("Monkey", MALE),
    "Uttara Ashadha": ("Mongoose", MALE),
    "Shravana": ("Monkey", FEMALE),
    "Dhanishta": ("Lion", FEMALE),
    "Shatabhisha": ("Horse", FEMALE),
    "Purva Bhadrapada": ("Lion", MALE),
    "Uttara Bhadrapada": ("Cow", FEMALE),
    "Revati": ("Elephant", FEMALE),
}

# The matrix uses its own spellings for three animals.
_MATRIX_NAME = {"Goat": "SHEEP", "Deer": "HARE", "Mongoose": "MANGOOSE", "Serpent": "SERPANT"}

MATRIX_ORDER = ("HORSE", "ELEPHANT", "SHEEP", "SERPANT", "DOG", "CAT", "RAT", "COW",
                "BUFFALO", "TIGER", "HARE", "MONKEY", "MANGOOSE", "LION")

# rows = MALE animal, columns = FEMALE animal (Class 2 slides 9-10).
YONI_MATRIX: Dict[str, Dict[str, int]] = {
    "HORSE":    dict(zip(MATRIX_ORDER, (4, 2, 2, 3, 2, 2, 2, 1, 0, 1, 3, 3, 2, 1))),
    "ELEPHANT": dict(zip(MATRIX_ORDER, (2, 4, 3, 3, 2, 2, 2, 2, 3, 1, 2, 3, 2, 0))),
    "SHEEP":    dict(zip(MATRIX_ORDER, (2, 3, 4, 2, 1, 2, 1, 3, 3, 1, 2, 0, 3, 1))),
    "SERPANT":  dict(zip(MATRIX_ORDER, (3, 3, 2, 4, 2, 1, 1, 1, 1, 2, 2, 2, 0, 2))),
    "DOG":      dict(zip(MATRIX_ORDER, (2, 2, 1, 2, 4, 2, 1, 2, 2, 1, 0, 2, 1, 1))),
    "CAT":      dict(zip(MATRIX_ORDER, (2, 2, 2, 1, 2, 4, 0, 2, 2, 1, 3, 3, 2, 1))),
    "RAT":      dict(zip(MATRIX_ORDER, (2, 2, 1, 1, 1, 0, 4, 2, 2, 2, 2, 2, 1, 2))),
    "COW":      dict(zip(MATRIX_ORDER, (1, 2, 3, 1, 2, 2, 2, 4, 3, 0, 3, 2, 2, 1))),
    "BUFFALO":  dict(zip(MATRIX_ORDER, (0, 3, 3, 1, 2, 2, 2, 3, 4, 1, 2, 2, 2, 1))),
    "TIGER":    dict(zip(MATRIX_ORDER, (1, 1, 1, 2, 1, 1, 2, 0, 1, 4, 1, 1, 2, 1))),
    "HARE":     dict(zip(MATRIX_ORDER, (1, 2, 2, 2, 0, 3, 2, 3, 2, 1, 4, 2, 2, 1))),
    "MONKEY":   dict(zip(MATRIX_ORDER, (3, 3, 0, 2, 2, 3, 2, 2, 2, 1, 2, 4, 3, 2))),
    "MANGOOSE": dict(zip(MATRIX_ORDER, (2, 2, 3, 0, 1, 2, 1, 2, 2, 2, 2, 3, 4, 2))),
    "LION":     dict(zip(MATRIX_ORDER, (1, 0, 1, 2, 1, 1, 2, 1, 2, 1, 1, 2, 2, 4))),
}


def yoni_of(nakshatra: str) -> Tuple[str, str]:
    """(animal, yoni gender) for a Nakshatra, from the owner image."""
    return YONI_BY_NAKSHATRA[nakshatra]


def matrix_value(male_animal: str, female_animal: str) -> int:
    """MALE row -> FEMALE column, exactly as the Class 2 matrix is oriented."""
    row = _MATRIX_NAME.get(male_animal, male_animal.upper())
    col = _MATRIX_NAME.get(female_animal, female_animal.upper())
    return YONI_MATRIX[row][col]


def evaluate(bride: PersonFacts, groom: PersonFacts) -> FactorResult:
    bride_animal, bride_gender = yoni_of(bride.moon_nakshatra)
    groom_animal, groom_gender = yoni_of(groom.moon_nakshatra)

    # GROOM = male row, BRIDE = female column. The Nakshatra yoni genders are
    # recorded as separate facts and never swap the axis.
    score = matrix_value(groom_animal, bride_animal)

    if score >= 4:
        status, summary = "Strong alignment", (
            "A natural, instinctive pull between the two, with a comfortable "
            "physical and emotional rhythm."
        )
    elif score >= 2:
        status, summary = "Supportive", (
            "An easy attraction and instinctive comfort, though not without the "
            "occasional difference in pace."
        )
    elif score == 1:
        status, summary = "Mixed", (
            "Attraction is present but the instinctive styles differ enough that "
            "each may need to meet the other halfway."
        )
    else:
        status, summary = "Needs attention", (
            "Instinctive rhythms differ noticeably here, so patience and open "
            "communication may matter more than usual."
        )

    return FactorResult(
        key="yoni",
        label="Attraction & chemistry",
        subtitle="Instinctive compatibility",
        status=status,
        summary=summary,
        facts={
            # Internal evidence only: never serialized to the customer.
            "brideAnimal": bride_animal,
            "brideYoniGender": bride_gender,
            "groomAnimal": groom_animal,
            "groomYoniGender": groom_gender,
            "matrixOrientation": "male_row_female_column",
            "score": score,
        },
        points_awarded=score,
    )
