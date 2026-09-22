"""KAVACH admin identity: verified account user vs reading person.

Tests never touch production Supabase: the archive store is replaced with an
in-memory fake, exactly like the existing archive-isolation fixtures.
"""

from __future__ import annotations

import pathlib

import pytest
from fastapi.testclient import TestClient

import archive
import main

REPO = pathlib.Path(__file__).resolve().parents[2]
FRONTEND = REPO / "frontend-next"

ACCOUNT_ID = "11111111-1111-1111-1111-111111111111"
OTHER_ID = "22222222-2222-2222-2222-222222222222"
GOOGLE_ID = "33333333-3333-3333-3333-333333333333"

TOKEN = "verified-session-token"
OTHER_TOKEN = "other-session-token"
GOOGLE_TOKEN = "google-session-token"

FIXTURE = {
    "date": "2010-01-21", "time": "08:19", "place": "Delhi",
    "latitude": 28.6139, "longitude": 77.209, "timezone": "Asia/Kolkata",
    "name": "Trishna Rai",
}


class FakeStore:
    """In-memory stand-in for the Supabase archive store."""

    def __init__(self):
        self.rows: list[dict] = []
        self.admins = {ACCOUNT_ID}
        self.profiles = {
            ACCOUNT_ID: {"email": "shaurya@example.com", "name": "Shaurya Rai"},
            GOOGLE_ID: {"email": "google@example.com", "name": "Google User"},
            OTHER_ID: {"email": "other@example.com", "name": None},
        }

    def configured(self):
        return True

    def insert(self, row):
        stored = dict(row)
        # Hex-shaped ids so the admin detail route's id validation accepts them.
        stored["id"] = f"{len(self.rows) + 1:08x}-0000-4000-8000-000000000000"
        self.rows.append(stored)
        return stored["id"]

    def verify_token(self, token):
        return {
            TOKEN: ACCOUNT_ID,
            OTHER_TOKEN: OTHER_ID,
            GOOGLE_TOKEN: GOOGLE_ID,
        }.get(token)

    def is_admin(self, user_id):
        return user_id in self.admins

    def email_for(self, user_id):
        profile = self.profiles.get(user_id)
        return profile.get("email") if profile else None

    def profile_for(self, user_id):
        return self.profiles.get(user_id)

    def query(self, filters, select, limit, offset, count=False):
        rows = [dict(row) for row in self.rows]
        if filters.get("user_id") == "is.null":
            rows = [row for row in rows if not row.get("user_id")]
        elif filters.get("user_id") == "not.is.null":
            rows = [row for row in rows if row.get("user_id")]
        if filters.get("product"):
            wanted = filters["product"].split(".", 1)[-1]
            rows = [row for row in rows if row.get("product") == wanted]
        return rows[offset:offset + limit], len(rows)

    def get(self, submission_id):
        for row in self.rows:
            if row["id"] == submission_id:
                return dict(row)
        return None

    def delete(self, submission_id):
        return False

    def stats(self, since_iso):
        return {"total": len(self.rows)}


@pytest.fixture()
def store(monkeypatch):
    fake = FakeStore()
    monkeypatch.setattr(archive, "store", fake)
    monkeypatch.setenv("KAVACH_ARCHIVE", "1")
    monkeypatch.setenv("KAVACH_RATELIMIT", "0")
    archive.set_request_identity(None, None)
    yield fake
    archive.set_request_identity(None, None)


def _ask(client, path, payload, token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return client.post(path, json=payload, headers=headers)


# --- 1-4: authenticated products archive the verified user -------------------
def test_authenticated_kundli_request_archives_the_verified_user(store):
    client = TestClient(main.app)
    response = _ask(client, "/api/kundli", FIXTURE, token=TOKEN)
    assert response.status_code == 200

    rows = [row for row in store.rows if row["product"] == "kundli"]
    assert rows, "the Kundli submission must be archived"
    assert rows[-1]["user_id"] == ACCOUNT_ID, "verified identity, not Guest"


@pytest.mark.parametrize("product", ["reading", "life_summary", "weekly", "kundli"])
def test_every_personalized_product_archives_the_verified_user(store, product):
    """Every archive write goes through one verified-identity path."""
    archive.set_request_identity(TOKEN, None)
    archive.record_submission(product, {"date": "2010-01-21"}, {"ok": True})
    assert store.rows[-1]["user_id"] == ACCOUNT_ID, product


def test_frontend_sends_the_bearer_token_for_every_gated_product():
    helper = (FRONTEND / "lib" / "authHeaders.ts").read_text(encoding="utf-8")
    assert "Authorization: `Bearer ${token}`" in helper
    assert "getSession()" in helper, "the existing session architecture is reused"

    for name in ("api.ts", "kundli.ts", "weekly.ts"):
        source = (FRONTEND / "lib" / name).read_text(encoding="utf-8")
        assert "authHeaders" in source, name
    life = (FRONTEND / "app" / "life-summary" / "page.tsx").read_text(encoding="utf-8")
    assert "authHeaders" in life
    # The token is never put in a URL.
    for source in (helper, life):
        assert "?token" not in source and "access_token=" not in source


# --- 5-6: login method is irrelevant ----------------------------------------
def test_google_and_password_users_are_treated_identically(store):
    archive.set_request_identity(GOOGLE_TOKEN, None)
    archive.record_submission("kundli", {}, {"ok": True})
    archive.set_request_identity(TOKEN, None)
    archive.record_submission("kundli", {}, {"ok": True})

    assert [row["user_id"] for row in store.rows] == [GOOGLE_ID, ACCOUNT_ID]
    # Identity is resolved from a verified Supabase user, not a login method.
    source = (REPO / "backend" / "archive.py").read_text(encoding="utf-8")
    assert "store.verify_token(token)" in source
    assert "signInWithOAuth" not in source


# --- 7-9: forged / invalid / guest ------------------------------------------
def test_forged_browser_identity_is_ignored(store):
    archive.set_request_identity(TOKEN, None)
    archive.record_submission(
        "kundli",
        {"date": "2010-01-21", "user_id": OTHER_ID, "email": "evil@example.com", "name": "Fake"},
        {"ok": True},
    )
    row = store.rows[-1]
    assert row["user_id"] == ACCOUNT_ID, "must come from the verified token"
    # Browser-supplied identity fields are not even stored.
    assert "user_id" not in row["input_data"]
    assert "email" not in row["input_data"]


def test_invalid_bearer_token_is_not_authenticated(store):
    archive.set_request_identity("forged-token", None)
    archive.record_submission("kundli", {}, {"ok": True})
    assert store.rows[-1]["user_id"] is None


def test_guest_request_remains_null(store):
    archive.set_request_identity(None, None)
    archive.record_submission("kundli", {}, {"ok": True})
    assert store.rows[-1]["user_id"] is None


# --- 10-11: admin list and detail show identity -----------------------------
def test_admin_list_shows_the_authenticated_identity(store):
    archive.set_request_identity(TOKEN, None)
    archive.record_submission("kundli", {"name": "Trishna Rai", "date": "2010-01-21"}, {"ok": True})

    body = TestClient(main.app).get(
        "/api/admin/submissions", headers={"Authorization": f"Bearer {TOKEN}"}
    ).json()
    row = body["submissions"][0]
    assert row["account_name"] == "Shaurya Rai"
    assert row["account_email"] == "shaurya@example.com"
    assert row["user_id"] == ACCOUNT_ID


def test_admin_detail_shows_the_authenticated_identity(store):
    archive.set_request_identity(TOKEN, None)
    archive.record_submission("kundli", {"name": "Trishna Rai"}, {"ok": True})
    submission_id = store.rows[-1]["id"]

    body = TestClient(main.app).get(
        f"/api/admin/submissions/{submission_id}",
        headers={"Authorization": f"Bearer {TOKEN}"},
    ).json()
    detail = body["submission"]
    assert detail["account_name"] == "Shaurya Rai"
    assert detail["account_email"] == "shaurya@example.com"


# --- 12-13: display-name fallback -------------------------------------------
def test_display_name_is_used_and_missing_name_falls_back_to_email(store):
    archive.set_request_identity(TOKEN, None)
    archive.record_submission("kundli", {}, {"ok": True})
    archive.set_request_identity(OTHER_TOKEN, None)
    archive.record_submission("kundli", {}, {"ok": True})

    body = TestClient(main.app).get(
        "/api/admin/submissions", headers={"Authorization": f"Bearer {TOKEN}"}
    ).json()
    by_user = {row["user_id"]: row for row in body["submissions"]}
    assert by_user[ACCOUNT_ID]["account_name"] == "Shaurya Rai"
    assert by_user[OTHER_ID]["account_name"] is None
    assert by_user[OTHER_ID]["account_email"] == "other@example.com"


# --- 14-15: historical rows --------------------------------------------------
def test_historical_null_user_id_stays_guest(store):
    store.rows.append({"id": "row-old", "product": "kundli", "user_id": None,
                       "input_data": {}, "created_at": "2026-01-01T00:00:00+00:00"})
    body = TestClient(main.app).get(
        "/api/admin/submissions", headers={"Authorization": f"Bearer {TOKEN}"}
    ).json()
    row = body["submissions"][0]
    assert row["user_id"] is None
    assert row["account_name"] is None and row["account_email"] is None


def test_historical_valid_user_id_resolves_identity(store):
    store.rows.append({"id": "row-old-2", "product": "kundli", "user_id": ACCOUNT_ID,
                       "input_data": {}, "created_at": "2026-01-01T00:00:00+00:00"})
    body = TestClient(main.app).get(
        "/api/admin/submissions", headers={"Authorization": f"Bearer {TOKEN}"}
    ).json()
    row = body["submissions"][0]
    assert row["account_name"] == "Shaurya Rai"
    assert row["account_email"] == "shaurya@example.com"


# --- 16-17: Reading For vs account ------------------------------------------
def test_person_name_is_shown_separately_and_never_replaces_the_account(store):
    archive.set_request_identity(TOKEN, None)
    archive.record_submission("kundli", {"name": "Trishna Rai", "date": "2010-01-21"}, {"ok": True})

    body = TestClient(main.app).get(
        "/api/admin/submissions", headers={"Authorization": f"Bearer {TOKEN}"}
    ).json()
    row = body["submissions"][0]
    assert row["person_name"] == "Trishna Rai"
    assert row["account_name"] == "Shaurya Rai", "the account name must not be replaced"


def test_non_kundli_products_do_not_report_a_person_name(store):
    archive.set_request_identity(TOKEN, None)
    archive.record_submission("reading", {"name": "not a person field"}, {"ok": True})
    body = TestClient(main.app).get(
        "/api/admin/submissions", headers={"Authorization": f"Bearer {TOKEN}"}
    ).json()
    assert body["submissions"][0]["person_name"] is None


def test_historical_kundli_without_person_name_is_handled(store):
    store.rows.append({"id": "row-old-3", "product": "kundli", "user_id": ACCOUNT_ID,
                       "input_data": {"date": "2010-01-21"}, "created_at": "2026-01-01T00:00:00+00:00"})
    body = TestClient(main.app).get(
        "/api/admin/submissions", headers={"Authorization": f"Bearer {TOKEN}"}
    ).json()
    assert body["submissions"][0]["person_name"] is None


# --- 18: no tokens anywhere --------------------------------------------------
def test_no_token_ever_reaches_the_archive_or_the_admin_payload(store):
    archive.set_request_identity(TOKEN, None)
    archive.record_submission("kundli", {"name": "Trishna Rai"}, {"ok": True})
    blob = repr(store.rows)

    for banned in ("access_token", "refresh_token", "Authorization", "Bearer", TOKEN,
                   "password", "provider_token"):
        assert banned not in blob, banned

    body = TestClient(main.app).get(
        "/api/admin/submissions", headers={"Authorization": f"Bearer {TOKEN}"}
    ).text
    for banned in ("access_token", "refresh_token", "provider_token", TOKEN, "Bearer"):
        assert banned not in body, banned


# --- 19: admin security unchanged -------------------------------------------
def test_non_admin_cannot_access_the_admin_api(store):
    client = TestClient(main.app)
    assert client.get("/api/admin/submissions").status_code == 401
    assert client.get("/api/admin/submissions",
                      headers={"Authorization": "Bearer forged"}).status_code == 401
    assert client.get("/api/admin/submissions",
                      headers={"Authorization": f"Bearer {OTHER_TOKEN}"}).status_code == 403


def test_archive_security_is_unchanged():
    sql = (REPO / "supabase" / "migrations" / "0002_product_submissions.sql").read_text(encoding="utf-8")
    assert "enable row level security" in sql
    assert "force row level security" in sql
    assert "revoke all on public.product_submissions from anon" in sql
    assert "revoke all on public.product_submissions from authenticated" in sql
    assert "references auth.users (id)" in sql


# --- 20: no astrology methodology changed -----------------------------------
def test_no_astrology_calculation_was_changed():
    calculator = (REPO / "backend" / "calculator.py").read_text(encoding="utf-8")
    assert "FLG_SPEED" in calculator
    aggregate = (REPO / "backend" / "kundli" / "aggregate.py").read_text(encoding="utf-8")
    assert 'motion = "Retrograde" if retrograde.get(planet.name) else "Direct"' in aggregate
    # The identity work lives in the archive/admin layer only.
    source = (REPO / "backend" / "archive.py").read_text(encoding="utf-8")
    for banned in ("swisseph", "swe.calc", "ayanamsa"):
        assert banned not in source.lower(), banned
