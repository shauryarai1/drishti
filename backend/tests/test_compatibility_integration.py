"""KAVACH marriage compatibility - end-to-end integration.

Covers the persistence/identity layer added on top of the V1 engine: the
migration constraints, the archive allowlist, Admin identity for the account vs
the two chart people, and the frontend wiring (gate, pending form, bearer token,
six factors, save and reopen).

Never touches production Supabase: the archive store is an in-memory fake.
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
TOKEN = "verified-session-token"

MIGRATION = REPO / "supabase" / "migrations" / "0003_compatibility.sql"
EXPERIENCE = FRONTEND / "components" / "CompatibilityExperience.tsx"
PAGE = FRONTEND / "app" / "compatibility" / "page.tsx"
HISTORY = FRONTEND / "lib" / "history.ts"
PENDING = FRONTEND / "lib" / "pendingForms.ts"
HISTORY_PAGE = FRONTEND / "app" / "history" / "page.tsx"


def _read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


class FakeStore:
    def __init__(self):
        self.rows: list[dict] = []

    def configured(self):
        return True

    def insert(self, row):
        stored = dict(row)
        stored["id"] = f"{len(self.rows) + 1:08x}-0000-4000-8000-000000000000"
        self.rows.append(stored)
        return stored["id"]

    def verify_token(self, token):
        return ACCOUNT_ID if token == TOKEN else None

    def is_admin(self, user_id):
        return user_id == ACCOUNT_ID

    def email_for(self, user_id):
        return "shaurya@example.com" if user_id == ACCOUNT_ID else None

    def profile_for(self, user_id):
        return {"email": "shaurya@example.com", "name": "Shaurya Rai"} if user_id == ACCOUNT_ID else None

    def query(self, filters, select, limit, offset, count=False):
        return [dict(r) for r in self.rows][offset:offset + limit], len(self.rows)

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
    archive.set_request_identity(None, None)
    yield fake
    archive.set_request_identity(None, None)


def _payload():
    return {
        "bride": {"name": "Ananya", "date": "2010-01-21", "time": "08:19", "place": "Delhi",
                  "latitude": 28.6139, "longitude": 77.209, "timezone": "Asia/Kolkata"},
        "groom": {"name": "Arjun", "date": "1990-05-15", "time": "14:15", "place": "Delhi",
                  "latitude": 28.6139, "longitude": 77.209, "timezone": "Asia/Kolkata"},
    }


# --- 1/2. migration and RLS --------------------------------------------------
def test_migration_adds_compatibility_without_touching_policies():
    sql = _read(MIGRATION)
    assert "saved_readings_type_check" in sql
    assert "product_submissions_product_check" in sql
    assert "'compatibility'" in sql
    # Additive only: no policy, grant or RLS statement is rewritten.
    for banned in ("create policy", "drop policy", "enable row level security",
                   "force row level security", "revoke", "grant "):
        assert banned not in sql.lower(), banned
    # The original migrations are untouched.
    assert "compatibility" not in _read(REPO / "supabase" / "migrations" / "0001_saved_readings.sql")
    assert "compatibility" not in _read(REPO / "supabase" / "migrations" / "0002_product_submissions.sql")


def test_rls_still_holds_on_the_archive_tables():
    for name in ("0001_saved_readings.sql", "0002_product_submissions.sql"):
        sql = _read(REPO / "supabase" / "migrations" / name)
        assert "enable row level security" in sql
        assert "force row level security" in sql


# --- 3/4/5. archive integration ---------------------------------------------
def test_archive_registry_accepts_compatibility():
    assert "compatibility" in archive.PRODUCTS
    fields = archive.INPUT_FIELDS["compatibility"]
    assert fields == ("bride_name", "bride_date", "bride_time", "bride_place",
                      "groom_name", "groom_date", "groom_time", "groom_place")


def test_authenticated_compatibility_archives_the_verified_user(store):
    client = TestClient(main.app)
    body = client.post("/api/compatibility", json=_payload(),
                       headers={"Authorization": f"Bearer {TOKEN}"}).json()
    assert body["status"] == "ok"

    rows = [row for row in store.rows if row["product"] == "compatibility"]
    assert rows, "the compatibility submission must be archived"
    assert rows[-1]["user_id"] == ACCOUNT_ID
    # Only safe customer-facing fields, and both people kept separate.
    assert set(rows[-1]["input_data"]) == set(archive.INPUT_FIELDS["compatibility"])
    assert rows[-1]["input_data"]["bride_name"] == "Ananya"
    assert rows[-1]["input_data"]["groom_name"] == "Arjun"


def test_forged_browser_identity_is_ignored_and_guests_stay_null(store):
    archive.set_request_identity(TOKEN, None)
    archive.record_submission("compatibility", {
        "bride_name": "Ananya", "groom_name": "Arjun",
        "user_id": "22222222-2222-2222-2222-222222222222",
    }, {"ok": True})
    assert store.rows[-1]["user_id"] == ACCOUNT_ID
    assert "user_id" not in store.rows[-1]["input_data"]

    archive.set_request_identity(None, None)
    archive.record_submission("compatibility", {"bride_name": "A", "groom_name": "B"}, {"ok": True})
    assert store.rows[-1]["user_id"] is None


def test_no_token_is_ever_archived(store):
    archive.set_request_identity(TOKEN, None)
    archive.record_submission("compatibility", {"bride_name": "A", "groom_name": "B"}, {"ok": True})
    blob = repr(store.rows)
    for banned in ("access_token", "refresh_token", "provider_token", "Bearer", TOKEN, "password"):
        assert banned not in blob, banned


# --- 6. Admin identity: account vs bride vs groom ----------------------------
def test_admin_shows_account_identity_and_both_chart_people(store):
    archive.set_request_identity(TOKEN, None)
    archive.record_submission("compatibility", {
        "bride_name": "Ananya", "bride_date": "2010-01-21", "bride_time": "08:19", "bride_place": "Delhi",
        "groom_name": "Arjun", "groom_date": "1990-05-15", "groom_time": "14:15", "groom_place": "Delhi",
    }, {"ok": True})

    client = TestClient(main.app)
    listed = client.get("/api/admin/submissions",
                        headers={"Authorization": f"Bearer {TOKEN}"}).json()["submissions"][0]
    assert listed["account_name"] == "Shaurya Rai"
    assert listed["account_email"] == "shaurya@example.com"
    assert listed["compatibility"] == {"bride": "Ananya", "groom": "Arjun"}
    # The account identity is never replaced by either chart person.
    assert listed["account_name"] not in ("Ananya", "Arjun")
    assert listed["person_name"] is None

    detail = client.get(f"/api/admin/submissions/{listed['id']}",
                        headers={"Authorization": f"Bearer {TOKEN}"}).json()["submission"]
    assert detail["compatibility"] == {"bride": "Ananya", "groom": "Arjun"}
    assert detail["account_name"] == "Shaurya Rai"


def test_non_admin_still_cannot_read_the_admin_api(store):
    client = TestClient(main.app)
    assert client.get("/api/admin/submissions").status_code == 401
    assert client.get("/api/admin/submissions",
                      headers={"Authorization": "Bearer forged"}).status_code == 401


# --- frontend: gate, pending form, bearer, factors, save, reopen -------------
def test_route_page_and_metadata_exist():
    assert PAGE.exists() and EXPERIENCE.exists()
    page = _read(PAGE)
    assert "metadata" in page and "CompatibilityExperience" in page


def test_frontend_gate_and_pending_form_and_bearer():
    ui = _read(EXPERIENCE)
    assert "ResultGate" in ui, "the result must be gated"
    assert "authStatus" in ui
    assert "savePendingForm('compatibility'" in ui
    assert "takePendingForm('compatibility')" in ui
    assert "loginHref('/compatibility')" in ui
    assert "authHeaders" in ui, "the verified bearer token must be sent"
    assert "token" not in ui.split("authHeaders")[0][-40:].lower()  # no token in a URL


def test_pending_key_is_dedicated_and_complete():
    source = _read(PENDING)
    assert "compatibility" in source
    assert "compatibility: [" in source
    for field in ("bride_name", "bride_date", "bride_time", "bride_place",
                  "groom_name", "groom_date", "groom_time", "groom_place"):
        assert field in source, field
    # The expiry/consume model is shared, not duplicated.
    assert "MAX_AGE_MS" in source and "takePendingForm" in source


def test_ui_renders_the_interpreted_report_and_no_score_or_yoni():
    ui = _read(EXPERIENCE)
    lowered = ui.lower()
    # The interpreted sections are what the customer sees.
    for section in ("report.overall", "report.atAGlance", "report.strengths",
                    "report.attentionAreas", "report.inDepth", "report.kavachView"):
        assert section in ui, section
    # A legacy renderer keeps older saved factor reports openable.
    assert "report.factors?.map" in ui
    for banned in ("yoni", "/36", "percentage", "score", "star rating", "should marry",
                   "do not marry", "perfect match", "will fail", "will succeed"):
        assert banned not in lowered, banned
    assert "points" not in ui


def test_save_uses_the_authenticated_account_with_duplicate_protection():
    ui = _read(EXPERIENCE)
    assert "saveCompatibilityReading(user.id" in ui
    assert "savedSignatureRef" in ui
    assert "if (savedSignatureRef.current === signature) return;" in ui


def test_history_supports_compatibility_and_reopens_without_recalculation():
    history = _read(HISTORY)
    assert "'compatibility'" in history
    assert "Marriage Compatibility" in history
    assert "buildCompatibilityTitle" in history
    assert "saveCompatibilityReading" in history
    assert "— Compatibility" in history

    ui = _read(EXPERIENCE)
    assert "getReading(user.id, savedId)" in ui
    assert "stored.report" in ui
    # Reopening must not call the calculation endpoint.
    saved_block = ui.split("const savedId = params.get('saved')")[1].split("const restored")[0]
    assert "fetch(" not in saved_block
    assert "/api/compatibility" not in saved_block

    assert "compatibility?saved=" in _read(HISTORY_PAGE)


def test_navigation_includes_compatibility():
    assert "'/compatibility'" in _read(FRONTEND / "components" / "Header.tsx")
    footer = _read(FRONTEND / "components" / "Footer.tsx")
    assert 'href="/compatibility"' in footer
    tools = _read(FRONTEND / "components" / "HomeToolsSection.tsx")
    assert "/compatibility" in tools and "Marriage Compatibility" in tools


def test_safety_language_absent_from_the_public_frontend():
    ui = _read(EXPERIENCE).lower()
    for banned in ("death", "lifespan", "fertilit", "pregnan", "child health",
                   "genetic", "hereditar", "medical", "violence", "poverty", "misery"):
        assert banned not in ui, banned


def test_yoni_is_implemented_and_deeper_factors_remain_unimplemented():
    assert (REPO / "backend" / "compatibility" / "yoni.py").exists()
    for name in ("mercury", "kuja", "dosha", "seventh_house", "eighth_house"):
        assert not (REPO / "backend" / "compatibility" / f"{name}.py").exists()


def test_compatibility_engine_and_bnn_are_unchanged():
    registry = _read(REPO / "backend" / "kundli" / "analysis" / "relationships.py")
    assert '"Mars": (("Moon", "Jupiter", "Venus", "Sun", "Ketu"), ("Mercury", "Rahu", "Saturn"))' in registry
    engine = _read(REPO / "backend" / "compatibility" / "engine.py")
    assert "FACTOR_ORDER" in engine and "overall_summary" in engine
    assert "kundli.analysis.relationships" not in engine
