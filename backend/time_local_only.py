"""
Standalone timing test: NO network calls.
Uses fixed lat/lng/tz for Delhi.
"""
from __future__ import annotations

import time
import swisseph as swe
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from config import AYANAMSA, ALL_PLANETS, EXTRA_PLANETS, RASHI_NAMES
from calculator import _jd_utc, _sign_from_longitude, calc_planet_longitudes, calc_ascendant, whole_sign_house
from models import ChartResponse, PlanetData, HouseData, AscendantData

# Fixed coordinates / timezone
LAT = 28.6139
LNG = 77.2090
TZ = "Asia/Kolkata"
DATE = "2010-01-21"
TIME = "08:19"

def main() -> None:
    timings = {}

    # 1. Input parsing + local datetime
    t0 = time.perf_counter()
    local_dt = datetime.strptime(f"{DATE} {TIME}", "%Y-%m-%d %H:%M").replace(
        tzinfo=ZoneInfo(TZ)
    )
    utc_dt = local_dt.astimezone(timezone.utc)
    timings["input_and_timezone"] = time.perf_counter() - t0

    # 2. Julian date
    t0 = time.perf_counter()
    jd = _jd_utc(utc_dt)
    timings["julian_date"] = time.perf_counter() - t0

    # 3. Ayanamsa
    t0 = time.perf_counter()
    ayanamsa = swe.get_ayanamsa(jd)
    if isinstance(ayanamsa, tuple):
        ayanamsa = ayanamsa[0]
    ayanamsa = float(ayanamsa)
    timings["ayanamsa"] = time.perf_counter() - t0

    # 4. Planets
    t0 = time.perf_counter()
    sid_lons = calc_planet_longitudes(jd)
    timings["planets"] = time.perf_counter() - t0

    # 5. Ascendant
    t0 = time.perf_counter()
    tropical_asc = calc_ascendant(jd, LAT, LNG)
    sid_asc = tropical_asc - ayanamsa
    sid_asc = sid_asc % 360.0
    asc_sign, asc_sign_idx, asc_degree = _sign_from_longitude(sid_asc)
    timings["ascendant"] = time.perf_counter() - t0

    # 6. Houses
    t0 = time.perf_counter()
    houses = []
    for i in range(12):
        sign_idx = (asc_sign_idx + i) % 12
        houses.append(
            HouseData(
                number=i + 1,
                sign=RASHI_NAMES[sign_idx],
                cusp_longitude=float(sign_idx) * 30.0,
            )
        )
    timings["houses"] = time.perf_counter() - t0

    # 7. Planet house assignment
    t0 = time.perf_counter()
    planets = []
    extra_planets = []
    for name in ALL_PLANETS:
        lon = sid_lons[name]
        sign, sign_idx, degree = _sign_from_longitude(lon)
        house = whole_sign_house(sign_idx, asc_sign_idx)
        planet_data = PlanetData(
            name=name,
            longitude=round(lon, 6),
            sign=sign,
            house=house,
            degree=round(degree, 6),
            source="Swiss Ephemeris",
            status="CALCULATED",
        )
        if name in EXTRA_PLANETS:
            extra_planets.append(planet_data)
        else:
            planets.append(planet_data)
    timings["house_assignment"] = time.perf_counter() - t0

    total = sum(timings.values())

    # Output
    print("TIMING")
    print("------------------------")
    for k, v in timings.items():
        print(f"{k:20s}: {v*1000:.2f} ms")
    print(f"{'total':20s}: {total*1000:.2f} ms")
    print("------------------------")
    print()
    print(f"Ascendant: {asc_sign} {asc_degree:.4f}")
    print(f"Ayanamsa : {ayanamsa:.6f}")
    print()
    print("Main planets:")
    for p in planets:
        print(f"  {p.name:8s} | {p.longitude:8.4f} | {p.sign:12s} | {p.degree:6.2f} | House {p.house}")
    print()
    print("Additional planets:")
    for p in extra_planets:
        print(f"  {p.name:8s} | {p.longitude:8.4f} | {p.sign:12s} | {p.degree:6.2f} | House {p.house}")
    print()
    print("Houses:")
    for h in houses:
        print(f"  {h.number:2d} | {h.sign}")
    print()
    print("Validation:")
    print(f"  main planets      : {len(planets)}")
    print(f"  extra planets     : {len(extra_planets)}")
    print(f"  houses count      : {len(houses)}")
    print(f"  unique house signs: {sorted(set(h.sign for h in houses))}")
    print(f"  all 1-12 present  : {sorted(h.number for h in houses) == list(range(1,13))}")


if __name__ == "__main__":
    main()
