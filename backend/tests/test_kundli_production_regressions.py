"""Focused production-regression tests for the Kundli UI fixes.

These exercise real runtime behaviour (Node executes the exported geometry and
compatibility modules) plus the authoritative API payload. They guard against
the dense-house collision, the Navtara legacy-snapshot crash, the missing
Ascendant Nakshatra and the saved-snapshot transit regression.
"""

from __future__ import annotations

import pathlib
import shutil
import subprocess

import pytest
from fastapi.testclient import TestClient

import main

REPO = pathlib.Path(__file__).resolve().parents[2]
FRONTEND = REPO / "frontend-next"
GEOMETRY = FRONTEND / "components" / "kundli" / "chartGeometry.ts"
COMPAT = FRONTEND / "components" / "kundli" / "kundliCompat.ts"
CHARTS = FRONTEND / "components" / "kundli" / "KundliCharts.tsx"
PAGE = FRONTEND / "app" / "kundli" / "page.tsx"
PANEL = FRONTEND / "components" / "kundli" / "NavtaraPanel.tsx"

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


GEOMETRY_HARNESS = """
import { HOUSE_GEOMETRY, planetSlots, LABEL_BOX, RASHI_BOX } from "MODULE";
const W = LABEL_BOX.width, H = LABEL_BOX.height;
function inside(p, poly){const [x,y]=p;let c=false;for(let i=0,j=poly.length-1;i<poly.length;j=i++){const [xi,yi]=poly[i],[xj,yj]=poly[j];if(((yi>y)!==(yj>y))&&(x<(xj-xi)*(y-yi)/(yj-yi)+xi))c=!c;}return c;}
function distEdge(p, poly){let b=1e9;for(let i=0;i<poly.length;i++){const [x1,y1]=poly[i],[x2,y2]=poly[(i+1)%poly.length];const dx=x2-x1,dy=y2-y1;const t=Math.max(0,Math.min(1,((p[0]-x1)*dx+(p[1]-y1)*dy)/(dx*dx+dy*dy)));const px=x1+t*dx,py=y1+t*dy;b=Math.min(b,Math.hypot(p[0]-px,p[1]-py));}return b;}
function boxCorners(x,y){return [[x-W/2,y-H/2],[x+W/2,y-H/2],[x-W/2,y+H/2],[x+W/2,y+H/2],[x,y],[x,y-H/2],[x,y+H/2],[x-W/2,y],[x+W/2,y]];}
function disjoint(a,b){return Math.abs(a[0]-b[0])>=W || Math.abs(a[1]-b[1])>=H;}
let failures=[];
for (const [key, geo] of Object.entries(HOUSE_GEOMETRY)) {
  for (let count=1; count<=7; count++) {
    const slots = planetSlots(Number(key), count);
    if (slots.length !== count) { failures.push(`${key}: expected ${count} slots`); continue; }
    for (const s of slots) {
      for (const c of boxCorners(s[0], s[1])) {
        if (!inside(c, geo.points)) failures.push(`${key}/${count}: corner outside polygon`);
        if (distEdge(c, geo.points) < 1.5) failures.push(`${key}/${count}: label crosses a line`);
      }
      if (Math.abs(s[0]-geo.rashi[0]) < (W+RASHI_BOX.width)/2 && Math.abs(s[1]-geo.rashi[1]) < (H+RASHI_BOX.height)/2) {
        failures.push(`${key}/${count}: label overlaps sign number`);
      }
    }
    for (let i=0;i<slots.length;i++) for (let j=i+1;j<slots.length;j++) {
      if (!disjoint(slots[i], slots[j])) failures.push(`${key}/${count}: labels ${i}/${j} overlap`);
    }
  }
}
if (failures.length) { console.error(failures.join("\\n")); process.exit(1); }
console.log("GEOMETRY_OK");
""".replace("MODULE", GEOMETRY.as_uri())


def test_dense_house_geometry_never_collides(tmp_path):
    assert "GEOMETRY_OK" in _node(GEOMETRY_HARNESS, tmp_path)


def test_compat_handles_legacy_snapshots(tmp_path):
    script = (
        'import { hasNavtara, navtaraRows, ascendantNakshatraView, mergeAdditiveFields } from "'
        + COMPAT.as_uri() + '";\n'
        'const fail = (m) => { console.error("FAIL: " + m); process.exit(1); };\n'
        'if (hasNavtara(undefined) || hasNavtara(null) || hasNavtara({})) fail("hasNavtara legacy");\n'
        'if (navtaraRows(undefined).length !== 0) fail("rows undefined");\n'
        'const rows = navtaraRows({ positions: [{ position: 1, nakshatra: "Ashwini", tara: "Janma" }] });\n'
        'if (rows.length !== 1 || rows[0].tara !== "Janma" || rows[0].specialRoles.length !== 0) fail("row normalise");\n'
        'const legacy = { summary: { lagnaRashi: "Virgo" }, chart: { ascendant: { rashi: "Virgo", degree: 5, longitude: 160 }, planets: [{ planet: "Sun" }], houses: [] }, dasha: { balanceAtBirth: { lord: "Ketu", years: 1 } } };\n'
        'const view = ascendantNakshatraView(legacy);\n'
        'if (view.available !== false || view.rashi !== "Virgo") fail("asc legacy available");\n'
        'const fresh = { summary: { ascendantNakshatra: "Hasta", ascendantPada: 2, ascendantNakshatraLord: "Moon" }, chart: { ascendant: { nakshatra: "Hasta", pada: 2, nakshatraLord: "Moon" } }, dasha: { currentPrana: { lord: "Moon" } }, navtara: { janmaNakshatra: "Hasta", positions: [{ position: 1 }] } };\n'
        'const merged = mergeAdditiveFields(legacy, fresh);\n'
        'if (merged.chart.planets[0].planet !== "Sun") fail("historical planets changed");\n'
        'if (merged.chart.ascendant.rashi !== "Virgo" || merged.chart.ascendant.longitude !== 160) fail("historical ascendant changed");\n'
        'if (merged.chart.ascendant.nakshatra !== "Hasta") fail("additive asc nakshatra missing");\n'
        'if (merged.summary.ascendantNakshatra !== "Hasta") fail("additive summary missing");\n'
        'if (!merged.navtara || merged.navtara.janmaNakshatra !== "Hasta") fail("additive navtara missing");\n'
        'if (!merged.dasha.currentPrana) fail("additive dasha missing");\n'
        'if (merged.dasha.balanceAtBirth.lord !== "Ketu") fail("historical dasha changed");\n'
        'const view2 = ascendantNakshatraView(merged);\n'
        'if (!view2.available || view2.pada !== "2") fail("asc after merge");\n'
        'console.log("COMPAT_OK");\n'
    )
    assert "COMPAT_OK" in _node(script, tmp_path)


def test_new_kundli_has_ascendant_nakshatra_and_navtara():
    body = TestClient(main.app).post("/api/kundli", json=FIXTURE).json()

    ascendant = body["chart"]["ascendant"]
    assert ascendant["nakshatra"] and ascendant["nakshatraLord"]
    assert isinstance(ascendant["pada"], int)
    assert body["summary"]["ascendantNakshatra"] == ascendant["nakshatra"]
    assert len(body["navtara"]["positions"]) == 27
    assert body["navtara"]["positions"][0]["position"] == 1


def test_navtara_panel_is_legacy_safe():
    panel = PANEL.read_text(encoding="utf-8")
    assert "hasNavtara(data)" in panel
    assert "navtaraRows(data)" in panel
    assert "data.positions.map" not in panel

    page = PAGE.read_text(encoding="utf-8")
    assert "<PanelBoundary label=\"Navtara\">" in page
    assert "<NavtaraPanel data={kundli.navtara} />" in page
    assert "PanelBoundary" in page  # other optional panels are protected too


def test_saved_snapshot_load_fills_additive_fields_and_transits():
    page = PAGE.read_text(encoding="utf-8")
    assert "mergeAdditiveFields(" in page
    assert "void loadTransits(payload, loadId);" in page


def test_moon_chart_removed_from_charts_tab():
    charts = CHARTS.read_text(encoding="utf-8")
    assert "Moon Chart" not in charts
    assert "'MOON'" not in charts
    assert "moonChartToKundliData" not in charts
    assert "Lagna Chart" in charts
