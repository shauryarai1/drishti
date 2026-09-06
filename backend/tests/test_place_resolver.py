from unittest.mock import patch

import pytest

from place_resolver import resolve_place


@patch("place_resolver.Nominatim")
@patch("place_resolver.TimezoneFinder")
def test_resolve_delhi(mock_tf_cls, mock_nominatim_cls):
    mock_nominatim_cls.return_value.geocode.return_value = type(
        "Loc", (), {"latitude": 28.6139, "longitude": 77.209}
    )()
    mock_tf_cls.return_value.timezone_at.return_value = "Asia/Kolkata"

    result = resolve_place("Delhi, India")
    assert result.status == "RESOLVED"
    assert result.latitude == pytest.approx(28.6139, abs=0.01)
    assert result.longitude == pytest.approx(77.209, abs=0.01)
    assert result.timezone == "Asia/Kolkata"


@patch("place_resolver.Nominatim")
@patch("place_resolver.TimezoneFinder")
def test_resolve_unknown(mock_tf_cls, mock_nominatim_cls):
    mock_nominatim_cls.return_value.geocode.return_value = None
    result = resolve_place("UnknownPlaceXYZ")
    assert result.status == "UNRESOLVED"
    assert result.latitude is None