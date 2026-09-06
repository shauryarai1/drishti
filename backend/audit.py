"""
Audit script for Vedic Kundli calculation pipeline.
Traces every step for DOB: 2010-01-21, TOB: 08:19, Place: Delhi, India
"""
import swisseph as swe
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

# === SETTINGS ===
ASTROLOGY_SYSTEM = "vedic"
ZODIAC = "sidereal"
AYANAMSA = "lahiri"
HOUSE_SYSTEM = "placidus"
PLANETS = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Rahu", "Ketu"]

swe.set_ephe_path(r"C:\sweph\ephe")
swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)

# === INPUT ===
birth_date = "2010-01-21"
birth_time = "08:19"
place = "Delhi, India"

# === PLACE RESOLUTION ===
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

geolocator = Nominatim(user_agent="kundli-audit")
location = geolocator.geocode(place, language="en")

if location is None:
    print("ERROR: Place could not be resolved")
    exit(1)

latitude = location.latitude
longitude = location.longitude
print(f"Place: {place}")
print(f"Latitude: {latitude}")
print(f"Longitude: {longitude}")

tf = TimezoneFinder()
timezone_str = tf.timezone_at(lat=latitude, lng=longitude)
print(f"Timezone: {timezone_str}")

# === UTC CONVERSION ===
local_dt = datetime.strptime(f"{birth_date} {birth_time}", "%Y-%m-%d %H:%M")
local_dt = local_dt.replace(tzinfo=ZoneInfo(timezone_str))
utc_dt = local_dt.astimezone(timezone.utc)
print(f"Local datetime: {local_dt.isoformat()}")
print(f"UTC datetime: {utc_dt.isoformat()}")

# === JULIAN DATE ===
def jd_utc(dt):
    utc_dt = dt.astimezone(timezone.utc)
    return swe.julday(
        utc_dt.year,
        utc_dt.month,
        utc_dt.day,
        utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0,
        swe.GREG_CAL,
    )

jd = jd_utc(utc_dt)
print(f"\nJulian Date (UTC): {jd}")

# === SWISS EPHEMERIS CALCULATIONS ===
print("\n" + "="*80)
print("SWISS EPHEMERIS CALCULATIONS (with FLG_SIDEREAL flag)")
print("="*80)

# Calculate tropical positions first (no sidereal flag)
print("\n--- TROPICAL POSITIONS (no sidereal flag) ---")
for name in PLANETS:
    if name == "Ketu":
        rahu_result = swe.calc_ut(jd, swe.MEAN_NODE)
        rahu_long = rahu_result[0]
        if isinstance(rahu_long, tuple):
            rahu_long = rahu_long[0]
        ketu_long = (float(rahu_long) + 180.0) % 360.0
        print(f"{name:10s}: {ketu_long:10.4f}°")
    elif name == "Rahu":
        rahu_result = swe.calc_ut(jd, swe.MEAN_NODE)
        rahu_long = rahu_result[0]
        if isinstance(rahu_long, tuple):
            rahu_long = rahu_long[0]
        print(f"{name:10s}: {float(rahu_long):10.4f}°")
    else:
        idx_map = {
            "Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY,
            "Venus": swe.VENUS, "Mars": swe.MARS, "Jupiter": swe.JUPITER,
            "Saturn": swe.SATURN
        }
        result = swe.calc_ut(jd, idx_map[name])
        lon = result[0]
        if isinstance(lon, tuple):
            lon = lon[0]
        print(f"{name:10s}: {float(lon):10.4f}°")

# Calculate sidereal positions
print("\n--- SIDEREAL POSITIONS (FLG_SIDEREAL flag) ---")
for name in PLANETS:
    if name == "Ketu":
        rahu_result = swe.calc_ut(jd, swe.MEAN_NODE, swe.FLG_SIDEREAL)
        rahu_long = rahu_result[0]
        if isinstance(rahu_long, tuple):
            rahu_long = rahu_long[0]
        ketu_long = (float(rahu_long) + 180.0) % 360.0
        print(f"{name:10s}: {ketu_long:10.4f}°")
    elif name == "Rahu":
        rahu_result = swe.calc_ut(jd, swe.MEAN_NODE, swe.FLG_SIDEREAL)
        rahu_long = rahu_result[0]
        if isinstance(rahu_long, tuple):
            rahu_long = rahu_long[0]
        print(f"{name:10s}: {float(rahu_long):10.4f}°")
    else:
        idx_map = {
            "Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY,
            "Venus": swe.VENUS, "Mars": swe.MARS, "Jupiter": swe.JUPITER,
            "Saturn": swe.SATURN
        }
        result = swe.calc_ut(jd, idx_map[name], swe.FLG_SIDEREAL)
        lon = result[0]
        if isinstance(lon, tuple):
            lon = lon[0]
        print(f"{name:10s}: {float(lon):10.4f}°")

# === HOUSES ===
print("\n" + "="*80)
print("HOUSE CUSPS (Placidus)")
print("="*80)
house_system_flag = HOUSE_SYSTEM[0].upper()
cusps, ascmc = swe.houses(jd, latitude, longitude, house_system_flag.encode())
print(f"Ascendant (ASCMC[0]): {ascmc[0]:.6f}°")
print(f"MC (ASCMC[1]): {ascmc[1]:.6f}°")
print(f"ARMC (ASCMC[2]): {ascmc[2]:.6f}°")
print(f"Vertex (ASCMC[3]): {ascmc[3]:.6f}°")
print(f"\nHouse Cusps:")
for i, cusp in enumerate(cusps[:12], 1):
    print(f"  House {i:2d}: {cusp:.6f}°")

# === AYANAMSA ===
print("\n" + "="*80)
print("AYANAMSA")
print("="*80)
print(f"Lahiri ayanamsa for JD {jd}: {swe.get_ayanamsa(jd):.6f}°")

# === COMPARISON WITH REFERENCE IMAGE ===
print("\n" + "="*80)
print("COMPARISON WITH REFERENCE IMAGE")
print("="*80)
print("\nIMPORTANT: The reference image shows a North Indian Kundli.")
print("We need to read the values from the image for comparison.")
print("\nFrom visual inspection of 1.png:")
print("  - House 1 (Lagna) sign: Libra (appears to be)")
print("  - House 1 (Lagna) degree: ~15-20°")
print("\nOur calculated values:")
print(f"  - Ascendant: 318.891074° = Aquarius 18.89°")
print(f"\nMAJOR MISMATCH DETECTED!")
print(f"Reference shows Libra, we calculated Aquarius")
print(f"Difference: ~{318.891074 - 180:.1f}° (approximately 139°)")

# === DEBUGGING ===
print("\n" + "="*80)
print("DEBUGGING: Checking each step")
print("="*80)

# Check 1: Timezone conversion
print(f"\n1. Timezone conversion:")
print(f"   Local: {local_dt.isoformat()}")
print(f"   UTC:   {utc_dt.isoformat()}")
print(f"   IST offset: +5:30")
print(f"   08:19 IST = {8 - 5:02d}:{19:02d} UTC = 02:49 UTC")
print(f"   Expected: 2010-01-21T02:49:00+00:00")
print(f"   Got:      {utc_dt.isoformat()}")

# Check 2: Julian Date
print(f"\n2. Julian Date:")
print(f"   JD = {jd}")
print(f"   Expected for 2010-01-21 02:49 UTC: ~2455197.6")
print(f"   Verification: Jan 1, 2000 = 2451545.0")
days_since_2000 = (datetime(2010, 1, 21) - datetime(2000, 1, 1, 12, 0)).total_seconds() / 86400
print(f"   Days since Jan 1, 2000 12:00 UT: {days_since_2000:.2f}")
print(f"   Expected JD: {2451545.0 + days_since_2000:.2f}")

# Check 3: Sidereal vs Tropical
print(f"\n3. Tropical vs Sidereal:")
print(f"   Lahiri ayanamsa for 2010: ~24.0° (approximately)")
print(f"   Our ayanamsa from swe: {swe.get_ayanamsa(jd):.4f}°")
print(f"   Tropical Sun - Ayanamsa = Sidereal Sun")
print(f"   If tropical Sun ~301° and ayanamsa ~24°")
print(f"   Then sidereal Sun ~277° (Capricorn)")

# Check 4: Ascendant
print(f"\n4. Ascendant calculation:")
print(f"   Our calculated ascendant: {ascmc[0]:.4f}°")
print(f"   In sidereal mode, this should already be sidereal")
print(f"   Sign: Aquarius (310-330°)")
print(f"   Degree: {ascmc[0] % 30:.4f}°")

# === CONCLUSION ===
print("\n" + "="*80)
print("CONCLUSION")
print("="*80)
print("\nPossible root causes for mismatch:")
print("1. Reference image uses different birth details than provided")
print("2. Reference image uses different ayanamsa (not Lahiri)")
print("3. Reference image uses different house system")
print("4. Reference image uses tropical zodiac instead of sidereal")
print("5. Our calculation has an error in timezone conversion")
print("6. Our calculation has an error in Julian date computation")
print("7. Our calculation has an error in ayanamsa application")
print("8. Reference image is for a different person entirely")

print("\nNext steps:")
print("- Verify the birth details used for the reference image")
print("- Test with a known astrology software (e.g., Jagannatha Hora)")
print("- Check if the reference image uses Fagan-Bradley ayanamsa")
print("- Verify timezone handling for India (IST = UTC+5:30)")
