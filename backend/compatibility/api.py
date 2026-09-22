"""HTTP surface for KAVACH MARRIAGE COMPATIBILITY.

Both charts come from the EXISTING authoritative Kundli engine; nothing about
Swiss Ephemeris, Lahiri, nakshatras or signs is re-implemented here.

The source method is directional, so the two inputs are explicit BRIDE and
GROOM roles. Gender is never inferred from a name, account or profile.

The public payload carries the six qualitative factor results only - no rule
tables, no Yoni, no /36 total and no prohibited output.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from .engine import evaluate_compatibility
from .models import PersonFacts

logger = logging.getLogger("kavach.compatibility")

router = APIRouter(prefix="/api/compatibility", tags=["compatibility"])

FACTOR_KEYS = ("tara", "gana", "nadi", "rashi", "graha_maitri", "vasya")


class PersonInput(BaseModel):
    name: str = ""
    date: str = ""
    time: str = ""
    place: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: str = ""


class CompatibilityRequest(BaseModel):
    bride: PersonInput
    groom: PersonInput


def _facts(person: PersonInput, role: str) -> PersonFacts:
    """Moon sign, Moon nakshatra and Moon-sign ruler from the authoritative chart."""
    from kundli import build_kundli
    from kundli.analysis.signs import SIGN_LORD

    chart = build_kundli({
        "date": person.date,
        "time": person.time,
        "place": person.place,
        "latitude": person.latitude,
        "longitude": person.longitude,
        "timezone": person.timezone or "Asia/Kolkata",
        "name": person.name,
    })
    moon = next(
        (row for row in chart.get("planets", []) if row.get("planet") == "Moon"),
        None,
    )
    if not moon or not moon.get("rashi") or not moon.get("nakshatra"):
        raise ValueError("The Moon position could not be established for this chart.")
    moon_sign = moon["rashi"]
    ruler = SIGN_LORD.get(moon_sign)
    if not ruler:
        raise ValueError("The Moon-sign ruler could not be established for this chart.")
    return PersonFacts(
        name=person.name.strip(),
        role=role,
        moon_sign=moon_sign,
        moon_nakshatra=moon["nakshatra"],
        moon_ruler=ruler,
    )


def _validate(person: PersonInput, label: str) -> Optional[str]:
    if not person.name.strip():
        return f"Please enter {label}'s name."
    if not person.date.strip() or not person.time.strip() or not person.place.strip():
        return f"Please complete {label}'s birth date, time and place."
    return None


@router.post("")
def compatibility(payload: CompatibilityRequest) -> Dict[str, Any]:
    """Qualitative traditional compatibility for two charts."""
    for person, label in ((payload.bride, "the bride"), (payload.groom, "the groom")):
        problem = _validate(person, label)
        if problem:
            return {"status": "invalid", "message": problem}

    try:
        from kundli.analysis.signs import RASHIS
        from navtara.constants import NAKSHATRAS

        bride = _facts(payload.bride, "bride")
        groom = _facts(payload.groom, "groom")
        report = evaluate_compatibility(bride, groom, NAKSHATRAS, RASHIS)
    except ValueError as exc:
        return {"status": "invalid", "message": str(exc)}
    except Exception as exc:  # a calculation failure must never leak internals
        logger.warning("Compatibility calculation failed: %s", type(exc).__name__)
        return {"status": "error", "message": "We couldn't prepare this compatibility report."}

    people: List[Dict[str, Any]] = [
        {"role": p.role, "name": p.name, "moonSign": p.moon_sign, "moonNakshatra": p.moon_nakshatra}
        for p in (bride, groom)
    ]

    # Owner-visible archive: verified identity comes from the request token, and
    # the two chart-person names are kept separate from the account.
    try:
        from archive import record_submission

        record_submission(
            "compatibility",
            {
                "bride_name": bride.name,
                "bride_date": payload.bride.date,
                "bride_time": payload.bride.time,
                "bride_place": payload.bride.place,
                "groom_name": groom.name,
                "groom_date": payload.groom.date,
                "groom_time": payload.groom.time,
                "groom_place": payload.groom.place,
            },
            {"report": report},
        )
    except Exception as exc:
        logger.warning("Compatibility archive skipped: %s", type(exc).__name__)

    return {"status": "ok", "people": people, "report": report}
