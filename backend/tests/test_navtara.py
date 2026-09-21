"""Exhaustive tests for the PRIVATE Navtara foundation (deterministic)."""

from __future__ import annotations

import pathlib

import pytest

from navtara import (
    CAUTION_TARAS,
    FORBIDDEN_PUBLIC_CLAIMS,
    FORBIDDEN_PUBLIC_TERMS,
    NAKSHATRAS,
    SPECIAL_ROLES,
    TARA_MEANINGS,
    TARA_SEQUENCE,
    build_navtara_profile,
    get_navtara,
    get_special_roles,
    get_tara_from_position,
    relative_nakshatra_position,
)

ASHWINI_EXPECTED = [
    ("Ashwini", "Janma", []), ("Bharani", "Sampat", []), ("Krittika", "Vipat", []),
    ("Rohini", "Kshema", ["Jati"]), ("Mrigashira", "Pratyari", []),
    ("Ardra", "Sadhaka", []), ("Punarvasu", "Vadha", []), ("Pushya", "Mitra", []),
    ("Ashlesha", "AtiMitra", []), ("Magha", "Janma", ["Karma"]),
    ("Purva Phalguni", "Sampat", []), ("Uttara Phalguni", "Vipat", ["Desha"]),
    ("Hasta", "Kshema", ["Abhisheka"]), ("Chitra", "Pratyari", []),
    ("Swati", "Sadhaka", []), ("Vishakha", "Vadha", ["Sanghatika"]),
    ("Anuradha", "Mitra", []), ("Jyeshtha", "AtiMitra", ["Samudaya"]),
    ("Mula", "Janma", ["Adhana"]), ("Purva Ashadha", "Sampat", []),
    ("Uttara Ashadha", "Vipat", []), ("Shravana", "Kshema", []),
    ("Dhanishta", "Pratyari", []), ("Shatabhisha", "Sadhaka", []),
    ("Purva Bhadrapada", "Vadha", []), ("Uttara Bhadrapada", "Mitra", []),
    ("Revati", "AtiMitra", []),
]


# --- canonical order ------------------------------------------------------
def test_canonical_order():
    assert len(NAKSHATRAS) == 27
    assert NAKSHATRAS[0] == "Ashwini"
    assert NAKSHATRAS[1] == "Bharani"
    assert NAKSHATRAS[5] == "Ardra"
    assert NAKSHATRAS[13] == "Chitra"
    assert NAKSHATRAS[26] == "Revati"
    assert len(set(NAKSHATRAS)) == 27


# --- relative counting ----------------------------------------------------
def test_relative_position_of_janma_is_one():
    assert relative_nakshatra_position("Ashwini", "Ashwini") == 1
    assert relative_nakshatra_position("Uttara Bhadrapada", "Uttara Bhadrapada") == 1


def test_relative_position_wraps():
    assert relative_nakshatra_position("Revati", "Ashwini") == 2
    assert relative_nakshatra_position("Uttara Bhadrapada", "Ashwini") == 3
    assert relative_nakshatra_position("Ashwini", "Revati") == 27


# --- nine-tara mapping ----------------------------------------------------
@pytest.mark.parametrize("positions,tara", [
    ((1, 10, 19), "Janma"), ((2, 11, 20), "Sampat"), ((3, 12, 21), "Vipat"),
    ((4, 13, 22), "Kshema"), ((5, 14, 23), "Pratyari"), ((6, 15, 24), "Sadhaka"),
    ((7, 16, 25), "Vadha"), ((8, 17, 26), "Mitra"), ((9, 18, 27), "AtiMitra"),
])
def test_tara_pattern(positions, tara):
    for position in positions:
        assert get_tara_from_position(position) == tara


def test_caution_taras():
    assert CAUTION_TARAS == ("Vipat", "Pratyari", "Vadha")
    assert get_navtara("Ashwini", "Krittika")["isCaution"] is True
    assert get_navtara("Ashwini", "Pushya")["isCaution"] is False


# --- special roles --------------------------------------------------------
def test_special_role_positions():
    assert SPECIAL_ROLES == {4: "Jati", 10: "Karma", 12: "Desha", 13: "Abhisheka",
                             16: "Sanghatika", 18: "Samudaya", 19: "Adhana"}
    assert get_special_roles(4) == ["Jati"]
    assert get_special_roles(5) == []
    assert get_special_roles(19) == ["Adhana"]


def test_multiple_roles_coexist():
    profile = build_navtara_profile("Ashwini").by_position()
    assert profile[4].tara == "Kshema" and profile[4].special_roles == ["Jati"]
    assert profile[10].tara == "Janma" and profile[10].special_roles == ["Karma"]
    assert profile[12].tara == "Vipat" and profile[12].special_roles == ["Desha"]
    assert profile[16].tara == "Vadha" and profile[16].special_roles == ["Sanghatika"]
    assert profile[18].tara == "AtiMitra" and profile[18].special_roles == ["Samudaya"]


# --- reference table: Janma = Ashwini -------------------------------------
def test_ashwini_reference_table():
    profile = build_navtara_profile("Ashwini")
    assert len(profile.positions) == 27
    for item, (nakshatra, tara, roles) in zip(profile.positions, ASHWINI_EXPECTED):
        assert item.nakshatra == nakshatra
        assert item.tara == tara
        assert item.special_roles == roles


# --- wrap-around: Janma = Uttara Bhadrapada -------------------------------
def test_uttara_bhadrapada_wrap_around():
    profile = build_navtara_profile("Uttara Bhadrapada")
    head = [(item.nakshatra, item.tara) for item in profile.positions[:10]]
    # Inclusive counting from Uttara Bhadrapada (position -> nakshatra):
    #  1 Uttara Bhadrapada  2 Revati      3 Ashwini      4 Bharani   5 Krittika
    #  6 Rohini             7 Mrigashira  8 Ardra        9 Punarvasu 10 Pushya
    assert head == [
        ("Uttara Bhadrapada", "Janma"), ("Revati", "Sampat"), ("Ashwini", "Vipat"),
        ("Bharani", "Kshema"), ("Krittika", "Pratyari"), ("Rohini", "Sadhaka"),
        ("Mrigashira", "Vadha"), ("Ardra", "Mitra"), ("Punarvasu", "AtiMitra"),
        ("Pushya", "Janma"),
    ]
    assert profile.positions[0].special_roles == []
    assert profile.positions[3].special_roles == ["Jati"]
    assert profile.positions[9].special_roles == ["Karma"]
    assert profile.positions[-1].position == 27


# --- exhaustive: every possible Janma Nakshatra ---------------------------
@pytest.mark.parametrize("janma", NAKSHATRAS)
def test_every_janma_produces_a_valid_profile(janma):
    profile = build_navtara_profile(janma)
    assert len(profile.positions) == 27
    assert [item.position for item in profile.positions] == list(range(1, 28))
    assert {item.nakshatra for item in profile.positions} == set(NAKSHATRAS)
    assert profile.positions[0].nakshatra == janma
    assert profile.positions[0].tara == "Janma"

    counts = {tara: 0 for tara in TARA_SEQUENCE}
    for item in profile.positions:
        counts[item.tara] += 1
    assert all(count == 3 for count in counts.values())

    for position, role in SPECIAL_ROLES.items():
        assert profile.positions[position - 1].special_roles == [role]


def test_all_729_pairs_map_correctly():
    seen = 0
    for janma in NAKSHATRAS:
        houses = set()
        for target in NAKSHATRAS:
            info = get_navtara(janma, target)
            assert 1 <= info["position"] <= 27
            assert info["tara"] in TARA_SEQUENCE
            houses.add(info["position"])
            seen += 1
        assert houses == set(range(1, 28))
    assert seen == 27 * 27


# --- privacy / safety of the structure -----------------------------------
def test_meanings_never_contain_forbidden_public_claims():
    # Only rendered public text matters (internal notes legitimately say
    # "never predict death").
    rendered = []
    for entry in TARA_MEANINGS.values():
        rendered.extend(entry.get("public_tone", []))
        rendered.extend(entry.get("themes", []))
        rendered.append(str(entry.get("about", "")))
    blob = " ".join(rendered).lower()
    for banned in FORBIDDEN_PUBLIC_CLAIMS:
        assert banned not in blob, banned


def test_vadha_is_marked_strong_caution_with_safe_tone():
    vadha = TARA_MEANINGS["Vadha"]
    assert vadha["nature"] == "strong_caution"
    tone = " ".join(vadha["public_tone"]).lower()
    assert "strong caution" in tone
    assert "death" not in tone


def test_mitra_and_ati_mitra_directions_are_opposite():
    assert TARA_MEANINGS["Mitra"]["direction"] == "native_to_others"
    assert TARA_MEANINGS["AtiMitra"]["direction"] == "others_to_native"


def test_forbidden_public_terms_cover_the_mechanism():
    for term in ("navtara", "vipat tara", "vadha tara", "sanghatika nakshatra", "1/10/19"):
        assert term in FORBIDDEN_PUBLIC_TERMS


def test_navtara_is_not_wired_into_any_public_route():
    root = pathlib.Path(__file__).resolve().parents[1]
    main_source = (root / "main.py").read_text(encoding="utf-8").lower()
    assert "navtara" not in main_source
    assert "daily" in main_source  # /daily remains the public daily feature


def test_no_planet_rules_were_invented():
    root = pathlib.Path(__file__).resolve().parents[1] / "navtara"
    for path in root.glob("*.py"):
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith('"""'):
                continue
            lowered = stripped.lower()
            for forbidden in ("benefic", "malefic", "exalt", "debilit", "planet_rules",
                              "aspect_rules", "friendship"):
                assert forbidden not in lowered, f"{path.name}: {stripped}"


def test_no_ai_or_network_in_navtara():
    root = pathlib.Path(__file__).resolve().parents[1] / "navtara"
    for path in root.glob("*.py"):
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith(("import ", "from ")):
                lowered = stripped.lower()
                for forbidden in ("gemini", "httpx", "requests", "openai", "urllib", "socket"):
                    assert forbidden not in lowered, f"{path.name}: {stripped}"
