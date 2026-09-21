"""Current Dasha Reading tests: lord mapping, synthesis, privacy, determinism."""

from __future__ import annotations

import json
import pathlib
import re

import pytest
from fastapi.testclient import TestClient

import main
from dasha_reading import (
    LORD_NAKSHATRAS,
    build_current_dasha_reading,
    build_private_current_dasha,
    get_lord_nakshatras,
)
from dasha_reading.public import render_reading
from navtara import NAKSHATRAS

FIXTURE = {"date": "1990-05-15", "time": "14:15", "place": "New Delhi, India",
           "latitude": 28.6139, "longitude": 77.209, "timezone": "Asia/Kolkata"}

PRIVATE_TERMS = ("navtara", "navatara", "tara", "sampat", "vipat", "kshema", "pratyari",
                 "sadhaka", "vadha", "mitra", "atimitra", "ati-mitra", "relativeposition",
                 "relative_position", "taranumber", "tara_number", "janmanakshatra",
                 "lordnakshatras", "specialroles", "nakshatra")

LORDS = ("Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury")


# --- 9-lord -> 27-Nakshatra mapping --------------------------------------
@pytest.mark.parametrize("lord", LORDS)
def test_each_lord_has_exactly_three_canonical_nakshatras(lord):
    group = get_lord_nakshatras(lord)
    assert len(group) == 3
    assert len(set(group)) == 3
    for nakshatra in group:
        assert nakshatra in NAKSHATRAS


def test_all_nine_groups_cover_all_27_exactly_once():
    grouped = [nakshatra for lord in LORDS for nakshatra in get_lord_nakshatras(lord)]
    assert len(grouped) == 27
    assert sorted(grouped) == sorted(NAKSHATRAS)
    assert set(LORD_NAKSHATRAS) == set(LORDS)


def test_groups_are_in_canonical_order():
    assert get_lord_nakshatras("Saturn") == ["Pushya", "Anuradha", "Uttara Bhadrapada"]
    assert get_lord_nakshatras("Jupiter") == ["Punarvasu", "Vishakha", "Purva Bhadrapada"]
    assert get_lord_nakshatras("Mercury") == ["Ashlesha", "Jyeshtha", "Revati"]


# --- fixture: private reading --------------------------------------------
def test_fixture_private_reading_shape():
    private = build_private_current_dasha(FIXTURE, as_of="2026-09-21T12:00:00+05:30")
    assert private["janmaNakshatra"] in NAKSHATRAS
    assert private["mahadasha"]["lord"] in LORDS
    assert private["antardasha"]["lord"] in LORDS
    assert private["mahadasha"]["start"] <= private["asOf"] < private["mahadasha"]["end"]
    assert len(private["lordNakshatras"]) == 3
    for item in private["lordNakshatras"]:
        assert item["nakshatra"] in get_lord_nakshatras(private["mahadasha"]["lord"])
        assert item["tara"] and item["taraNumber"] and item["relativePosition"]


def test_fixture_uses_existing_dasha_engine_values():
    from kundli.dasha import vimshottari_dasha
    private = build_private_current_dasha(FIXTURE, as_of="2026-09-21T12:00:00+05:30")
    assert private["mahadasha"]["lord"] == "Rahu"          # verified Kundli fixture
    assert private["mahadasha"]["start"].startswith("2011-01-28")


# --- synthesis ------------------------------------------------------------
def _private(taras):
    return {
        "janmaNakshatra": "Ashwini",
        "asOf": "2026-09-21T12:00:00+05:30",
        "timezone": "Asia/Kolkata",
        "mahadasha": {"lord": "Saturn", "start": "2020-01-01", "end": "2039-01-01"},
        "antardasha": {"lord": "Mercury", "start": "2026-01-01", "end": "2028-01-01"},
        "lordNakshatras": [{"nakshatra": f"T{i}", "tara": tara, "taraNumber": i + 1,
                            "relativePosition": i + 1, "nature": "n/a"}
                           for i, tara in enumerate(taras)],
    }


def test_all_supportive_is_not_scored_or_labelled():
    public = render_reading(_private(["Sampat", "Sadhaka", "AtiMitra"]))
    assert public["supports"]
    assert public["care"] == []
    blob = json.dumps(public).lower()
    for banned in ("score", "percent", "%", "good dasha", "bad dasha", "positive", "negative",
                   "rating", "marks", "grade"):
        assert banned not in blob, banned


def test_caution_does_not_erase_support_and_vice_versa():
    public = render_reading(_private(["Sampat", "Sadhaka", "Pratyari"]))
    assert public["supports"] and public["care"]
    summary = public["summary"].lower()
    assert "resource" in summary or "practical" in summary
    assert "resistance" in summary or "patience" in summary or "friction" in summary
    assert public["headline"] == "Progress With Patience"


def test_multiple_caution_classifications_are_kept_separate():
    public = render_reading(_private(["Vipat", "Vadha", "Pratyari"]))
    assert len(public["care"]) == 3
    assert public["supports"] == []
    assert public["headline"] == "A Demanding Phase That Rewards Care"


def test_janma_is_self_oriented_not_scored():
    public = render_reading(_private(["Janma", "Janma", "Janma"]))
    assert public["supports"]
    assert public["care"] == []
    assert "own state" in json.dumps(public).lower() or "personal" in public["guidance"].lower()


def test_mitra_and_ati_mitra_keep_their_directions():
    given = render_reading(_private(["Mitra", "Mitra", "Mitra"]))
    received = render_reading(_private(["AtiMitra", "AtiMitra", "AtiMitra"]))
    assert "support and cooperate" in given["supports"][0].lower()
    assert "from other people" in received["supports"][0].lower()
    assert given["headline"] != received["headline"]


def test_vadha_uses_safe_language_and_no_fear():
    public = render_reading(_private(["Vadha", "Vadha", "Vadha"]))
    blob = json.dumps(public).lower()
    for banned in ("death", "fatal", "disaster", "dangerous", "killed", "guaranteed",
                   "will lose", "will become rich", "bad dasha"):
        assert banned not in blob, banned
    assert "care" in blob


def test_determinism():
    first = json.dumps(render_reading(_private(["Sampat", "Sadhaka", "Pratyari"])), sort_keys=True)
    second = json.dumps(render_reading(_private(["Sampat", "Sadhaka", "Pratyari"])), sort_keys=True)
    assert first == second


# --- public endpoint ------------------------------------------------------
def test_endpoint_returns_customer_safe_reading():
    response = TestClient(main.app).post("/api/current-dasha-reading", json={
        "birth": FIXTURE, "asOf": "2026-09-21T12:00:00+05:30"})
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"asOf", "timezone", "mahadasha", "antardasha", "headline",
                         "summary", "supports", "care", "guidance", "methodologyVersion"}
    assert body["mahadasha"]["name"] and body["mahadasha"]["start"]
    assert body["antardasha"]["name"]
    assert body["headline"] and body["summary"] and body["guidance"]


def test_endpoint_privacy_regression():
    body = TestClient(main.app).post("/api/current-dasha-reading", json={
        "birth": FIXTURE, "asOf": "2026-09-21T12:00:00+05:30"}).json()
    blob = json.dumps(body).lower()
    for term in PRIVATE_TERMS:
        assert term not in blob, term

    def keys(node):
        found = set()
        if isinstance(node, dict):
            for key, value in node.items():
                found.add(str(key).lower())
                found |= keys(value)
        elif isinstance(node, list):
            for item in node:
                found |= keys(item)
        return found

    present = keys(body)
    for banned in ("tara", "lordnakshatras", "janmanakshatra", "relativeposition",
                   "taranumber", "navtara", "specialroles"):
        assert banned not in present, banned


def test_endpoint_rejects_bad_input_cleanly():
    response = TestClient(main.app).post("/api/current-dasha-reading", json={
        "birth": {**FIXTURE, "time": "99:99"}})
    assert response.status_code == 400
    assert "couldn't prepare" in response.json()["message"].lower()
    assert "traceback" not in json.dumps(response.json()).lower()


# --- scope guards ---------------------------------------------------------
def test_no_forbidden_inputs_are_used():
    root = pathlib.Path(__file__).resolve().parents[1] / "dasha_reading"
    for path in root.glob("*.py"):
        source = re.sub(r'""".*?"""', "", path.read_text(encoding="utf-8"), flags=re.S)
        for line in source.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            lowered = stripped.lower()
            for forbidden in ("transit", "house", "aspect", "dignity", "shadbala",
                              "friendship", "tarot", "gemini", "random", "weekly",
                              "daily", "interpretation"):
                assert forbidden not in lowered, f"{path.name}: {stripped}"


def test_life_summary_five_rules_untouched():
    root = pathlib.Path(__file__).resolve().parents[1]
    summary = (root / "life_summary" / "knowledge.py").read_text(encoding="utf-8")
    for key in ("personality", "relationships", "professional", "subconscious", "problems"):
        assert key in summary
    main_source = (root / "main.py").read_text(encoding="utf-8")
    assert "/api/current-dasha-reading" in main_source
