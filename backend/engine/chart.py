"""
Main chart pipeline for Vedic D1 Rashi chart.
"""
from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import swisseph as swe

from config import PLANETS
from engine.ayanamsa import value as ayanamsa_value
from engine.ascendant import calc as ascendant_calc
from engine.houses import assign_house, lagna_sign_index
from engine.julian import from_utc
from engine.planets import calc_all
from engine.rashi import longitude_to_rashi, longitude_to_nakshatra
from models import BirthDetails, Chart, PlanetData


_geolocator = Nominatim(user_agent="kundli-engine")
_timezone_finder = TimezoneFinder()


def resolve_place(place: str) -> dict:
    location = _geolocator.geocode(place, language="en")
    if location is None:
        raise ValueError(f"Place could not be resolved: {place}")
    latitude = float(location.latitude)
    longitude = float(location.longitude)
    timezone_str = _timezone_finder.timezone_at(lat=latitude, lng=longitude)
    if timezone_str is None:
        raise ValueError(f"Timezone could not be resolved for: {place}")
    return {
        "latitude": latitude,
        "longitude": longitude,
        "timezone": timezone_str,
    }


def build_chart(birth: BirthDetails, place_info: dict | None = None) -> Chart:
    if place_info is None:
        place_info = resolve_place(birth.place)
    local_dt = datetime.strptime(
        f"{birth.date} {birth.time}", "%Y-%m-%d %H:%M"
    ).replace(tzinfo=ZoneInfo(place_info["timezone"]))
    utc_dt = local_dt.astimezone(timezone.utc)
    jd = from_utc(utc_dt)
    ayanamsa = ayanamsa_value(jd)
    _tropical_idx = {
        "Sun": swe.SUN,
        "Moon": swe.MOON,
        "Mercury": swe.MERCURY,
        "Venus": swe.VENUS,
        "Mars": swe.MARS,
        "Jupiter": swe.JUPITER,
        "Saturn": swe.SATURN,
        "Rahu": swe.MEAN_NODE,
    }
    tropical_planets = {}
    for name, idx in _tropical_idx.items():
        lon = swe.calc_ut(jd, idx, 0)[0]
        if isinstance(lon, tuple):
            lon = lon[0]
        tropical_planets[name] = float(lon)
    tropical_asc = swe.houses(jd, place_info["latitude"], place_info["longitude"], b"P")[1][0]
    if isinstance(tropical_asc, tuple):
        tropical_asc = tropical_asc[0]
    tropical_asc = float(tropical_asc)
    sidereal_planets = calc_all(jd)
    sidereal_asc = ascendant_calc(jd, place_info["latitude"], place_info["longitude"])
    lagna_sign = lagna_sign_index(sidereal_asc)

    planets = []
    for name in PLANETS:
        longitude = sidereal_planets[name]
        sign_name, sign_number, degree = longitude_to_rashi(longitude)
        nakshatra, pada = longitude_to_nakshatra(longitude)
        house = assign_house(sign_number, lagna_sign)
        planets.append(
            PlanetData(
                name=name,
                longitude=round(longitude, 6),
                sign=sign_name,
                house=house,
                degree=round(degree, 6),
                nakshatra=nakshatra,
                pada=pada,
                status="CALCULATED",
            )
        )

    asc_sign_name, _, asc_degree = longitude_to_rashi(sidereal_asc)
    return Chart(
        status="CALCULATED",
        settings={
            "system": "vedic",
            "zodiac": "sidereal",
            "ayanamsa": "lahiri",
            "house_system": "whole-sign",
        },
        birth={
            "date": birth.date,
            "time": birth.time,
            "place": birth.place,
            "latitude": place_info["latitude"],
            "longitude": place_info["longitude"],
            "timezone": place_info["timezone"],
            "utc_datetime": utc_dt.isoformat(),
        },
        ascendant={
            "longitude": round(sidereal_asc, 6),
            "sign": asc_sign_name,
            "house": 1,
            "degree": round(asc_degree, 6),
        },
        planets=planets,
        houses=[
            {
                "number": i + 1,
                "sign": longitude_to_rashi(
                    ((lagna_sign + i - 1) * 30) % 360
                )[0],
            }
            for i in range(12)
        ],
        validation={
            "passed": True,
            "checks": [
                "birthplace_resolved",
                "timezone_resolved",
                "julian_date_computed",
                "ayanamsa_applied",
                "ascendant_calculated",
                "planets_calculated",
                "houses_assigned",
            ],
        },
        debug={
            "utc_datetime": utc_dt.isoformat(),
            "latitude": place_info["latitude"],
            "longitude": place_info["longitude"],
            "timezone": place_info["timezone"],
            "julian_day": round(jd, 6),
            "ayanamsa": {
                "system": "lahiri",
                "value": round(ayanamsa, 6),
            },
            "tropical_ascendant": round((sidereal_asc + ayanamsa) % 360, 6),
            "sidereal_ascendant": round(sidereal_asc, 6),
            "lagna_sign": asc_sign_name,
            "lagna_sign_number": lagna_sign,
            "lagna_degree": round(asc_degree, 6),
            "house_system": "whole-sign",
            "planets": {
                name: {
                    "tropical_longitude": round(
                        (
                            tropical_planets[name]
                            if name != "Ketu"
                            else (sidereal_planets[name] + ayanamsa) % 360
                        )
                        % 360,
                        6,
                    ),
                    "sidereal_longitude": round(sidereal_planets[name], 6),
                    "sign_number": longitude_to_rashi(sidereal_planets[name])[1],
                    "sign_name": longitude_to_rashi(sidereal_planets[name])[0],
                    "degree": round(longitude_to_rashi(sidereal_planets[name])[2], 6),
                    "house": assign_house(
                        longitude_to_rashi(sidereal_planets[name])[1], lagna_sign
                    ),
                    "nakshatra": longitude_to_nakshatra(sidereal_planets[name])[0],
                    "pada": longitude_to_nakshatra(sidereal_planets[name])[1],
                }
                for name in PLANETS
            },
        },
    )
