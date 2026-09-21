"""Owner archive: capture, allowlisting, and admin authorisation.

These tests exercise the real FastAPI routes and the real archive code path with
an injected in-memory store, so no Supabase project is required. They do not fake
a live RLS result: the database-side guarantees are asserted separately.
"""

from __future__ import annotations

import pathlib
import re

import pytest
from fastapi.testclient import TestClient

import archive
import main

GUEST_SESSION = "11111111-2222-3333-4444-555555555555"
GOOD_TOKEN = "test-token-for-admin"
NORMAL_TOKEN = "test-token-normal-user"
ADMIN_ID = "aaaaaaaa-0000-0000-0000-000000000001"
NORMAL_ID = "bbbbbbbb-0000-0000-0000-000000000002"

KUNDLI_PAYLOAD = {
    "name": "Test Native",
    "date": "2010-01-21",
    "time": "08:19",
    "place": "Delhi, India",
    "latitude": 28.6139,
    "longitude": 77.209,
    "timezone": "Asia/Kolkata",
}


class FakeStore:
    """In-memory stand-in for the Supabase service-role store."""

    def __init__(self) -> None:
        self.rows: list[dict] = []
        self._seq = 0
        self.tokens = {GOOD_TOKEN: ADMIN_ID, NORMAL_TOKEN: NORMAL_ID}
        self.admins = {ADMIN_ID}

    def configured(self) -> bool:
        return True

    def verify_token(self, token: str):
        return self.tokens.get(token)

    def is_admin(self, user_id: str) -> bool:
        return user_id in self.admins

    def email_for(self, user_id: str):
        return {"user": "user@example.com", "admin": "owner@example.com"}.get(
            "admin" if user_id in self.admins else "user"
        )

    def insert(self, row: dict):
        self._seq += 1
        stored = dict(row)
        stored["id"] = f"00000000-0000-0000-0000-{self._seq:012d}"
        stored["created_at"] = f"2026-09-21T10:0{self._seq}:00+00:00"
        self.rows.append(stored)
        return stored["id"]

    # -- admin query surface -------------------------------------------------
    def _apply(self, filters: dict) -> list[dict]:
        results = list(self.rows)
        for key, value in filters.items():
            if key == "or":
                continue
            if key == "product":
                wanted = value.split(".", 1)[1]
                results = [row for row in results if row["product"] == wanted]
            elif key == "user_id":
                if value == "is.null":
                    results = [row for row in results if row.get("user_id") is None]
                elif value == "not.is.null":
                    results = [row for row in results if row.get("user_id")]
            elif key == "created_at":
                results = results  # range filtering already exercised via the API layer
        return results

    def query(self, filters, select, limit, offset, count=False):
        results = self._apply(filters)
        return results[offset : offset + limit], len(results)

    def get(self, submission_id):
        for row in self.rows:
            if row["id"] == submission_id:
                return dict(row)
        return None

    def delete(self, submission_id):
        before = len(self.rows)
        self.rows = [row for row in self.rows if row["id"] != submission_id]
        return len(self.rows) < before

    def stats(self, since_iso):
        out = {
            "total": len(self.rows),
            "today": len(self.rows),
            "guests": len([r for r in self.rows if not r.get("user_id")]),
            "accounts": len([r for r in self.rows if r.get("user_id")]),
        }
        for product in archive.PRODUCTS:
            out[product] = len([r for r in self.rows if r["product"] == product])
        return out


@pytest.fixture()
def fake_store(monkeypatch):
    store = FakeStore()
    monkeypatch.setattr(archive, "store", store)
    return store


@pytest.fixture()
def client():
    return TestClient(main.app)


def _generate_kundli(client, headers=None):
    return client.post("/api/kundli", json=KUNDLI_PAYLOAD, headers=headers or {})


def _ask(client, question, headers=None):
    return client.post(
        "/api/ask",
        json={"question": question, "timestamp": "2026-09-21T22:40:00+05:30", "conversation_id": "c-1"},
        headers=headers or {},
    )


# --- capture ---------------------------------------------------------------
def test_guest_kundli_submission_is_archived(fake_store, client):
    assert _generate_kundli(client, {"x-kavach-session": GUEST_SESSION}).status_code == 200
    assert len(fake_store.rows) == 1
    row = fake_store.rows[0]
    assert row["product"] == "kundli"
    assert row["user_id"] is None                      # guest, no identity invented
    assert row["visitor_session_id"] == GUEST_SESSION
    assert row["status"] == "SUCCEEDED"


def test_authenticated_kundli_submission_uses_verified_identity(fake_store, client):
    _generate_kundli(client, {"Authorization": f"Bearer {GOOD_TOKEN}"})
    assert len(fake_store.rows) == 1
    assert fake_store.rows[0]["user_id"] == ADMIN_ID


def test_identity_cannot_be_spoofed_through_the_body_or_headers(fake_store, client):
    payload = dict(KUNDLI_PAYLOAD, user_id="attacker-supplied", account="someone-else")
    assert client.post("/api/kundli", json=payload,
                       headers={"Authorization": "Bearer not-a-real-token"}).status_code == 200
    row = fake_store.rows[0]
    assert row["user_id"] is None                       # unverifiable token == guest
    assert "user_id" not in row["input_data"]
    assert "account" not in row["input_data"]


def test_kundli_input_and_result_are_retained_correctly(fake_store, client):
    response = _generate_kundli(client, {"x-kavach-session": GUEST_SESSION})
    body = response.json()
    row = fake_store.rows[0]

    assert row["input_data"] == KUNDLI_PAYLOAD          # exact permitted form values
    assert row["result_data"]["chart"]["ascendant"]["rashi"] == body["chart"]["ascendant"]["rashi"]
    assert row["result_data"]["planets"] == body["planets"]
    assert row["schema_version"] == archive.SCHEMA_VERSION
    assert row["error_category"] is None


def test_ask_kavach_question_and_answer_are_retained(fake_store, client, monkeypatch):
    import chat.gemini as gemini

    monkeypatch.setattr(gemini, "generate_reply_detailed",
                        lambda *a, **k: {"text": "Mars is retrograde in your chart."})

    question = "What did my 2010 chart say about Mars?"
    response = _ask(client, question, {"x-kavach-session": GUEST_SESSION})
    assert response.status_code == 200
    answer = response.json()["answer"]

    asks = [row for row in fake_store.rows if row["product"] == "ask"]
    assert len(asks) == 1
    assert asks[0]["input_data"]["question"] == question
    assert asks[0]["result_data"]["answer"] == answer
    assert asks[0]["result_data"]["answered"] is True


def test_unavailable_ask_answer_is_still_archived_with_its_status(fake_store, client, monkeypatch):
    import chat.gemini as gemini

    def boom(*_args, **_kwargs):
        raise RuntimeError("provider down")

    monkeypatch.setattr(gemini, "generate_reply_detailed", boom)
    assert _ask(client, "Will I travel this year?").status_code == 200

    asks = [row for row in fake_store.rows if row["product"] == "ask"]
    assert len(asks) == 1
    assert asks[0]["result_data"]["answered"] is False
    assert asks[0]["error_category"] == "model_unavailable"


def test_nothing_is_archived_without_a_submitted_request(fake_store, client):
    assert fake_store.rows == []
    assert client.get("/api/health").status_code == 200
    assert fake_store.rows == []


def test_archive_has_no_public_ingest_endpoint():
    """Unsent drafts cannot be reported: the client has no write path at all."""
    source = pathlib.Path(archive.__file__).read_text(encoding="utf-8")
    assert "router.post" not in source
    assert "router.put" not in source
    assert "router.patch" not in source


# --- sensitive fields ------------------------------------------------------
@pytest.mark.parametrize("key", ["password", "password_confirmation", "access_token",
                                 "refresh_token", "authorization", "cookie", "api_key",
                                 "service_role_key", "reset_token", "headers", "jwt",
                                 "ip_address", "device_fingerprint", "credit_card"])
def test_sensitive_fields_are_rejected(key):
    with pytest.raises(archive.RejectedInput):
        archive.sanitise_input("kundli", {"date": "2010-01-21", key: "secret-value"})


def test_sensitive_field_anywhere_is_rejected():
    with pytest.raises(archive.RejectedInput):
        archive.sanitise_input("weekly", {"birth": {"date": "2010-01-21", "token": "x"}})


def test_nothing_sensitive_is_stored(fake_store):
    for product, payload in (
        ("kundli", {"date": "2010-01-21", "password": "hunter2"}),
        ("ask", {"question": "hi", "authorization": "Bearer abc"}),
    ):
        archive.record_submission(product, payload, {"ok": True})
    assert fake_store.rows == []


def test_result_sanitisation_drops_internal_keys():
    cleaned = archive.sanitise_result(
        "reading",
        {"status": "ok", "attention": {"hook": "keep"}, "reasoning": "hidden",
         "system_prompt": "hidden", "trace": {"rule": "hidden"}, "_internal_engine_status": "x"},
    )
    assert cleaned == {"status": "ok", "attention": {"hook": "keep"}}


def test_unknown_product_is_rejected():
    with pytest.raises(archive.RejectedInput):
        archive.sanitise_input("delete_everything", {"x": 1})


def test_oversized_payload_is_not_stored(fake_store):
    archive.record_submission("kundli", {"name": "x" * 50_000, "date": "2010-01-21"}, {"ok": True})
    assert fake_store.rows == []


def test_archiving_failure_never_breaks_the_product(fake_store, client, monkeypatch):
    def explode(*_args, **_kwargs):
        raise RuntimeError("store down")

    monkeypatch.setattr(archive, "sanitise_input", explode)
    assert _generate_kundli(client).status_code == 200


# --- admin access ----------------------------------------------------------
def test_unauthenticated_cannot_list_or_open(fake_store, client):
    assert client.get("/api/admin/submissions").status_code == 401
    assert client.get("/api/admin/stats").status_code == 401
    assert client.get("/api/admin/submissions/00000000-0000-0000-0000-000000000001").status_code == 401


def test_normal_user_cannot_list_open_or_delete(fake_store, client):
    headers = {"Authorization": f"Bearer {NORMAL_TOKEN}"}
    _generate_kundli(client, headers)
    submission_id = fake_store.rows[0]["id"]

    assert client.get("/api/admin/submissions", headers=headers).status_code == 403
    assert client.get("/api/admin/stats", headers=headers).status_code == 403
    assert client.get(f"/api/admin/submissions/{submission_id}", headers=headers).status_code == 403
    assert client.delete(f"/api/admin/submissions/{submission_id}", headers=headers).status_code == 403


def test_guest_cannot_list_or_open(fake_store, client):
    _generate_kundli(client, {"x-kavach-session": GUEST_SESSION})
    submission_id = fake_store.rows[0]["id"]
    assert client.get("/api/admin/submissions").status_code == 401
    assert client.get(f"/api/admin/submissions/{submission_id}").status_code == 401


def test_admin_can_list_and_open(fake_store, client):
    headers = {"Authorization": f"Bearer {GOOD_TOKEN}"}
    _generate_kundli(client, {"x-kavach-session": GUEST_SESSION})
    _generate_kundli(client, headers)

    listed = client.get("/api/admin/submissions", headers=headers)
    assert listed.status_code == 200
    body = listed.json()
    assert body["total"] == 2
    assert len(body["submissions"]) == 2

    detail = client.get(f"/api/admin/submissions/{fake_store.rows[0]['id']}", headers=headers)
    assert detail.status_code == 200
    submission = detail.json()["submission"]
    assert submission["input_data"]["date"] == "2010-01-21"
    assert submission["result_data"]["chart"] is not None
    assert submission["account_email"] is None or isinstance(submission["account_email"], str)

    stats = client.get("/api/admin/stats", headers=headers).json()["stats"]
    assert stats["total"] == 2
    assert stats["guests"] == 1
    assert stats["accounts"] == 1
    assert stats["kundli"] == 2


def test_admin_filters_and_pagination(fake_store, client):
    headers = {"Authorization": f"Bearer {GOOD_TOKEN}"}
    for _ in range(3):
        _generate_kundli(client, {"x-kavach-session": GUEST_SESSION})
    _ask(client, "one question", headers)

    assert client.get("/api/admin/submissions?product=kundli", headers=headers).json()["total"] == 3
    assert client.get("/api/admin/submissions?product=ask", headers=headers).json()["total"] == 1
    assert client.get("/api/admin/submissions?visitor=guests", headers=headers).json()["total"] == 3
    assert client.get("/api/admin/submissions?visitor=accounts", headers=headers).json()["total"] == 1
    assert client.get("/api/admin/submissions?product=not-a-product", headers=headers).status_code == 400

    page_one = client.get("/api/admin/submissions?page=1&page_size=2", headers=headers).json()
    assert len(page_one["submissions"]) == 2 and page_one["total"] == 4
    page_two = client.get("/api/admin/submissions?page=2&page_size=2", headers=headers).json()
    assert len(page_two["submissions"]) == 2
    assert {row["id"] for row in page_one["submissions"]}.isdisjoint(
        {row["id"] for row in page_two["submissions"]}
    )


def test_admin_can_delete_one_submission(fake_store, client):
    headers = {"Authorization": f"Bearer {GOOD_TOKEN}"}
    _generate_kundli(client, headers)
    submission_id = fake_store.rows[0]["id"]

    assert client.delete(f"/api/admin/submissions/{submission_id}", headers=headers).status_code == 200
    assert fake_store.rows == []
    assert client.get(f"/api/admin/submissions/{submission_id}", headers=headers).status_code == 404


def test_admin_detail_rejects_a_malformed_id(fake_store, client):
    headers = {"Authorization": f"Bearer {GOOD_TOKEN}"}
    assert client.get("/api/admin/submissions/..%2Fetc%2Fpasswd", headers=headers).status_code in (400, 404)


def test_admin_api_is_unavailable_when_unconfigured(monkeypatch):
    monkeypatch.setattr(archive.store, "configured", lambda: False)
    assert TestClient(main.app).get("/api/admin/stats",
                                    headers={"Authorization": f"Bearer {GOOD_TOKEN}"}).status_code == 503


# --- storage guarantees ----------------------------------------------------
MIGRATION_0001 = pathlib.Path(__file__).resolve().parents[2] / "supabase" / "migrations" / "0001_saved_readings.sql"
MIGRATION_0002 = pathlib.Path(__file__).resolve().parents[2] / "supabase" / "migrations" / "0002_product_submissions.sql"


def test_saved_readings_policies_are_unchanged():
    sql = MIGRATION_0001.read_text(encoding="utf-8").lower()
    assert len(re.findall(r"create policy", sql)) == 4
    assert sql.count("auth.uid()") >= 4
    assert "to authenticated" in sql
    assert "using (true)" not in sql


def test_product_submissions_grants_nothing_to_browsers():
    sql = re.sub(r"--.*", "", MIGRATION_0002.read_text(encoding="utf-8")).lower()
    assert "revoke all on public.product_submissions from anon" in sql
    assert "revoke all on public.product_submissions from authenticated" in sql
    assert "grant" not in sql
    assert "create policy" not in sql
    assert "enable row level security" in sql and "force row level security" in sql


def test_admin_registry_is_not_browser_readable():
    sql = MIGRATION_0002.read_text(encoding="utf-8").lower()
    assert "revoke all on public.admin_users from anon" in sql
    assert "revoke all on public.admin_users from authenticated" in sql
    assert "references auth.users (id)" in sql


def _code_without_comments(text: str) -> str:
    """Prose may name secrets; only real code should fail this check."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return re.sub(r"//.*", "", text)


def test_service_role_key_never_reaches_the_frontend():
    frontend = pathlib.Path(__file__).resolve().parents[2] / "frontend-next"
    offenders = []
    for path in frontend.rglob("*.ts*"):
        if "node_modules" in path.parts or ".next" in path.parts:
            continue
        text = _code_without_comments(path.read_text(encoding="utf-8", errors="ignore")).lower()
        if "service_role" in text or "service-role" in text or "service_role_key" in text:
            offenders.append(str(path))
    assert offenders == [], offenders
