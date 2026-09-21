"""Kundli aggregation: reuses the existing chart, Panchang and astronomy paths.

No proprietary KAVACH interpretation is exposed here - calculated chart data only.
"""

from __future__ import annotations

from datetime import datetime, time
from typing import Any, Dict, List
from zoneinfo import ZoneInfo

from calculator import (
    BirthData,
    _sign_from_longitude,
    calc_planet_longitudes,
    calc_planet_retrograde,
    generate_chart,
    whole_sign_house,
)
from panchang import astronomy
from panchang.moment import calculate_panchang_moment

from .dasha import vimshottari_dasha
from .nakshatra import nakshatra_of

NAVAGRAHA = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")
NODES = ("Rahu", "Ketu")


def _birth_moment(payload: Dict[str, Any]) -> datetime:
    tz = ZoneInfo(payload.get("timezone") or "Asia/Kolkata")
    date = datetime.fromisoformat(str(payload["date"])).date()
    hour, minute = (int(part) for part in str(payload["time"]).split(":")[:2])
    return datetime.combine(date, time(hour, minute), tzinfo=tz)


def _planet_rows(chart, retrograde: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for planet in chart.planets:
        if planet.name not in NAVAGRAHA:
            continue
        info = nakshatra_of(planet.longitude)
        if planet.name in NODES:
            motion = "Node"
        else:
            motion = "Retrograde" if retrograde.get(planet.name) else "Direct"
        rows.append({
            "planet": planet.name,
            "longitude": round(planet.longitude, 6),
            "rashi": planet.sign,
            "degree": round(planet.degree, 4),
            "house": planet.house,
            "nakshatra": info["name"],
            "pada": info["pada"],
            "nakshatraLord": info["lord"],
            "motion": motion,
        })
    order = {name: index for index, name in enumerate(NAVAGRAHA)}
    return sorted(rows, key=lambda item: order.get(item["planet"], 99))


def build_kundli(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Full Kundli payload from the existing calculator + Panchang engine."""
    birth = BirthData(
        date=str(payload["date"]),
        time=str(payload["time"]),
        place=payload.get("place") or "Unknown",
        latitude=float(payload["latitude"]),
        longitude=float(payload["longitude"]),
    )
    chart = generate_chart(birth)
    moment = _birth_moment(payload)
    panchang = calculate_panchang_moment(
        moment, float(payload["latitude"]), float(payload["longitude"]),
        payload.get("timezone") or "Asia/Kolkata", payload.get("place") or "",
    )

    # Retrograde comes from the real longitudinal speed at the birth instant.
    # (The Panchang D1 positions do not request speed and report False.)
    retrograde = calc_planet_retrograde(astronomy.to_jd(moment))
    planets = _planet_rows(chart, retrograde)

    moon = next((item for item in planets if item["planet"] == "Moon"), None)
    sun = next((item for item in planets if item["planet"] == "Sun"), None)
    moon_longitude = next(p.longitude for p in chart.planets if p.name == "Moon")
    dasha = vimshottari_dasha(moon_longitude, moment)

    tithi = panchang.get("tithi", {})
    nakshatra = panchang.get("nakshatra", {})
    ascendant = chart.ascendant

    return {
        "status": "ok",
        "birth": {
            "name": payload.get("name") or "",
            "date": birth.date,
            "time": birth.time,
            "place": birth.place,
            "latitude": birth.latitude,
            "longitude": birth.longitude,
            "timezone": payload.get("timezone") or "Asia/Kolkata",
        },
        "summary": {
            "lagna": f"{ascendant.sign} {round(ascendant.degree, 2)}",
            "lagnaRashi": ascendant.sign,
            "moonRashi": moon["rashi"] if moon else None,
            "sunRashi": sun["rashi"] if sun else None,
            "nakshatra": nakshatra.get("name"),
            "pada": nakshatra.get("pada"),
            "paksha": tithi.get("paksha"),
            "tithi": tithi.get("name"),
        },
        "chart": {
            "ascendant": {
                "rashi": ascendant.sign,
                "degree": round(ascendant.degree, 4),
                "longitude": round(ascendant.longitude, 6),
            },
            "houses": [
                {"number": house.number, "rashi": house.sign,
                 "cuspLongitude": round(house.cusp_longitude, 6)}
                for house in chart.houses
            ],
            "planets": planets,
        },
        "planets": planets,
        "panchang": {
            "vara": panchang.get("vara", {}).get("english"),
            "tithi": tithi.get("name"),
            "paksha": tithi.get("paksha"),
            "nakshatra": nakshatra.get("name"),
            "pada": nakshatra.get("pada"),
            "yoga": panchang.get("yoga", {}).get("name"),
            "karana": panchang.get("karana", {}).get("name"),
            "sunRashi": sun["rashi"] if sun else None,
            "moonRashi": moon["rashi"] if moon else None,
        },
        "dasha": dasha,
    }


def build_transits(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Current sidereal positions mapped to the natal houses. No interpretation."""
    birth = BirthData(
        date=str(payload["date"]),
        time=str(payload["time"]),
        place=payload.get("place") or "Unknown",
        latitude=float(payload["latitude"]),
        longitude=float(payload["longitude"]),
    )
    natal = generate_chart(birth)
    _, lagna_index, _ = _sign_from_longitude(natal.ascendant.longitude)

    timezone_name = payload.get("timezone") or "Asia/Kolkata"
    now = datetime.now(ZoneInfo(timezone_name))
    jd = astronomy.to_jd(now)
    longitudes = calc_planet_longitudes(jd)

    rows: List[Dict[str, Any]] = []
    for planet in NAVAGRAHA:
        longitude = longitudes.get(planet)
        if longitude is None:
            continue
        sign, sign_index, degree = _sign_from_longitude(longitude)
        info = nakshatra_of(longitude)
        rows.append({
            "planet": planet,
            "longitude": round(longitude, 6),
            "rashi": sign,
            "degree": round(degree, 4),
            "nakshatra": info["name"],
            "pada": info["pada"],
            "natalHouse": whole_sign_house(sign_index, lagna_index),
        })

    return {
        "status": "ok",
        "asOf": {"timestamp": now.isoformat(), "timezone": timezone_name},
        "natalLagna": natal.ascendant.sign,
        "transits": rows,
    }
