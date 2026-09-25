"""Focused five-level Vimshottari hierarchy and drill-down contracts."""

from __future__ import annotations

import datetime as dt
import pathlib
import re
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

import main
from kundli.dasha import DASHA_LEVELS, ORDER, YEARS, dasha_children, vimshottari_dasha
from kundli.nakshatra import nakshatra_of

REPO = pathlib.Path(__file__).resolve().parents[2]
PAGE = REPO / "frontend-next" / "app" / "kundli" / "page.tsx"
FLOW = REPO / "frontend-next" / "components" / "kundli" / "DashaFlow.tsx"


def stamps(value: str) -> dt.datetime:
    return dt.datetime.fromisoformat(value)


def assert_covered(level: int, lord: str, start: str, end: str) -> list[dict]:
    children = dasha_children(level, lord, start, end)
    assert children[0]["start"] == start
    assert children[-1]["end"] == end
    for previous, current in zip(children, children[1:]):
        assert previous["end"] == current["start"]
    assert stamps(children[-1]["end"]) - stamps(children[0]["start"]) == stamps(end) - stamps(start)
    return children


def test_recursive_children_cover_exactly_through_prana():
    start = "2020-01-01T00:00:00+05:30"
    end = "2039-01-01T00:00:00+05:30"
    parent_lord = "Saturn"

    for level in range(1, 5):
        children = assert_covered(level, parent_lord, start, end)
        parent_lord = children[3]["lord"]
        start = children[3]["start"]
        end = children[3]["end"]

    assert children[0]["level"] == "Prana"
    assert all(child["lord"] in ORDER for child in children)


def test_child_sequence_uses_existing_vimshottari_order_and_ratios():
    children = dasha_children(1, "Saturn", "2020-01-01T00:00:00+00:00", "2039-01-01T00:00:00+00:00")
    start = ORDER.index("Saturn")
    assert [child["lord"] for child in children] == list(ORDER[start:]) + list(ORDER[:start])
    total_years = sum(child["years"] for child in children)
    assert children[0]["years"] / total_years == pytest.approx(YEARS["Saturn"] / 120, abs=1e-9)


def test_birth_balance_and_existing_mahadasha_output_remain_authoritative():
    birth = dt.datetime(1990, 5, 15, 14, 15, tzinfo=ZoneInfo("Asia/Kolkata"))
    moon_longitude = 123.45
    result = vimshottari_dasha(moon_longitude, birth, now=birth)
    info = nakshatra_of(moon_longitude)
    expected_balance = (1 - info["progress"]) * YEARS[info["lord"]]

    assert result["mahadashas"][0]["lord"] == info["lord"]
    assert result["mahadashas"][0]["isBalanceAtBirth"] is True
    assert result["balanceAtBirth"]["years"] == round(expected_balance, 6)
    assert result["mahadashas"][0]["start"] == birth.isoformat()
    assert len(result["currentDashaFlow"]) == 5
    assert [item["level"] for item in result["currentDashaFlow"]] == list(DASHA_LEVELS)


def test_current_detection_is_exact_at_child_boundary():
    birth = dt.datetime(1990, 5, 15, 14, 15, tzinfo=ZoneInfo("Asia/Kolkata"))
    result = vimshottari_dasha(123.45, birth, now=birth)
    maha = result["mahadashas"][0]
    children = dasha_children(1, maha["lord"], maha["start"], maha["end"])
    boundary = stamps(children[1]["start"])
    at_boundary = vimshottari_dasha(123.45, birth, now=boundary)

    assert at_boundary["currentAntardasha"]["start"] == children[1]["start"]
    assert at_boundary["currentAntardasha"]["start"] != children[0]["start"]


def test_children_endpoint_is_deterministic_and_rejects_invalid_levels():
    client = TestClient(main.app)
    payload = {"level": 1, "lord": "Saturn",
               "start": "2020-01-01T00:00:00+00:00",
               "end": "2039-01-01T00:00:00+00:00"}
    response = client.post("/api/kundli/dasha/children", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["level"] == "Antardasha"
    assert body["periods"][0]["start"] == payload["start"]
    assert body["periods"][-1]["end"] == payload["end"]

    invalid = client.post("/api/kundli/dasha/children", json={**payload, "level": 5})
    assert invalid.status_code == 400
    assert "Dasha" in invalid.json()["message"]


def test_dasha_ui_is_drilldown_not_five_static_tables():
    page = PAGE.read_text(encoding="utf-8")
    flow = FLOW.read_text(encoding="utf-8")

    assert "<DashaFlow dasha={kundli.dasha}" in page
    assert "fetchDashaChildren" in flow
    assert "Back to" in flow
    assert "View Current Dasha" in flow
    assert "currentDashaFlow" in flow
    assert "Vimshottari Dasha" in flow
    assert len(re.findall(r"<Table", page)) < 5
