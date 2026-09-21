"""Deterministic tests for the Vimshottari Dasha engine and Nakshatra derivation.

Conventions asserted here are documented in kundli/dasha.py:
* proportional balance of the birth nakshatra lord's Mahadasha
* 120-year cycle, 365.2425 days per year
* antardasha = mahadasha_years * lord_years / 120
"""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from kundli.dasha import ORDER, TOTAL_YEARS, YEAR_DAYS, YEARS, antardashas, vimshottari_dasha
from kundli.nakshatra import NAKSHATRA_SPAN, nakshatra_of
from panchang.constants import NAKSHATRA_NAMES

TZ = ZoneInfo("Asia/Kolkata")
BIRTH = datetime(1990, 5, 15, 14, 15, tzinfo=TZ)


# --- nakshatra derivation -------------------------------------------------
def test_exact_nakshatra_start():
    info = nakshatra_of(0.0)
    assert info["name"] == NAKSHATRA_NAMES[0]
    assert info["pada"] == 1
    assert info["lord"] == "Ketu"
    assert info["progress"] == 0.0


def test_middle_of_nakshatra():
    info = nakshatra_of(NAKSHATRA_SPAN / 2)
    assert info["name"] == NAKSHATRA_NAMES[0]
    assert info["progress"] == pytest.approx(0.5, abs=1e-6)
    assert info["pada"] == 3


def test_near_nakshatra_end():
    info = nakshatra_of(NAKSHATRA_SPAN - 0.001)
    assert info["name"] == NAKSHATRA_NAMES[0]
    assert info["pada"] == 4
    assert info["progress"] > 0.999


def test_boundary_rolls_to_next_nakshatra():
    info = nakshatra_of(NAKSHATRA_SPAN)
    assert info["name"] == NAKSHATRA_NAMES[1]
    assert info["lord"] == "Venus"
    assert info["pada"] == 1


def test_last_nakshatra_and_wrap():
    info = nakshatra_of(359.999)
    assert info["name"] == NAKSHATRA_NAMES[26]
    assert info["lord"] == "Mercury"
    assert nakshatra_of(360.0)["name"] == NAKSHATRA_NAMES[0]


@pytest.mark.parametrize("index,lord", [
    (1, "Ketu"), (4, "Moon"), (8, "Saturn"), (17, "Saturn"),
    (20, "Venus"), (27, "Mercury"),
])
def test_lord_selection(index, lord):
    longitude = (index - 1) * NAKSHATRA_SPAN + 0.01
    info = nakshatra_of(longitude)
    assert info["name"] == NAKSHATRA_NAMES[index - 1]
    assert info["lord"] == lord


def test_every_nakshatra_name_resolves_to_a_lord():
    lords = {nakshatra_of((index + 0.5) * NAKSHATRA_SPAN)["lord"] for index in range(27)}
    assert None not in lords
    assert lords == set(ORDER)


# --- mahadasha sequence ---------------------------------------------------
def test_sequence_order_and_cycle():
    assert ORDER[0] == "Ketu" and ORDER[-1] == "Mercury"
    assert TOTAL_YEARS == 120
    assert sum(YEARS.values()) == 120


def test_birth_balance_is_proportional_not_full():
    half = vimshottari_dasha(NAKSHATRA_SPAN / 2, BIRTH)
    assert half["birthNakshatraLord"] == "Ketu"
    assert half["progressAtBirth"] == pytest.approx(0.5, abs=1e-6)
    assert half["balanceAtBirth"]["years"] == pytest.approx(3.5, abs=1e-6)
    first = half["mahadashas"][0]
    assert first["lord"] == "Ketu" and first["isBalanceAtBirth"] is True
    assert first["years"] == pytest.approx(3.5, abs=1e-6)


def test_birth_balance_mercury_case():
    # Moon in the last nakshatra (Revati, Mercury) at 25% progress.
    longitude = 26 * NAKSHATRA_SPAN + NAKSHATRA_SPAN * 0.25
    result = vimshottari_dasha(longitude, BIRTH)
    assert result["birthNakshatra"] == NAKSHATRA_NAMES[26]
    assert result["birthNakshatraLord"] == "Mercury"
    assert result["balanceAtBirth"]["years"] == pytest.approx(0.75 * 17, abs=1e-6)


def test_mahadasha_dates_are_contiguous():
    result = vimshottari_dasha(NAKSHATRA_SPAN / 3, BIRTH)
    periods = result["mahadashas"]
    assert len(periods) >= 9
    for previous, current in zip(periods, periods[1:]):
        assert previous["end"] == current["start"]
    assert periods[0]["start"] == BIRTH.isoformat()


def test_full_cycle_after_balance():
    # start at a nakshatra boundary so the balance is the full 7 years
    result = vimshottari_dasha(0.0, BIRTH)
    periods = result["mahadashas"]
    first_nine = periods[:9]
    assert [item["lord"] for item in first_nine] == list(ORDER)
    total = sum(item["years"] for item in first_nine)
    assert total == pytest.approx(TOTAL_YEARS, abs=1e-6)


def test_wrapping_continues_after_mercury():
    # birth halfway through Ashvini: the balance period is short, so the timeline
    # must wrap past Mercury back to Ketu within the default 120-year span.
    result = vimshottari_dasha(NAKSHATRA_SPAN / 2, BIRTH)
    lords = [item["lord"] for item in result["mahadashas"]]
    assert "Saturn" in lords and "Mercury" in lords
    assert lords[lords.index("Mercury") + 1] == "Ketu"

    # and a two-cycle span wraps repeatedly while staying contiguous
    longer = vimshottari_dasha(NAKSHATRA_SPAN / 2, BIRTH, span_years=240)
    long_lords = [item["lord"] for item in longer["mahadashas"]]
    assert long_lords.count("Ketu") >= 3
    for previous, current in zip(longer["mahadashas"], longer["mahadashas"][1:]):
        assert previous["end"] == current["start"]


def test_no_overlaps_or_gaps_over_two_cycles():
    result = vimshottari_dasha(NAKSHATRA_SPAN * 3.5, BIRTH)
    periods = result["mahadashas"]
    cursor = datetime.fromisoformat(periods[0]["start"])
    for item in periods:
        start = datetime.fromisoformat(item["start"])
        end = datetime.fromisoformat(item["end"])
        assert start == cursor
        assert end > start
        cursor = end


def test_current_mahadasha_lookup_is_inside_its_range():
    result = vimshottari_dasha(0.0, BIRTH)
    current = result["currentMahadasha"]
    assert current is not None
    now = datetime.now(TZ).isoformat()
    assert current["start"] <= now < current["end"]


def test_year_length_convention():
    result = vimshottari_dasha(0.0, BIRTH)
    first = result["mahadashas"][0]
    start = datetime.fromisoformat(first["start"])
    end = datetime.fromisoformat(first["end"])
    expected = timedelta(days=YEARS["Ketu"] * YEAR_DAYS)
    assert (end - start) == expected


# --- antardasha -----------------------------------------------------------
def test_antardasha_sequence_starts_at_mahadasha_lord():
    start = BIRTH
    subs = antardashas("Venus", start, YEARS["Venus"])
    assert [item["lord"] for item in subs] == list(ORDER[ORDER.index("Venus"):]) + list(ORDER[:ORDER.index("Venus")])
    assert subs[0]["lord"] == "Venus"


def test_antardasha_durations_are_proportional():
    subs = antardashas("Venus", BIRTH, YEARS["Venus"])
    spans = {item["lord"]: (datetime.fromisoformat(item["end"]) - datetime.fromisoformat(item["start"])).total_seconds()
             for item in subs}
    mahadasha_seconds = YEARS["Venus"] * YEAR_DAYS * 86400
    for lord, seconds in spans.items():
        assert seconds == pytest.approx(mahadasha_seconds * YEARS[lord] / TOTAL_YEARS, rel=1e-6)


def test_antardashas_are_contiguous_and_fill_the_mahadasha():
    subs = antardashas("Saturn", BIRTH, YEARS["Saturn"])
    assert subs[0]["start"] == BIRTH.isoformat()
    for previous, current in zip(subs, subs[1:]):
        assert previous["end"] == current["start"]
    end = datetime.fromisoformat(subs[-1]["end"])
    assert (end - BIRTH) == timedelta(days=YEARS["Saturn"] * YEAR_DAYS)


def test_current_antardasha_is_inside_the_current_mahadasha():
    result = vimshottari_dasha(NAKSHATRA_SPAN * 2.5, BIRTH)
    maha = result["currentMahadasha"]
    antar = result["currentAntardasha"]
    assert maha and antar
    assert maha["start"] <= antar["start"] < antar["end"] <= maha["end"]
    assert antar["lord"] in ORDER
