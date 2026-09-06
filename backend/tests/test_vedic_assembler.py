from vedic_assembler import assign_houses, build_ascendant, build_houses_list


def test_assign_houses_whole_sign():
    ascendant_sign = "Leo"
    planet_signs = {
        "Sun": "Leo",
        "Mars": "Cancer",
        "Jupiter": "Sagittarius",
    }
    houses = assign_houses(ascendant_sign, planet_signs)
    assert houses["Sun"] == 1
    assert houses["Mars"] == 12
    assert houses["Jupiter"] == 5


def test_build_ascendant():
    asc = build_ascendant(123.456)
    assert asc.sign == "Leo"
    assert asc.house == 1
    assert 0 <= asc.degree < 30


def test_build_houses_list():
    houses = build_houses_list("Leo", [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330])
    assert len(houses) == 12
    assert houses[0].number == 1