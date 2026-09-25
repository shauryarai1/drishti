"""Focused Kundli chart presentation and Transit reliability checks."""

from __future__ import annotations

import pathlib

from fastapi.testclient import TestClient

import main
from kundli.nakshatra import nakshatra_of

REPO = pathlib.Path(__file__).resolve().parents[2]
FRONTEND = REPO / "frontend-next"
CHART = FRONTEND / "components" / "NorthIndianChart.tsx"
KUNDLI = FRONTEND / "components" / "Kundli.tsx"
CHARTS = FRONTEND / "components" / "kundli" / "KundliCharts.tsx"
KUNDLI_PAGE = FRONTEND / "app" / "kundli" / "page.tsx"
KUNDLI_LIB = FRONTEND / "lib" / "kundli.ts"

FIXTURE = {
    "date": "2010-01-21", "time": "08:19", "place": "Delhi",
    "latitude": 28.6139, "longitude": 77.209, "timezone": "Asia/Kolkata",
    "name": "Fixture",
}


def read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def test_ascendant_nakshatra_uses_authoritative_longitude():
    body = TestClient(main.app).post("/api/kundli", json=FIXTURE).json()
    ascendant = body["chart"]["ascendant"]
    expected = nakshatra_of(ascendant["longitude"])

    assert ascendant["nakshatra"] == expected["name"]
    assert ascendant["pada"] == expected["pada"]
    assert ascendant["nakshatraLord"] == expected["lord"]
    assert body["summary"]["ascendantNakshatra"] == expected["name"]
    assert body["summary"]["ascendantPada"] == expected["pada"]


def test_frontend_renders_ascendant_nakshatra_without_recalculating():
    page = read(KUNDLI_PAGE)
    lib = read(KUNDLI_LIB)

    assert "Ascendant Nakshatra" in page
    assert "kundli.chart.ascendant.nakshatra" in page
    assert "ascendantNakshatra" in lib
    assert "nakshatra_of" not in page.lower()


def test_chart_uses_real_degree_and_motion_fields():
    lib = read(KUNDLI_LIB)
    component = read(KUNDLI)

    assert "isRetrograde: Boolean(position?.isRetrograde)" in component
    assert "degreeInSign: Number.parseFloat(position?.degree || '0')" in component
    assert "degree: `${planet.degree.toFixed(2)}`" in lib
    assert "Math.floor(planet.degreeInSign)" in read(CHART)


def test_chart_presentation_is_mobile_readable_white_and_red():
    chart = read(CHART)
    wrapper = read(CHARTS)
    kundli = read(KUNDLI)

    assert "max-w-[680px]" in chart
    assert "aspect-[0.862]" in chart
    assert "preserveAspectRatio=\"none\"" in chart
    assert "bg-white" in chart
    assert "#B4232F" in chart
    assert "#ffffff" in chart
    assert "kundli-degree-text" in chart
    assert "linearGradient" not in chart
    assert "feDropShadow" not in chart
    assert "H{poly.houseNum}" not in chart
    assert "Rashi Sign No." not in chart
    assert "LAGNA (1)" not in chart
    assert "-mx-3" in wrapper
    assert "w-[calc(100%+1.5rem)]" in wrapper
    assert "rounded-xl border" not in kundli


def test_planet_slots_are_deterministic_and_compact():
    chart = read(CHART)
    assert "HOUSE_SAFE_SLOTS" in chart
    assert "1:" in chart and "12:" in chart
    assert "[-30, -15], [30, -15]" in chart
    assert "[-28, -25], [28, -25]" in chart
    assert "safe.length" in chart


def test_transit_request_has_bounded_retry_and_timeout():
    lib = read(KUNDLI_LIB)
    page = read(KUNDLI_PAGE)

    assert "TRANSIT_TIMEOUT_MS = 10000" in lib
    assert "while (attempt < 2)" in lib
    assert "status === 429 || status >= 500" in lib
    assert "signal: controller.signal" in lib
    assert "setTransitLoading" in page
    assert "Transit data couldn&apos;t be loaded." in page
    assert "Retry" in page
    assert "loadId !== loadIdRef.current" in page
