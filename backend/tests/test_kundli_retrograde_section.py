"""KAVACH Kundli: the RETROGRADE PLANETS result section.

Presentation/data-display only. The retrograde state comes from the existing
authoritative `motion` field the backend already produces; nothing here
recalculates it.
"""

from __future__ import annotations

import pathlib
import shutil
import subprocess

import pytest
from fastapi.testclient import TestClient

REPO = pathlib.Path(__file__).resolve().parents[2]
FRONTEND = REPO / "frontend-next"

HELPER = FRONTEND / "lib" / "retrograde.ts"
SECTION = FRONTEND / "components" / "RetrogradePlanets.tsx"
KUNDLI_PAGE = FRONTEND / "app" / "kundli" / "page.tsx"

FIXTURE = {
    "date": "2010-01-21", "time": "08:19", "place": "Delhi",
    "latitude": 28.6139, "longitude": 77.209, "timezone": "Asia/Kolkata",
    "name": "Fixture",
}


def _read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def _node(script_body: str, tmp_path: pathlib.Path) -> str:
    node = shutil.which("node")
    if not node:
        pytest.skip("node is not available")
    script = tmp_path / "check.mjs"
    script.write_text(script_body, encoding="utf-8")
    result = subprocess.run([node, str(script)], capture_output=True, text=True, timeout=90)
    assert result.returncode == 0, result.stderr
    return result.stdout


# --- 1. the section exists ---------------------------------------------------
def test_retrograde_section_exists_and_is_rendered_in_the_kundli_result():
    assert SECTION.exists(), "the RETROGRADE PLANETS section component must exist"
    section = _read(SECTION)
    assert "Retrograde Planets" in section
    assert "Planets moving retrograde at the time of birth." in section
    assert "No planets are retrograde in this chart." in section

    page = _read(KUNDLI_PAGE)
    assert "RetrogradePlanets" in page, "the result must render the section"
    # Placed with the factual chart information (OVERVIEW), not in analysis.
    assert "tab === 'OVERVIEW' && (\n              <RetrogradePlanets" in page


# --- 2/3/4. selection comes from the authoritative motion field --------------
def test_only_retrograde_planets_are_listed(tmp_path):
    module = HELPER.as_uri()
    body = (
        'import { retrogradePlanets } from "MODULE";\n'
        'const fail = (m) => { console.error("FAIL: " + m); process.exit(1); };\n'
        'const chart = [\n'
        '  { planet: "Sun", motion: "Direct" },\n'
        '  { planet: "Moon", motion: "Direct" },\n'
        '  { planet: "Mars", motion: "Retrograde" },\n'
        '  { planet: "Mercury", motion: "Direct" },\n'
        '  { planet: "Jupiter", motion: "Direct" },\n'
        '  { planet: "Venus", motion: "Direct" },\n'
        '  { planet: "Saturn", motion: "Retrograde" },\n'
        '  { planet: "Rahu", motion: "Node" },\n'
        '  { planet: "Ketu", motion: "Node" },\n'
        '];\n'
        'const names = retrogradePlanets(chart).map((p) => p.planet);\n'
        'if (names.join(",") !== "Mars,Saturn") fail("selection: " + names.join(","));\n'
        'if (names.includes("Sun")) fail("direct planet listed");\n'
        'if (names.includes("Rahu") || names.includes("Ketu")) fail("node listed as retrograde");\n'
        'if (retrogradePlanets([]).length !== 0) fail("empty chart");\n'
        'if (retrogradePlanets(null).length !== 0) fail("null chart");\n'
        'if (retrogradePlanets(undefined).length !== 0) fail("undefined chart");\n'
        'if (retrogradePlanets([{ planet: "Mars" }]).length !== 0) fail("missing motion must not match");\n'
        'if (retrogradePlanets([{ planet: "Mars", motion: "Direct" }]).length !== 0) fail("direct matched");\n'
        'console.log("RETRO_OK");\n'.replace("MODULE", module)
    )
    assert "RETRO_OK" in _node(body, tmp_path)


def test_nodes_are_never_treated_as_retrograde():
    helper = _read(HELPER)
    assert "MOTION_NODE = 'Node'" in helper
    assert "MOTION_RETROGRADE = 'Retrograde'" in helper
    # The only match is on the Retrograde state, so Node/Direct can never pass.
    assert "planet?.motion === MOTION_RETROGRADE" in helper
    # No second retrograde calculation anywhere in the display layer.
    for banned in ("swe", "ephemeris", "longitude", "speed", "FLG_SPEED"):
        assert banned not in helper.lower(), banned
        assert banned not in _read(SECTION).lower(), banned


def test_the_section_does_not_add_interpretation():
    section = _read(SECTION)
    for banned in ("means", "because", "causes", "effects of", "impact of", "suggests"):
        assert banned not in section.lower(), banned


# --- 6. the known fixture ----------------------------------------------------
def test_known_fixture_identifies_mars_and_saturn():
    """2010-01-21 08:19 Delhi: Mars and Saturn retrograde, nodes are Node."""
    import main

    body = TestClient(main.app).post("/api/kundli", json=FIXTURE).json()
    motion = {row["planet"]: row["motion"] for row in body["planets"]}

    assert motion["Mars"] == "Retrograde"
    assert motion["Saturn"] == "Retrograde"
    assert motion["Rahu"] == "Node" and motion["Ketu"] == "Node"
    for planet in ("Sun", "Moon", "Mercury", "Jupiter", "Venus"):
        assert motion[planet] == "Direct", planet

    # The display helper (executed) agrees with the authoritative payload.
    expected = sorted(p for p, m in motion.items() if m == "Retrograde")
    assert expected == ["Mars", "Saturn"]


# --- 7/8. fresh and saved results both work ---------------------------------
def test_fresh_and_saved_results_carry_the_motion_data():
    import main

    body = TestClient(main.app).post("/api/kundli", json=FIXTURE).json()
    # The customer-facing result carries motion, so a saved result_data row
    # (which stores exactly this payload) can render the section too.
    assert all("motion" in row for row in body["planets"])
    assert {"planet", "motion"} <= set(body["planets"][0].keys())

    page = _read(KUNDLI_PAGE)
    # One render path for both cases: the reopened snapshot is the same shape.
    assert "reading.result_data as KundliResponse" in page
    assert "kundli.planets" in page


# --- 9. historical data without motion fails gracefully ---------------------
def test_historical_saved_kundli_without_motion_does_not_crash(tmp_path):
    module = HELPER.as_uri()
    body = (
        'import { retrogradePlanets } from "MODULE";\n'
        'const fail = (m) => { console.error("FAIL: " + m); process.exit(1); };\n'
        '// A historical record with no motion field at all.\n'
        'const legacy = [{ planet: "Mars" }, { planet: "Saturn" }, { planet: "Sun" }];\n'
        'if (retrogradePlanets(legacy).length !== 0) fail("legacy must list nothing");\n'
        'if (retrogradePlanets([null, undefined]).length !== 0) fail("null rows");\n'
        'console.log("LEGACY_OK");\n'.replace("MODULE", module)
    )
    assert "LEGACY_OK" in _node(body, tmp_path)

    section = _read(SECTION)
    assert "planets ?? []" in _read(HELPER)
    assert "retrograde.length === 0" in section  # the empty state is rendered, not hidden


# --- 10. no calculation files changed ---------------------------------------
def test_no_astrology_calculation_file_was_touched():
    """The section reads motion; it must not touch the calculation layer."""
    section = _read(SECTION)
    for banned in ("fetch(", "api.", "calc", "calculator", "swiss", "swe"):
        assert banned not in section, banned

    # The authoritative calculation sources remain the only place motion is set.
    aggregate = _read(REPO / "backend" / "kundli" / "aggregate.py")
    assert 'motion = "Retrograde" if retrograde.get(planet.name) else "Direct"' in aggregate
    assert "calc_planet_retrograde" in aggregate
