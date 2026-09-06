from unittest.mock import patch
from fastapi.testclient import TestClient

from main import app


def test_chart_endpoint_success():
    client = TestClient(app)
    payload = {"date": "2008-05-14", "time": "14:35", "place": "Delhi, India"}
    with patch("main.resolve_place") as mock_resolve:
        mock_resolve.return_value = type(
            "PlaceResult",
            (),
            {
                "status": "RESOLVED",
                "latitude": 28.6139,
                "longitude": 77.209,
                "timezone": "Asia/Kolkata",
            },
        )()
        resp = client.post("/api/chart", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "CALCULATED"
    assert data["validation"]["passed"] is True
    assert len(data["planets"]) == 9
    assert data["ascendant"] is not None


def test_chart_endpoint_bad_place():
    client = TestClient(app)
    payload = {"date": "2008-05-14", "time": "14:35", "place": "NotAPlaceXYZ123"}
    with patch("main.resolve_place") as mock_resolve:
        mock_resolve.return_value = type(
            "PlaceResult",
            (),
            {
                "status": "UNRESOLVED",
                "latitude": None,
                "longitude": None,
                "timezone": None,
            },
        )()
        resp = client.post("/api/chart", json=payload)
    assert resp.status_code == 400