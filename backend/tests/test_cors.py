"""CORS configuration: production and preview frontends must pass preflight.

The production failure this covers: OPTIONS /api/kundli returned 400 because the
deployed origin was not in the allowed list.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import main

client = TestClient(main.app)

PRODUCTION_ORIGIN = "https://kavachtoday.com"

PREFLIGHT_HEADERS = {
    "Origin": PRODUCTION_ORIGIN,
    "Access-Control-Request-Method": "POST",
    "Access-Control-Request-Headers": "content-type,authorization,x-kavach-session",
}


def test_production_preflight_for_kundli_succeeds():
    response = client.options("/api/kundli", headers=PREFLIGHT_HEADERS)

    assert response.status_code == 200, "preflight must not be rejected"
    assert response.headers["access-control-allow-origin"] == PRODUCTION_ORIGIN
    assert response.headers["access-control-allow-credentials"] == "true"

    allowed_methods = response.headers["access-control-allow-methods"].lower()
    assert "post" in allowed_methods

    allowed_headers = response.headers["access-control-allow-headers"].lower()
    for header in ("content-type", "authorization", "x-kavach-session"):
        assert header in allowed_headers, header


@pytest.mark.parametrize(
    "origin",
    [
        "https://kavachtoday.com",
        "https://www.kavachtoday.com",
        "https://kavachastrology.vercel.app",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
    ],
)
def test_trusted_origins_are_allowed(origin):
    response = client.options(
        "/api/kundli",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,authorization,x-kavach-session",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin


def test_untrusted_origin_is_still_rejected():
    response = client.options(
        "/api/kundli",
        headers={
            "Origin": "https://not-kavach.example.com",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_actual_post_response_carries_cors_headers():
    response = client.post(
        "/api/kundli",
        json={"date": "nonsense", "time": "", "latitude": 0.0, "longitude": 0.0},
        headers={"Origin": PRODUCTION_ORIGIN, "Content-Type": "application/json"},
    )
    # The payload is invalid, but the CORS headers must still be present on the
    # response so the browser can surface the error to the app.
    assert response.headers["access-control-allow-origin"] == PRODUCTION_ORIGIN
    assert response.headers["access-control-allow-credentials"] == "true"


def test_credentials_are_not_combined_with_a_wildcard_origin():
    assert "*" not in main.ALLOWED_ORIGINS
    assert "https://kavachtoday.com" in main.ALLOWED_ORIGINS
    assert "https://www.kavachtoday.com" in main.ALLOWED_ORIGINS
    assert "https://kavachastrology.vercel.app" in main.ALLOWED_ORIGINS


def test_allowed_headers_cover_authenticated_and_session_requests():
    lowered = {header.lower() for header in main.ALLOWED_HEADERS}
    assert {"content-type", "authorization", "x-kavach-session"} <= lowered
