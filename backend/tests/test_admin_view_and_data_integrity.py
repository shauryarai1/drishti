"""Admin VIEW correctness and archive data-integrity regression tests.

Covers two things:
  1. The admin detail endpoint returns the exact selected database row, stays
     admin-only, and never leaks private fields.
  2. One customer request produces AT MOST ONE archive row - including primary
     provider failure and the Gemini fallback - and admin statistics are database-derived
     rather than hardcoded.
"""

from __future__ import annotations

import json
import pathlib

import httpx
import pytest
from fastapi.testclient import TestClient

import archive
import chat.groq as groq
import main

REPO = pathlib.Path(__file__).resolve().parents[2]
ADMIN_PAGE = REPO / "frontend-next" / "app" / "admin" / "page.tsx"
ADMIN_CLIENT = REPO / "frontend-next" / "lib" / "admin.ts"

ADMIN_TOKEN = "admin-token"
USER_TOKEN = "user-token"
ADMIN_ID = "aaaaaaaa-0000-0000-0000-000000000001"
USER_ID = "bbbbbbbb-0000-0000-0000-000000000002"

ASK = {"timestamp": "2026-09-21T22:40:00+05:30", "latitude": 28.6139, "longitude": 77.209,
       "timezone": "Asia/Kolkata"}
KUNDLI = {"name": "Test Native", "date": "2010-01-21", "time": "08:19", "place": "Delhi, India",
          "latitude": 28.6139, "longitude": 77.209, "timezone": "Asia/Kolkata"}

FORBIDDEN_KEYS = ("reasoning", "reasoning_content", "system_prompt", "private_context",
                  "authorization", "token", "api_key", "apikey", "service_role", "password")


class RecordingStore:
    """Records every write and answers admin queries from memory."""

    def __init__(self) -> None:
        self.rows: list[dict] = []
        self.inserts = 0
        self.queries: list[dict] = []
        self.stats_calls = 0

    def configured(self) -> bool:
        return True

    def verify_token(self, token):
        return {ADMIN_TOKEN: ADMIN_ID, USER_TOKEN: USER_ID}.get(token)

    def is_admin(self, user_id: str) -> bool:
        return user_id == ADMIN_ID

    def email_for(self, user_id: str):
        return "owner@example.com" if user_id == ADMIN_ID else None

    def insert(self, row: dict):
        self.inserts += 1
        stored = dict(row)
        # UUID-shaped ids so requests pass the endpoint's id validation.
        stored["id"] = f"00000000-0000-0000-0000-{self.inserts:012d}"
        stored["created_at"] = f"2026-09-21T10:{self.inserts:02d}:00+00:00"
        self.rows.append(stored)
        return stored["id"]

    # -- admin read surface (mirrors the real store's contract) --------------
    def query(self, filters, select, limit, offset, count=False):
        self.queries.append({"filters": filters, "limit": limit, "offset": offset})
        return self.rows[offset:offset + limit], len(self.rows)

    def get(self, submission_id):
        return next((r for r in self.rows if r["id"] == submission_id), None)

    def delete(self, submission_id):
        return False

    def stats(self, since_iso):
        self.stats_calls += 1
        out = {"total": len(self.rows),
               "today": len(self.rows),
               "guests": sum(1 for r in self.rows if not r.get("user_id")),
               "accounts": sum(1 for r in self.rows if r.get("user_id"))}
        for product in archive.PRODUCTS:
            out[product] = sum(1 for r in self.rows if r["product"] == product)
        return out


class FakeResponse:
    def __init__(self, status_code: int = 200, payload=None, text: str = "") -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = text or (json.dumps(payload) if payload is not None else "")

    def json(self):
        if self._payload is None:
            raise ValueError("no json")
        return self._payload


def reply_payload(content: str = "An answer.") -> dict:
    return {"choices": [{"message": {"role": "assistant", "content": content}}]}


@pytest.fixture()
def store(monkeypatch):
    recording = RecordingStore()
    monkeypatch.setattr(archive, "store", recording)
    return recording


@pytest.fixture()
def client():
    return TestClient(main.app)


@pytest.fixture()
def ask_ready(monkeypatch):
    """Providers and Tarot mocked so /api/ask always reaches the archive step."""
    monkeypatch.setattr("chat.reading.sensitive_response", lambda _q: None)

    def no_reading(_q):
        raise RuntimeError("no tarot in tests")

    monkeypatch.setattr("chat.reading.build_reading", no_reading)
    monkeypatch.setattr("chat.groq.generate_reply_detailed",
                        lambda *a, **k: {"text": "Groq answer.", "model": groq.MODEL,
                                         "preferred": groq.MODEL, "provider": "groq",
                                         "attempts": [{"model": groq.MODEL, "reason": "ok"}],
                                         "fallback": False})
    monkeypatch.setattr("chat.gemini.generate_reply_detailed",
                        lambda *a, **k: {"text": "Gemini answer.", "model": "gemini-3.6-flash",
                                         "preferred": "gemini-3.6-flash", "attempts": []})


def _ask(client, conversation_id="view-test"):
    return client.post("/api/ask", json={**ASK, "question": "hello", "conversation_id": conversation_id})


# --- 1. admin VIEW ----------------------------------------------------------
def test_admin_detail_returns_the_exact_selected_row(store, client):
    client.post("/api/kundli", json=KUNDLI)
    client.post("/api/kundli", json={**KUNDLI, "name": "Second Native", "date": "1990-05-15"})
    first, second = store.rows[0]["id"], store.rows[1]["id"]

    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    detail_first = client.get(f"/api/admin/submissions/{first}", headers=headers).json()["submission"]
    detail_second = client.get(f"/api/admin/submissions/{second}", headers=headers).json()["submission"]

    assert detail_first["id"] == first and detail_second["id"] == second
    assert detail_first["input_data"]["date"] == "2010-01-21"
    assert detail_second["input_data"]["date"] == "1990-05-15"
    assert detail_first["input_data"] != detail_second["input_data"]


def test_admin_detail_is_denied_to_non_admins_and_guests(store, client):
    client.post("/api/kundli", json=KUNDLI)
    row_id = store.rows[0]["id"]

    assert client.get(f"/api/admin/submissions/{row_id}").status_code == 401
    assert client.get(f"/api/admin/submissions/{row_id}",
                      headers={"Authorization": f"Bearer {USER_TOKEN}"}).status_code == 403
    assert client.get(f"/api/admin/submissions/{row_id}",
                      headers={"Authorization": "Bearer forged"}).status_code == 401


def test_admin_detail_handles_missing_and_malformed_ids(store, client):
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    assert client.get("/api/admin/submissions/00000000-0000-0000-0000-000000000999",
                      headers=headers).status_code == 404
    assert client.get("/api/admin/submissions/not-a-uuid", headers=headers).status_code == 400
    # Traversal is rejected: normalised to 404 by the router, or 400 by validation.
    assert client.get("/api/admin/submissions/..%2Fetc%2Fpasswd", headers=headers).status_code in (400, 404)


def test_admin_detail_never_exposes_private_fields(store, client, ask_ready):
    _ask(client)
    row = store.rows[0]
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    body = json.dumps(client.get(f"/api/admin/submissions/{row['id']}", headers=headers).json())

    for key in FORBIDDEN_KEYS:
        assert key not in body.lower(), key
    detail = json.loads(body)["submission"]
    assert detail["input_data"]["question"] == "hello"
    assert detail["result_data"]["answer"] == "Groq answer."


def test_admin_stats_are_database_derived_not_hardcoded(store, client):
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    empty = client.get("/api/admin/stats", headers=headers).json()["stats"]
    assert empty["total"] == 0 and empty["kundli"] == 0
    assert empty["today"] == 0

    client.post("/api/kundli", json=KUNDLI)
    client.post("/api/kundli", json=KUNDLI)
    filled = client.get("/api/admin/stats", headers=headers).json()["stats"]

    assert filled["total"] == 2, "stats must come from the database, not constants"
    assert filled["kundli"] == 2
    assert filled["guests"] == 2 and filled["accounts"] == 0
    assert store.stats_calls >= 2


def test_admin_list_uses_database_pagination_window(store, client):
    client.post("/api/kundli", json=KUNDLI)
    client.post("/api/kundli", json=KUNDLI)
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    body = client.get("/api/admin/submissions?page=2&page_size=1", headers=headers).json()

    assert body["total"] == 2
    assert len(body["submissions"]) == 1
    assert store.queries[-1]["limit"] == 1 and store.queries[-1]["offset"] == 1


def test_admin_frontend_requests_the_selected_id_and_shows_states():
    source = (REPO / "frontend-next" / "app" / "admin" / "page.tsx").read_text(encoding="utf-8")
    # The VIEW control passes the row id into the detail fetch.
    assert "onClick={() => void open(row)}" in source
    assert "fetchAdminSubmission(row.id)" in source
    # Loading state prevents repeated clicks from firing many requests.
    assert "detailLoadingId" in source
    assert "disabled={detailLoadingId === row.id}" in source
    # The detail panel is rendered above the list so it is immediately visible.
    assert source.index("Submitted information") < source.index("Recent submissions")
    # Errors are admin-facing and generic.
    assert "Could not load submission details." in (REPO / "frontend-next" / "lib" / "admin.ts").read_text(encoding="utf-8")


def test_admin_supports_every_archived_product():
    page = ADMIN_PAGE.read_text(encoding="utf-8")
    client_lib = ADMIN_CLIENT.read_text(encoding="utf-8")
    for product in ("reading", "kundli", "daily", "weekly", "life_summary", "dasha", "ask", "panchang"):
        assert f"value: '{product}'" in client_lib, product
        assert f"key: '{product}'" in page, product
    # Un-modelled types still render through the generic result view.
    assert "GenericResult" in page


# --- 2. data integrity: one request, one row --------------------------------
def test_one_ask_request_creates_exactly_one_archive_row(store, client, ask_ready):
    _ask(client)
    assert store.inserts == 1


def test_primary_failure_then_fallback_does_not_duplicate_the_archive_row(store, client, monkeypatch):
    """One user request archives one row, even across the fallback chain."""
    monkeypatch.setattr("chat.reading.sensitive_response", lambda _q: None)
    monkeypatch.setattr("chat.reading.build_reading", lambda _q: (_ for _ in ()).throw(RuntimeError("no tarot")))

    attempts = {"n": 0}

    def failing_post(url, headers=None, json=None, timeout=None):
        attempts["n"] += 1
        return FakeResponse(503, text="overloaded")

    monkeypatch.setattr(groq.httpx, "post", failing_post)
    monkeypatch.setenv("GROQ_API_KEY", "test-sentinel")
    monkeypatch.setattr("chat.gemini.generate_reply_detailed",
                        lambda *a, **k: {"text": "Gemini answered.", "model": "gemini-3.5-flash-lite",
                                         "preferred": "gemini-3.5-flash-lite", "provider": "gemini",
                                         "attempts": []})

    body = _ask(client).json()

    assert body["answer"] == "Gemini answered."
    assert attempts["n"] == 1, "there is exactly one primary attempt"
    assert store.inserts == 1, "primary failure + fallback must not create two submissions"


def test_gemini_fallback_does_not_duplicate_the_archive_row(store, client, monkeypatch):
    monkeypatch.setattr("chat.reading.sensitive_response", lambda _q: None)
    monkeypatch.setattr("chat.reading.build_reading", lambda _q: (_ for _ in ()).throw(RuntimeError("no tarot")))
    monkeypatch.setattr("chat.groq.generate_reply_detailed",
                        lambda *a, **k: {"text": None, "model": None, "preferred": groq.MODEL,
                                         "provider": "groq", "attempts": [{"model": "x", "reason": "transient_503"}],
                                         "fallback": True})
    monkeypatch.setattr("chat.gemini.generate_reply_detailed",
                        lambda *a, **k: {"text": "Gemini rescued it.", "model": "gemini-3.6-flash",
                                         "preferred": "gemini-3.6-flash", "attempts": []})

    body = _ask(client).json()

    assert body["answer"] == "Gemini rescued it."
    assert store.inserts == 1, "the Gemini fallback must not add a second submission"


def test_failed_validation_creates_no_archive_row(store, client):
    assert client.post("/api/ask", json={"timestamp": "2026-09-21T22:40:00+05:30"}).status_code == 422
    assert client.post("/api/kundli", json={"date": "2010-01-21"}).status_code == 422
    assert client.post("/api/ask", json={**ASK, "question": "x" * 80_000}).status_code == 413
    assert store.inserts == 0


@pytest.mark.parametrize("product,request_spec", [
    ("kundli", ("POST", "/api/kundli", KUNDLI)),
    ("reading", ("POST", "/api/interpretation", {k: v for k, v in KUNDLI.items() if k != "name"})),
    ("daily", ("POST", "/api/daily", {"latitude": 28.6139, "longitude": 77.209, "timezone": "Asia/Kolkata"})),
    ("weekly", ("POST", "/api/weekly", {"birth": KUNDLI, "forecast": {
        "startDate": "2026-09-21", "place": "Delhi", "latitude": 28.6139,
        "longitude": 77.209, "timezone": "Asia/Kolkata"}})),
    ("life_summary", ("POST", "/api/life-summary", {"date": "2010-01-21", "time": "08:19",
                                                    "place": "Delhi", "latitude": 28.6139,
                                                    "longitude": 77.209, "timezone": "Asia/Kolkata"})),
    ("dasha", ("POST", "/api/current-dasha-reading", {"birth": KUNDLI, "asOf": "2026-09-21"})),
    ("panchang", ("GET", "/api/panchang?date=2026-09-21&latitude=28.6139&longitude=77.209&timezone=Asia/Kolkata", None)),
])
def test_every_product_archives_exactly_one_row(store, client, product, request_spec):
    method, path, payload = request_spec
    response = client.get(path) if method == "GET" else client.post(path, json=payload)
    assert response.status_code == 200, f"{product}: {response.text[:200]}"
    assert store.inserts == 1, product
    assert store.rows[0]["product"] == product


def test_health_and_dev_probes_are_never_archived(store, client):
    client.get("/api/health")
    client.get("/api/health")
    assert store.inserts == 0


def test_tests_cannot_write_to_the_real_store():
    """The autouse isolation fixture must replace the real Supabase store."""
    import importlib

    conftest = importlib.import_module("conftest")
    assert hasattr(conftest, "archive_isolation"), "archive isolation fixture is required"
    assert not hasattr(archive.store, "service_key"), "tests must not use the real Supabase store"


def test_archiving_can_be_disabled_by_operators(monkeypatch, store, client):
    monkeypatch.setenv("KAVACH_ARCHIVE", "0")
    client.post("/api/kundli", json=KUNDLI)
    assert store.inserts == 0
