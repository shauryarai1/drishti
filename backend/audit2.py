"""
Extended audit: Test multiple ayanamsa systems and compare with external sources.
"""
import swisseph as swe
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

swe.set_ephe_path(r"C:\sweph\ephe")

birth_date = "2010-01-21"
birth_time = "08:19"
place = "Delhi, India"

from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

geolocator = Nominatim(user_agent="kundli-audit-2")
location = geolocator.geocode(place, language="en")
latitude = location.latitude
longitude = location.longitude

tf = TimezoneFinder()
timezone_str = tf.timezone_at(lat=latitude, lng=longitude)

local_dt = datetime.strptime(f"{birth_date} {birth_time}", "%Y-%m-%d %H:%M")
local_dt = local_dt.replace(tzinfo=ZoneInfo(timezone_str))
utc_dt = local_dt.astimezone(timezone.utc)

def jd_utc(dt):
    utc_dt = dt.astimezone(timezone.utc)
    return swe.julday(
        utc_dt.year, utc_dt.month, utc_dt.day,
        utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0,
        swe.GREG_CAL,
    )

jd = jd_utc(utc_dt)

print("="*80)
print(f"Birth: {birth_date} {birth_time}")
print(f"Place: {place} ({latitude:.4f}, {longitude:.4f})")
print(f"Timezone: {timezone_str}")
print(f"UTC: {utc_dt.isoformat()}")
print(f"JD: {jd}")
print("="*80)

# Test multiple ayanamsa systems
ayanamsa_systems = {
    "Lahiri": swe.SIDM_LAHIRI,
    "Fagan-Bradley": swe.SIDM_FAGAN_BRADLEY,
    "Krishnamurti": swe.SIDM_KRISHNAMURTI,
    "Yukteshwar": swe.SIDM_YUKTESHWAR,
    "J2000": swe.SIDM_J2000,
}

for ayanamsa_name, ayanamsa_id in ayanamsa_systems.items():
    print(f"\n{'='*80}")
    print(f"AYANAMSA: {ayanamsa_name}")
    print(f"{'='*80}")

    swe.set_sid_mode(ayanamsa_id, 0, 0)
    ayanamsa_value = swe.get_ayanamsa(jd)
    print(f"Ayanamsa value: {ayanamsa_value:.4f}°")

    # Calculate houses
    cusps, ascmc = swe.houses(jd, latitude, longitude, b'P')
    asc_long = ascmc[0]
    print(f"Ascendant: {asc_long:.4f}°")

    # Calculate planets
    planets = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Rahu", "Ketu"]
    for planet in planets:
        if planet == "Ketu":
            rahu_result = swe.calc_ut(jd, swe.MEAN_NODE, swe.FLG_SIDEREAL)
            rahu_long = rahu_result[0]
            if isinstance(rahu_long, tuple):
                rahu_long = rahu_long[0]
            ketu_long = (float(rahu_long) + 180.0) % 360.0
            print(f"{planet:10s}: {ketu_long:10.4f}°")
        elif planet == "Rahu":
            rahu_result = swe.calc_ut(jd, swe.MEAN_NODE, swe.FLG_SIDEREAL)
            rahu_long = rahu_result[0]
            if isinstance(rahu_long, tuple):
                rahu_long = rahu_long[0]
            print(f"{planet:10s}: {float(rahu_long):10.4f}°")
        else:
            idx_map = {
                "Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY,
                "Venus": swe.VENUS, "Mars": swe.MARS, "Jupiter": swe.JUPITER,
                "Saturn": swe.SATURN
            }
            result = swe.calc_ut(jd, idx_map[planet], swe.FLG_SIDEREAL)
            lon = result[0]
            if isinstance(lon, tuple):
                lon = lon[0]
            print(f"{planet:10s}: {float(lon):10.4f}°")

# Reset to Lahiri
swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)

print("\n" + "="*80)
print("CONCLUSION")
print("="*80)
print("\nIf reference image shows Libra ascendant (~180°),")
print("and our Lahiri calculation gives Aquarius (~319°),")
print("the difference is ~139°.")
print("\nThis is NOT an ayanamsa difference (max ~25°).")
print("This suggests:")
print("1. Different birth time")
print("2. Different birth date")
print("3. Different location")
print("4. Different house system (Whole Sign vs Placidus)")
print("5. Reference image is for a completely different person")
print("\nRecommendation: Verify the reference image birth details with the user.")
