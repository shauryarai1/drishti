"""Daily Moon — day quality rule.

SEPARATE from the birth-panchang significator channels. This uses TODAY'S
transits only and never reads the native's birth chart.

Astrologer's supplied rule:
    today's Moon Rashi      -> comfort-zone identifier
    today's Moon Nakshatra  -> day-pattern identifier
    its Nakshatra lord      -> located in TODAY'S chart
    lord in house 6/8/12    -> EXTRA CARE
    any other house         -> SUPPORTIVE

No further meanings are implemented.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, Optional

from panchang import PanchangRequest, compute_panchang

from . import selectors

EXTRA_CARE_HOUSES = frozenset({6, 8, 12})
SUPPORTIVE_HOUSES = frozenset({1, 2, 3, 4, 5, 7, 9, 10, 11})

# The astrologer has not yet confirmed which moment defines "today's chart".
# This default is TEMPORARY and must not be treated as settled methodology.
DEFAULT_CHART_REFERENCE = "sunrise"
CHART_REFERENCE_STATUS = "CONFIGURATION / AWAITING ASTROLOGER CONFIRMATION"
SUPPORTED_CHART_REFERENCES = ("sunrise",)


def classify_house(house: Optional[int]) -> str:
    """6 / 8 / 12 -> extra_care, everything else -> supportive."""
    if house in EXTRA_CARE_HOUSES:
        return "extra_care"
    return "supportive"


def _chart_for_reference(panchang: Dict[str, Any], reference: str) -> tuple[Dict[str, Any], str]:
    """Select the chart that represents "today's chart" for this rule."""
    if reference not in SUPPORTED_CHART_REFERENCES:
        raise ValueError(
            f"Unsupported daily chart reference '{reference}'. "
            f"Supported for testing: {SUPPORTED_CHART_REFERENCES}. "
            f"Status: {CHART_REFERENCE_STATUS}"
        )
    # sunrise -> the production Panchang's Sunrise D1 chart.
    return panchang["d1"], panchang["sun_moon"]["sunrise"]


def compute_daily_moon_signal(
    on_date: date,
    latitude: float,
    longitude: float,
    timezone: str = "Asia/Kolkata",
    label: str = "",
    daily_chart_reference: str = DEFAULT_CHART_REFERENCE,
) -> Dict[str, Any]:
    """Day-quality signal from today's Moon. No birth details required."""
    panchang = compute_panchang(
        PanchangRequest(
            on_date=on_date,
            latitude=latitude,
            longitude=longitude,
            timezone_name=timezone,
            label=label,
        )
    )

    moon_rashi = panchang["sun_moon_rashi"]["moon"]["name"]
    nakshatra = panchang["panchanga"]["nakshatra"]
    lord = selectors.nakshatra_lord(nakshatra["name"])

    chart, reference_time = _chart_for_reference(panchang, daily_chart_reference)
    placement = next(
        (position for position in chart["positions"] if position["planet"] == lord),
        None,
    )
    lord_house = placement["house"] if placement else None

    return {
        "engine": "daily_moon_signal",
        "date": panchang["day"]["date"],
        "location": panchang.get("location"),
        "birth_details_required": False,
        "moon": {
            "rashi": moon_rashi,
            "nakshatra": nakshatra["name"],
            "pada": nakshatra.get("pada"),
            "nakshatra_lord": lord,
        },
        "daily_chart": {
            "reference": daily_chart_reference,
            "reference_status": CHART_REFERENCE_STATUS,
            "reference_time": reference_time,
            "nakshatra_lord": lord,
            "lord_house": lord_house,
            "lord_rashi": placement["sign"] if placement else None,
        },
        "classification": classify_house(lord_house),
        "semantics": {
            "moon_rashi": "comfort_zone_identifier",
            "moon_nakshatra": "day_pattern_identifier",
            "house_rule": "houses 6, 8, 12 => extra_care; all other houses => supportive",
        },
        "notes": [
            "General daily signal — no birth details are used or required.",
            "The chart reference is configurable and still awaiting astrologer confirmation.",
            "No Moon-rashi or Nakshatra interpretations are implemented yet.",
        ],
    }
