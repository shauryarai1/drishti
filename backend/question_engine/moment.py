"""Question-moment context builder.

System B only. Uses the exact question timestamp and the selected location.
Never reads natal data.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from panchang.moment import calculate_panchang_moment


def build_question_moment_context(
    question_timestamp: datetime,
    latitude: float,
    longitude: float,
    timezone_name: str = "Asia/Kolkata",
    label: str = "",
) -> Dict[str, Any]:
    moment = calculate_panchang_moment(
        moment=question_timestamp,
        latitude=latitude,
        longitude=longitude,
        timezone_name=timezone_name,
        label=label,
    )
    return {
        "system": "question_moment",
        "uses_birth_details": False,
        "uses_natal_chart": False,
        "chart_reference": "question_moment",
        "moment": moment,
    }
