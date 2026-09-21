"""PRIVATE Current Dasha Reading engine.

Inputs are ONLY the native's Janma Moon Nakshatra and the three Vimshottari
Nakshatras of the CURRENT Mahadasha lord. No houses, aspects, dignity, transit,
Shadbala, friendship or any other planet rule.

The current Mahadasha/Antardasha come from the EXISTING Vimshottari engine.
"""

from __future__ import annotations

from datetime import date as date_type, datetime, time
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from kavach_core.mappings import NAKSHATRA_LORDS
from kundli.dasha import vimshottari_dasha
from navtara import get_janma_nakshatra_from_birth_details, get_navtara
from navtara.constants import NAKSHATRAS, canonical_nakshatra

from .public import render_reading

METHODOLOGY_VERSION = "current-dasha-navtara-v1"

# lord -> its three Vimshottari Nakshatras, derived from the authoritative
# approved mapping (never duplicated by hand).
def _canonical_index(name: str) -> int:
    canonical = canonical_nakshatra(name)
    return NAKSHATRAS.index(canonical) if canonical in NAKSHATRAS else len(NAKSHATRAS)


LORD_NAKSHATRAS: Dict[str, List[str]] = {
    lord: sorted({canonical_nakshatra(name) for name in names}, key=_canonical_index)
    for lord, names in NAKSHATRA_LORDS.items()
}


def get_lord_nakshatras(lord: str) -> List[str]:
    return list(LORD_NAKSHATRAS.get(lord, []))


def _birth_moment(birth: Dict[str, Any], timezone_name: str) -> datetime:
    tz = ZoneInfo(timezone_name)
    day = date_type.fromisoformat(str(birth["date"]))
    hour, minute = (int(part) for part in str(birth["time"]).split(":")[:2])
    return datetime.combine(day, time(hour, minute), tzinfo=tz)


def _dasha_for_date(moon_longitude: float, birth_moment: datetime, as_of: datetime) -> Dict[str, Any]:
    """Existing Vimshottari engine, evaluated at the requested instant."""
    # vimshottari_dasha uses 'now' internally for the current periods, so we
    # evaluate the returned timeline against the requested as-of moment.
    timeline = vimshottari_dasha(moon_longitude, birth_moment)
    stamp = as_of.isoformat()
    maha = next((item for item in timeline["mahadashas"]
                 if item["start"] <= stamp < item["end"]), timeline["currentMahadasha"])
    antar = None
    if maha:
        from kundli.dasha import antardashas
        start = datetime.fromisoformat(maha["start"])
        for item in antardashas(maha["lord"], start, maha["years"]):
            if item["start"] <= stamp < item["end"]:
                antar = item
                break
    return {"mahadasha": maha, "antardasha": antar}


def build_private_current_dasha(birth: Dict[str, Any], as_of: Optional[str] = None) -> Dict[str, Any]:
    """PRIVATE reading: Janma Nakshatra + current Mahadasha lord's 3 Nakshatras."""
    timezone_name = birth.get("timezone") or "Asia/Kolkata"
    tz = ZoneInfo(timezone_name)
    moment = _birth_moment(birth, timezone_name)
    as_of_moment = datetime.fromisoformat(as_of).astimezone(tz) if as_of else datetime.now(tz)

    natal = get_janma_nakshatra_from_birth_details(
        date=str(birth["date"]), time=str(birth["time"]),
        place=birth.get("place") or "", latitude=float(birth["latitude"]),
        longitude=float(birth["longitude"]),
    )
    janma = str(natal["nakshatra"])
    dasha = _dasha_for_date(float(natal["longitude"]), moment, as_of_moment)

    lord = (dasha["mahadasha"] or {}).get("lord")
    lord_nakshatras: List[Dict[str, Any]] = []
    for nakshatra in get_lord_nakshatras(lord or ""):
        info = get_navtara(janma, nakshatra)
        lord_nakshatras.append({
            "nakshatra": nakshatra,
            "tara": info["tara"],
            "taraNumber": info["taraNumber"],
            "relativePosition": info["position"],
            "nature": info["nature"],
        })

    return {
        "janmaNakshatra": janma,
        "asOf": as_of_moment.isoformat(),
        "timezone": timezone_name,
        "mahadasha": dasha["mahadasha"],
        "antardasha": dasha["antardasha"],
        "lordNakshatras": lord_nakshatras,
        "methodologyVersion": METHODOLOGY_VERSION,
    }


def build_current_dasha_reading(birth: Dict[str, Any], as_of: Optional[str] = None) -> Dict[str, Any]:
    """Private engine -> customer-safe DTO (the only thing the API returns)."""
    private = build_private_current_dasha(birth, as_of)
    return render_reading(private)
