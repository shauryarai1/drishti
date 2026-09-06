from models import PlanetData, HouseData, AscendantData


# Whole-sign house assignment: house 1 is the sign of the ascendant,
# house 2 is the next sign, etc.
SIGN_ORDER = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]


def _sign_index(sign: str) -> int:
    return SIGN_ORDER.index(sign)


def assign_houses(ascendant_sign: str, planet_signs: dict[str, str]) -> dict[str, int]:
    asc_index = _sign_index(ascendant_sign)
    houses: dict[str, int] = {}
    for planet, sign in planet_signs.items():
        diff = (_sign_index(sign) - asc_index) % 12
        houses[planet] = diff + 1
    return houses


def build_ascendant(longitude: float) -> AscendantData:
    from rashi import longitude_to_rashi

    sign, _, degree = longitude_to_rashi(longitude)
    return AscendantData(
        longitude=round(longitude, 6),
        sign=sign,
        house=1,
        degree=round(degree, 6),
    )


def build_houses_list(ascendant_sign: str, cusp_longitudes: list[float]) -> list[HouseData]:
    asc_index = _sign_index(ascendant_sign)
    houses: list[HouseData] = []
    for i in range(12):
        sign_index = (asc_index + i) % 12
        sign_name = SIGN_ORDER[sign_index]
        cusp = cusp_longitudes[i] if i < len(cusp_longitudes) else sign_index * 30.0
        houses.append(
            HouseData(
                number=i + 1,
                sign=sign_name,
                cusp_longitude=round(cusp, 6),
            )
        )
    return houses