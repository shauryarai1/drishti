"""Focused public Kundli Navtara profile checks."""

from __future__ import annotations

import pathlib

from fastapi.testclient import TestClient

import main
from navtara import SPECIAL_ROLES, TARA_SEQUENCE, build_navtara_profile

REPO = pathlib.Path(__file__).resolve().parents[2]
PAGE = REPO / "frontend-next" / "app" / "kundli" / "page.tsx"
PANEL = REPO / "frontend-next" / "components" / "kundli" / "NavtaraPanel.tsx"

FIXTURE = {
    "date": "2010-01-21", "time": "08:19", "place": "Delhi",
    "latitude": 28.6139, "longitude": 77.209, "timezone": "Asia/Kolkata",
    "name": "Fixture",
}


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
    assert "<NavtaraPanel data={kundli.navtara}" in page
    for heading in ("Position", "Nakshatra", "Tara", "Special Role", "Meaning"):
        assert heading in panel
    assert "item.position === 1" in panel
    assert "grid-cols-[36px_1fr_auto]" in panel
