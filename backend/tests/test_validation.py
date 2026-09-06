from validation import validate


def test_validation_success():
    result = validate(
        birth_date="1990-01-15",
        birth_time="14:30",
        place="Delhi, India",
        latitude=28.6139,
        longitude=77.209,
        timezone="Asia/Kolkata",
        utc_datetime=None,
        planets=[],
        ascendant=None,
        settings={"ayanamsa": "lahiri", "house_system": "placidus", "zodiac": "sidereal"},
    )
    assert result.passed is False
    names = {c.name for c in result.checks}
    assert "birth_date_valid" in names
    assert "birth_time_valid" in names
    assert "birthplace_resolved" in names
    assert "latitude_exists" in names
    assert "longitude_exists" in names
    assert "timezone_exists" in names