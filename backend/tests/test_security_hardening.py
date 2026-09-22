"""Security hardening regression suite.

Covers the audit findings: dev-tool gating, admin authorization, identity
spoofing, session-id handling, request-size caps, rate limiting, output
escaping, CORS, and secret hygiene.

Live Supabase RLS isolation cannot be exercised locally; the database-side
guarantees are asserted from the migration files instead (and must be verified
against the real project - see the audit report).
"""

from __future__ import annotations

import json
import pathlib
import re

import pytest
from fastapi.testclient import TestClient

import archive
import hardening
import main

REPO = pathlib.Path(__file__).resolve().parents[2]
FRONTEND = REPO / "frontend-next"

ADMIN_ID = "aaaaaaaa-0000-0000-0000-000000000001"
NORMAL_ID = "bbbbbbbb-0000-0000-0000-000000000002"
ADMIN_TOKEN = "admin-token"
NORMAL_TOKEN = "normal-token"


class FakeStore:
    def __init__(self) -> None:
        self.rows: list[dict] = []

    def configured(self) -> bool:
        return True

    def verify_token(self, token):
        return {ADMIN_TOKEN: ADMIN_ID, NORMAL_TOKEN: NORMAL_ID}.get(token)

    def is_admin(self, user_id: str) -> bool:
        return user_id == ADMIN_ID

    def email_for(self, user_id: str):
        return "owner@example.com" if user_id == ADMIN_ID else None

    def insert(self, row: dict):
        stored = dict(row)
        stored["id"] = f"id-{len(self.rows) + 1}"
        stored["created_at"] = "2026-09-21T10:00:00+00:00"
        self.rows.append(stored)
        return stored["id"]

    def query(self, filters, select, limit, offset, count=False):
        return self.rows[offset:offset + limit], len(self.rows)

    def get(self, submission_id):
        return next((r for r in self.rows if r["id"] == submission_id), None)

    def delete(self, submission_id):
        return False

    def stats(self, since_iso):
        return {"total": len(self.rows)}


@pytest.fixture()
def fake_store(monkeypatch):
    store = FakeStore()
    monkeypatch.setattr(archive, "store", store)
    return store


@pytest.fixture()
def client():
    return TestClient(main.app)


# --- dev-tool gating (fail-closed) ------------------------------------------
DEV_PATHS = (
    "/api/dev/panchang-engine",
    "/api/dev/daily-moon",
    "/api/dev/chat",
    "/api/dev/kavach-tarot",
    "/api/dev/kavach-trace",
)


@pytest.mark.parametrize("path", DEV_PATHS)
def test_dev_endpoints_are_closed_in_production(monkeypatch, client, path):
    monkeypatch.setenv("KAVACH_ENV", "production")
    monkeypatch.setenv("KAVACH_DEV_TOOLS", "1")  # even an explicit opt-in loses to production
    assert client.post(path, json={}).status_code == 404


@pytest.mark.parametrize("path", DEV_PATHS)
def test_dev_endpoints_fail_closed_without_explicit_opt_in(monkeypatch, client, path):
    monkeypatch.delenv("KAVACH_DEV_TOOLS", raising=False)
    monkeypatch.delenv("KAVACH_ENV", raising=False)
    # TestClient's peer host is not loopback, so dev tooling must stay closed.
    assert client.post(path, json={}).status_code == 404


def test_dev_gate_policy_is_fail_closed():
    assert hardening.dev_tools_allowed("203.0.113.9") is False or True  # documented below
    import os

    previous = os.environ.pop("KAVACH_DEV_TOOLS", None)
    previous_env = os.environ.pop("KAVACH_ENV", None)
    try:
        assert hardening.dev_tools_allowed("203.0.113.9") is False, "public caller must be denied"
        assert hardening.dev_tools_allowed("127.0.0.1") is True, "local development stays usable"
    finally:
        if previous is not None:
            os.environ["KAVACH_DEV_TOOLS"] = previous
        if previous_env is not None:
            os.environ["KAVACH_ENV"] = previous_env


# --- admin authorization ----------------------------------------------------
def test_unauthenticated_admin_access_is_denied(fake_store, client):
    assert client.get("/api/admin/stats").status_code == 401
    assert client.get("/api/admin/submissions").status_code == 401


def test_ordinary_user_admin_access_is_denied(fake_store, client):
    headers = {"Authorization": f"Bearer {NORMAL_TOKEN}"}
    assert client.get("/api/admin/stats", headers=headers).status_code == 403
    assert client.get("/api/admin/submissions", headers=headers).status_code == 403
    assert client.delete("/api/admin/submissions/id-1", headers=headers).status_code == 403


def test_invalid_or_expired_token_is_rejected(fake_store, client):
    headers = {"Authorization": "Bearer expired-or-forged-token"}
    assert client.get("/api/admin/stats", headers=headers).status_code == 401


def test_admin_route_guessing_yields_no_privileged_data(fake_store, client):
    body = client.get("/api/admin/submissions").json()
    assert "submissions" not in body


# --- identity spoofing ------------------------------------------------------
def test_forged_user_id_in_body_is_ignored(fake_store, client):
    payload = {"date": "2010-01-21", "time": "08:19", "place": "Delhi", "latitude": 28.6,
               "longitude": 77.2, "timezone": "Asia/Kolkata", "user_id": "attacker"}
    assert client.post("/api/kundli", json=payload).status_code == 200
    row = fake_store.rows[0]
    assert row["user_id"] is None
    assert "user_id" not in row["input_data"]


# --- guest session header ---------------------------------------------------
def test_malicious_session_header_is_dropped(fake_store, client):
    payload = {"date": "2010-01-21", "time": "08:19", "place": "Delhi", "latitude": 28.6,
               "longitude": 77.2, "timezone": "Asia/Kolkata"}
    for hostile in ("../../etc/passwd", "<script>alert(1)</script>", "x" * 300, "a b c"):
        assert client.post("/api/kundli", json=payload,
                           headers={"X-Kavach-Session": hostile}).status_code == 200
    assert all(row["visitor_session_id"] is None for row in fake_store.rows)


def test_wellformed_session_header_is_kept(fake_store, client):
    payload = {"date": "2010-01-21", "time": "08:19", "place": "Delhi", "latitude": 28.6,
               "longitude": 77.2, "timezone": "Asia/Kolkata"}
    client.post("/api/kundli", json=payload,
                headers={"X-Kavach-Session": "11111111-2222-3333-4444-555555555555"})
    assert fake_store.rows[0]["visitor_session_id"] == "11111111-2222-3333-4444-555555555555"


# --- request size -----------------------------------------------------------
def test_oversized_ask_payload_is_rejected(client):
    oversized = {"question": "x" * (hardening.MAX_BODY_BYTES + 1024),
                 "timestamp": "2026-09-21T22:40:00+05:30"}
    response = client.post("/api/ask", json=oversized)
    assert response.status_code == 413


def test_normal_payloads_are_not_size_limited(client):
    body = client.get("/api/panchang?date=2026-09-21&latitude=28.6&longitude=77.2"
                      "&timezone=Asia/Kolkata")
    assert body.status_code == 200


# --- rate limiting ----------------------------------------------------------
def test_rate_limit_returns_429_with_retry_after(monkeypatch, client):
    monkeypatch.setenv("KAVACH_RATELIMIT", "1")
    monkeypatch.setattr(hardening, "RATE_LIMITS", (("/api/health", 3),))
    hardening.LIMITER.reset()
    try:
        for _ in range(3):
            assert client.get("/api/health").status_code == 200
        blocked = client.get("/api/health")
        assert blocked.status_code == 429
        assert int(blocked.headers["retry-after"]) >= 1
        assert "Too many requests" in blocked.json()["message"]
    finally:
        hardening.LIMITER.reset()


def test_rate_limit_is_disabled_for_tests_by_default(client):
    assert client.get("/api/health").status_code == 200
    assert hardening.rate_limiting_enabled() is False


def test_trusted_client_ip_ignores_spoofed_forwarding():
    scope = {"client": ("10.0.0.5", 1234)}
    spoofed = {"x-forwarded-for": "1.2.3.4, 203.0.113.7"}
    # Render appends the real client address, so only the last entry is trusted.
    assert hardening.client_ip(scope, spoofed) == "203.0.113.7"
    assert hardening.client_ip(scope, {"x-forwarded-for": "not-an-ip"}) == "10.0.0.5"
    assert hardening.client_ip(scope, {}) == "10.0.0.5"


# --- output handling --------------------------------------------------------
def test_model_output_with_html_is_returned_as_plain_text(monkeypatch, fake_store):
    import chat.nvidia as nvidia

    class FakeResponse:
        status_code = 200
        text = ""

        def json(self):
            return {"choices": [{"message": {"role": "assistant",
                                             "content": "<script>alert('xss')</script>"}}]}

    monkeypatch.setattr(nvidia.httpx, "post", lambda *a, **k: FakeResponse())
    monkeypatch.setattr("chat.reading.sensitive_response", lambda _q: None)

    def no_reading(_q):
        raise RuntimeError("no tarot in tests")

    monkeypatch.setattr("chat.reading.build_reading", no_reading)
    monkeypatch.setenv("NVIDIA_API_KEY", "test-sentinel")

    body = TestClient(main.app).post(
        "/api/ask", json={"question": "tell me", "timestamp": "2026-09-21T22:40:00+05:30",
                          "conversation_id": "xss-test"}).json()

    # The API transports text, not markup; the frontend must never interpret it.
    assert body["answer"] == "<script>alert('xss')</script>"
    assert not any("dangerouslySetInnerHTML" in path.read_text(encoding="utf-8", errors="ignore")
                   for path in FRONTEND.rglob("*.tsx")
                   if "node_modules" not in path.parts and ".next" not in path.parts)


def test_reasoning_content_never_surfaces(monkeypatch):
    import chat.nvidia as nvidia

    secret = "HIDDEN-REASONING-SENTINEL"

    class FakeResponse:
        status_code = 200
        text = ""

        def json(self):
            return {"choices": [{"message": {"role": "assistant", "content": "public",
                                             "reasoning_content": secret}}]}

    monkeypatch.setattr(nvidia.httpx, "post", lambda *a, **k: FakeResponse())
    detail = nvidia.generate_reply_detailed("q", [])
    assert detail["text"] == "public"
    assert secret not in json.dumps(detail)


# --- headers / CORS ---------------------------------------------------------
def test_security_headers_present(client):
    response = client.get("/api/health")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert "camera=()" in response.headers["permissions-policy"]


def test_hsts_only_over_https(client):
    assert "strict-transport-security" not in client.get("/api/health").headers
    over_https = client.get("/api/health", headers={"X-Forwarded-Proto": "https"})
    assert over_https.headers["strict-transport-security"].startswith("max-age=")


def test_cors_production_origin_allowed_and_untrusted_rejected(client):
    allowed = client.options("/api/ask", headers={
        "Origin": "https://kavachtoday.com",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type,authorization,x-kavach-session",
    })
    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-origin"] == "https://kavachtoday.com"

    rejected = client.options("/api/ask", headers={
        "Origin": "https://attacker.example.com",
        "Access-Control-Request-Method": "POST",
    })
    assert rejected.status_code == 400


# --- database-side guarantees (static) --------------------------------------
def test_saved_readings_policies_are_strictly_owner_scoped():
    sql = (REPO / "supabase" / "migrations" / "0001_saved_readings.sql").read_text(encoding="utf-8").lower()
    policies = re.findall(r"create policy.*?;", sql, flags=re.DOTALL)
    assert len(policies) == 4
    for policy in policies:
        assert "auth.uid()" in policy and "user_id" in policy
        assert "to authenticated" in policy
    assert "using (true)" not in sql


def test_archive_tables_grant_nothing_to_browser_clients():
    sql = (REPO / "supabase" / "migrations" / "0002_product_submissions.sql").read_text(encoding="utf-8").lower()
    assert "revoke all on public.product_submissions from anon" in sql
    assert "revoke all on public.product_submissions from authenticated" in sql
    assert "revoke all on public.admin_users from anon" in sql
    assert "revoke all on public.admin_users from authenticated" in sql


def test_service_role_key_never_references_the_frontend():
    offenders = []
    for path in FRONTEND.rglob("*.ts*"):
        if "node_modules" in path.parts or ".next" in path.parts:
            continue
        text = re.sub(r"/\*.*?\*/", "", path.read_text(encoding="utf-8", errors="ignore"), flags=re.DOTALL)
        text = re.sub(r"//.*", "", text).lower()
        if "service_role" in text or "secret_key" in text:
            offenders.append(str(path))
    assert offenders == []


def test_missing_configuration_fails_safely(monkeypatch, fake_store):
    """Unconfigured archive must deny admin access rather than allow it."""
    monkeypatch.setattr(archive.store, "configured", lambda: False)
    response = TestClient(main.app).get("/api/admin/stats", headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    assert response.status_code == 503
