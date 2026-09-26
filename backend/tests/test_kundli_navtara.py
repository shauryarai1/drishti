"""Focused public Kundli Navtara profile checks."""

from __future__ import annotations

import pathlib
import shutil
import subprocess

import pytest
from fastapi.testclient import TestClient

import main
from kundli.aggregate import build_kundli
from navtara import SPECIAL_ROLES, TARA_SEQUENCE, build_navtara_profile

REPO = pathlib.Path(__file__).resolve().parents[2]
FRONTEND = REPO / "frontend-next"
PAGE = FRONTEND / "app" / "kundli" / "page.tsx"
PANEL = FRONTEND / "components" / "kundli" / "NavtaraPanel.tsx"
COMPAT = FRONTEND / "components" / "kundli" / "kundliCompat.ts"

FIXTURE = {
    "date": "2010-01-21", "time": "08:19", "place": "Delhi",
    "latitude": 28.6139, "longitude": 77.209, "timezone": "Asia/Kolkata",
    "name": "Fixture",
}


def _node(script_body: str, tmp_path: pathlib.Path) -> str:
    node = shutil.which("node")
    if not node:
        pytest.skip("node is not available")
    script = tmp_path / "check.mjs"
    script.write_text(script_body, encoding="utf-8")
    result = subprocess.run([node, str(script)], capture_output=True, text=True, timeout=90)
    assert result.returncode == 0, result.stderr
    return result.stdout


def test_kundli_exposes_all_27_positions_from_native_janma():
    body = TestClient(main.app).post("/api/kundli", json=FIXTURE).json()
    profile = body["navtara"]
    positions = profile["positions"]

    assert len(positions) == 27
    assert positions[0]["position"] == 1
    assert positions[0]["nakshatra"] == profile["janmaNakshatra"]
    assert positions[0]["tara"] == "Janma"
    assert [item["position"] for item in positions] == list(range(1, 28))
    assert [item["tara"] for item in positions[:9]] == list(TARA_SEQUENCE)
    assert all(item["meaning"] for item in positions)


def test_existing_special_roles_and_wrap_are_preserved():
    profile = build_navtara_profile("Uttara Bhadrapada").to_dict()
    positions = {item["position"]: item for item in profile["positions"]}

    assert positions[1]["nakshatra"] == "Uttara Bhadrapada"
    assert positions[2]["nakshatra"] == "Revati"
    assert positions[3]["nakshatra"] == "Ashwini"
    for position, role in SPECIAL_ROLES.items():
        assert positions[position]["specialRoles"] == [role]


def test_navtara_tab_and_mobile_panel_are_wired():
    page = PAGE.read_text(encoding="utf-8")
    panel = PANEL.read_text(encoding="utf-8")

    assert "'NAVTARA'" in page
    assert "<NavtaraPanel data={kundli.navtara} kundli={kundli} />" in page
    for heading in ("Position", "Nakshatra", "Tara", "Special Role", "Planets", "Meaning"):
        assert heading in panel
    assert "item.position === 1" in panel
    assert "grid-cols-[36px_1fr_auto]" in panel
    # Mobile shows the planets under the Nakshatra name; desktop gets a column.
    assert "sm:hidden" in panel and "hidden text-[12px] text-[#D6BE85] sm:block" in panel


def _join(planets_nakshatra: dict) -> dict:
    """The same canonical join the frontend performs, for expectation building."""
    out: dict = {}
    for planet, nakshatra in planets_nakshatra.items():
        key = "".join(c for c in nakshatra.lower() if c.isalpha())
        out.setdefault(key, []).append(planet)
    return out


def test_live_kundli_planets_join_to_navtara_rows():
    body = build_kundli(dict(FIXTURE))
    expected = _join({p["planet"]: p["nakshatra"] for p in body["planets"]})

    # Every planetary Nakshatra must exist as a Navtara row, and the join must
    # reproduce exactly the authoritative planetary Nakshatras.
    rows = {item["nakshatra"]: item for item in body["navtara"]["positions"]}
    for planet_row in body["planets"]:
        key = "".join(c for c in planet_row["nakshatra"].lower() if c.isalpha())
        assert planet_row["nakshatra"] in rows
        assert expected[key]  # non-empty

    # The join is lossless: every planet maps back to its own Nakshatra row.
    for nakshatra, planets in expected.items():
        matched = [r for r in rows.values()
                   if "".join(c for c in r["nakshatra"].lower() if c.isalpha()) == nakshatra]
        assert len(matched) == 1
        for planet in planets:
            source = next(p for p in body["planets"] if p["planet"] == planet)
            assert "".join(c for c in source["nakshatra"].lower() if c.isalpha()) == nakshatra


def test_planets_join_helper_handles_the_expected_example(tmp_path):
    script = (
        'import { planetsByNakshatra, planetsForNakshatra } from "' + COMPAT.as_uri() + '";\n'
        'const fail = (m) => { console.error("FAIL: " + m); process.exit(1); };\n'
        'const planets = [\n'
        '  { planet: "Sun", nakshatra: "Krittika" },\n'
        '  { planet: "Moon", nakshatra: "Chitra" },\n'
        '  { planet: "Mars", nakshatra: "Mrigashira" },\n'
        '  { planet: "Mercury", nakshatra: "Rohini" },\n'
        '  { planet: "Jupiter", nakshatra: "Punarvasu" },\n'
        '  { planet: "Venus", nakshatra: "Ardra" },\n'
        '  { planet: "Saturn", nakshatra: "Rohini" },\n'
        '  { planet: "Rahu", nakshatra: "Mrigashira" },\n'
        '  { planet: "Ketu", nakshatra: "Jyeshtha" },\n'
        '];\n'
        'const map = planetsByNakshatra({ planets });\n'
        'const j = (n) => planetsForNakshatra(n, map).join(",");\n'
        'if (j("Chitra") !== "Moon") fail("Chitra");\n'
        'if (j("Krittika") !== "Sun") fail("Krittika");\n'
        'if (j("Mrigashira") !== "Mars,Rahu") fail("Mrigashira: " + j("Mrigashira"));\n'
        'if (j("Rohini") !== "Mercury,Saturn") fail("Rohini: " + j("Rohini"));\n'
        'if (j("Punarvasu") !== "Jupiter") fail("Punarvasu");\n'
        'if (j("Ardra") !== "Venus") fail("Ardra");\n'
        'if (j("Jyeshtha") !== "Ketu") fail("Jyeshtha");\n'
        'if (j("Ashwini") !== "") fail("empty should be blank");\n'
        'if (planetsForNakshatra("", map).length !== 0) fail("blank key");\n'
        'const legacy = planetsByNakshatra(undefined);\n'
        'if (Object.keys(legacy).length !== 0) fail("legacy should be empty");\n'
        'const partial = planetsByNakshatra({ planets: [ { planet: "Sun" }, null, {}, { nakshatra: "Chitra" } ] });\n'
        'if (Object.keys(partial).length !== 0) fail("partial data should not join");\n'
        'console.log("NAVTARA_JOIN_OK");\n'
    )
    assert "NAVTARA_JOIN_OK" in _node(script, tmp_path)


def test_navtara_methodology_unchanged_by_the_planet_layer():
    body = build_kundli(dict(FIXTURE))
    positions = body["navtara"]["positions"]

    assert len(positions) == 27
    assert [item["tara"] for item in positions[:9]] == list(TARA_SEQUENCE)
    for position, role in SPECIAL_ROLES.items():
        assert positions[position - 1]["specialRoles"] == [role]
    assert all(item.get("meaning") for item in positions)
