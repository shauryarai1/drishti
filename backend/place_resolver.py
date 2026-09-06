from timezonefinder import TimezoneFinder
from geopy.geocoders import Nominatim

from models import PlaceResult


def resolve_place(place: str, country_hint: str = "") -> PlaceResult:
    geolocator = Nominatim(user_agent="kundli-app")
    query = place if not country_hint else f"{place}, {country_hint}"

    location = geolocator.geocode(query, language="en")

    if location is None:
        return PlaceResult(
            place=place,
            latitude=None,
            longitude=None,
            timezone=None,
            status="UNRESOLVED",
        )

    tf = TimezoneFinder()
    timezone = tf.timezone_at(lat=location.latitude, lng=location.longitude)

    return PlaceResult(
        place=place,
        latitude=location.latitude,
        longitude=location.longitude,
        timezone=timezone,
        status="RESOLVED",
    )