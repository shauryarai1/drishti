from datetime import date, datetime
from typing import List, Optional

from models import ValidationCheck, ValidationResult


REQUIRED_PLANETS = [
    "Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Rahu", "Ketu"
]


def _check(name: str, passed: bool, detail: str = "") -> ValidationCheck:
    return ValidationCheck(name=name, passed=passed, detail=detail or None)


def validate(
    *,
    birth_date: Optional[str],
    birth_time: Optional[str],
    place: Optional[str],
    latitude: Optional[float],
    longitude: Optional[float],
    timezone: Optional[str],
    utc_datetime: Optional[datetime],
    planets: Optional[List[dict]],
    ascendant: Optional[dict],
    settings: Optional[dict],
) -> ValidationResult:
    checks: List[ValidationCheck] = []

    # 1. Birth date valid
    if birth_date:
        try:
            date.fromisoformat(birth_date)
            checks.append(_check("birth_date_valid", True))
        except Exception as exc:
            checks.append(_check("birth_date_valid", False, str(exc)))
    else:
        checks.append(_check("birth_date_valid", False, "missing"))

    # 2. Birth time valid
    if birth_time:
        try:
            datetime.strptime(birth_time, "%H:%M")
            checks.append(_check("birth_time_valid", True))
        except Exception as exc:
            checks.append(_check("birth_time_valid", False, str(exc)))
    else:
        checks.append(_check("birth_time_valid", False, "missing"))

    # 3-6. Place resolved
    checks.append(_check("birthplace_resolved", place is not None and len(place.strip()) > 0, "missing" if not place else None))
    checks.append(_check("latitude_exists", latitude is not None, "missing" if latitude is None else None))
    checks.append(_check("longitude_exists", longitude is not None, "missing" if longitude is None else None))
    checks.append(_check("timezone_exists", timezone is not None, "missing" if timezone is None else None))

    # 7. UTC conversion valid
    if utc_datetime is not None:
        checks.append(_check("utc_conversion_valid", True))
    else:
        checks.append(_check("utc_conversion_valid", False, "missing"))

    # 8-10. Swiss Ephemeris / planet data
    checks.append(_check("ephemeris_available", planets is not None and len(planets) == len(REQUIRED_PLANETS)))
    checks.append(_check("ascendant_calculated", ascendant is not None))
    checks.append(_check("planets_calculated", all(p.get("status") == "CALCULATED" for p in planets or [])))

    # 11-13. Settings explicitly set
    if settings:
        checks.append(_check("ayanamsa_set", settings.get("ayanamsa") is not None, settings.get("ayanamsa")))
        checks.append(_check("house_system_set", settings.get("house_system") is not None, settings.get("house_system")))
        checks.append(_check("zodiac_system_set", settings.get("zodiac") == "sidereal", settings.get("zodiac")))
    else:
        checks.append(_check("ayanamsa_set", False, "missing"))
        checks.append(_check("house_system_set", False, "missing"))
        checks.append(_check("zodiac_system_set", False, "missing"))

    # 14. No required value missing
    required_checks = [
        birth_date, birth_time, place, latitude, longitude, timezone,
        utc_datetime, planets, ascendant, settings
    ]
    checks.append(_check("no_missing_required_values", all(v is not None for v in required_checks)))

    passed = all(c.passed for c in checks)
    return ValidationResult(passed=passed, checks=checks)