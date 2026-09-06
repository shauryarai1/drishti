from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from config import AYANAMSA, HOUSE_SYSTEM, ZODIAC, ASTROLOGY_SYSTEM


def format_debug(*, birth, utc_datetime, settings, planets, houses, ascendant, validation):
    lines = []
    lines.append("DEBUG")
    lines.append("────────────────────────")

    lines.append(f"Birth: {birth['date']}")
    lines.append(f"Time: {birth['time']}")
    lines.append(f"Place: {birth['place']}")
    lines.append(f"Latitude: {birth['latitude']}")
    lines.append(f"Longitude: {birth['longitude']}")
    lines.append(f"Timezone: {birth['timezone']}")
    lines.append(f"UTC: {utc_datetime.isoformat()}")
    lines.append("")
    lines.append(f"System: {settings.get('system', ASTROLOGY_SYSTEM)}")
    lines.append(f"Zodiac: {settings.get('zodiac', ZODIAC)}")
    lines.append(f"Ayanamsa: {settings.get('ayanamsa', AYANAMSA)}")
    lines.append(f"House System: {settings.get('house_system', HOUSE_SYSTEM)}")
    lines.append("")

    for p in planets:
        lines.append(f"{p['name']}:")
        lines.append(f"  Longitude: {p['longitude']}°")
        lines.append(f"  Sign: {p['sign']}")
        lines.append(f"  House: {p['house']}")
        lines.append(f"  Nakshatra: {p.get('nakshatra')}")
        lines.append(f"  Source: {p['source']}")
        lines.append(f"  Status: {p['status']}")
        lines.append("")

    if ascendant:
        lines.append(f"Ascendant:")
        lines.append(f"  Longitude: {ascendant['longitude']}°")
        lines.append(f"  Sign: {ascendant['sign']}")
        lines.append("")

    lines.append("Validation:")
    for c in validation.get("checks", []):
        status = "PASS" if c["passed"] else "FAIL"
        lines.append(f"  [{status}] {c['name']}")
        if c.get("detail"):
            lines.append(f"         {c['detail']}")

    lines.append("────────────────────────")
    return "\n".join(lines)