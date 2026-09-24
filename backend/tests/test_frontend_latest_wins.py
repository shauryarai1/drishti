"""Frontend reliability: every async result path is latest-request-wins.

A superseded response must never overwrite the current data, error or loading
state. These are structural guards: the behaviour is exercised by the pages at
runtime, and the tests below lock the pattern in place.
"""

from __future__ import annotations

import pathlib

REPO = pathlib.Path(__file__).resolve().parents[2]
APP = REPO / "frontend-next" / "app"

GUARDED = {
    "daily": APP / "daily" / "page.tsx",
    "life-summary": APP / "life-summary" / "page.tsx",
    "your-week": APP / "your-week" / "page.tsx",
    "kundli": APP / "kundli" / "page.tsx",
}


def _read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def test_every_result_page_has_a_latest_wins_guard():
    for name, path in GUARDED.items():
        source = _read(path)
        assert "useRef(0)" in source, name
        assert "Ref.current + 1" in source, name
        # The superseded response must be ignored before it can touch state.
        assert "!== " in source and ".current) return;" in source, name


def test_daily_guard_keeps_the_request_id():
    source = _read(GUARDED["daily"])
    assert "requestIdRef" in source
    assert "if (requestId !== requestIdRef.current) return;" in source
    assert "if (requestId === requestIdRef.current) setBusy(false);" in source


def test_life_summary_guard_covers_data_error_and_busy():
    source = _read(GUARDED["life-summary"])
    assert "requestIdRef" in source
    assert "if (requestId !== requestIdRef.current) return;" in source
    assert "if (requestId === requestIdRef.current) setBusy(false);" in source


def test_your_week_guard_covers_the_reveal_fetch():
    source = _read(GUARDED["your-week"])
    assert "requestIdRef" in source
    # The user-triggered reveal uses the latest-request-wins guard.
    assert source.count("requestIdRef.current + 1") == 1
    assert "if (requestId === requestIdRef.current) setBusy(false);" in source


def test_kundli_guard_covers_generate_transits_and_snapshot():
    source = _read(GUARDED["kundli"])
    assert "loadIdRef" in source
    # generate(), the transits fetch and the saved-snapshot load all guard.
    assert source.count("loadIdRef.current + 1") >= 2
    assert "if (loadId !== loadIdRef.current) return;" in source
    assert "if (loadId === loadIdRef.current) setBusy(false);" in source


def test_payloads_and_methodology_untouched_by_the_guard():
    """The guard must not change what is requested."""
    life = _read(GUARDED["life-summary"])
    assert "`${API_BASE}/life-summary`" in life
    week = _read(GUARDED["your-week"])
    assert "fetchWeekly(" in week and "birth:" in week and "forecast:" in week
    kundli = _read(GUARDED["kundli"])
    assert "fetchKundli(payload)" in kundli and "fetchKundliTransits(payload)" in kundli
