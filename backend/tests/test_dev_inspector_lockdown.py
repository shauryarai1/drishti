"""Production inspector lock-down and rate-limiting regression tests.

Two guarantees are covered here:
  1. Ordinary production requests can never obtain inspector/trace data (private
     model context, routing metadata, hidden reading mechanics), and production
     does not even record it.
  2. The rate limiter protects paid/limited AI endpoints, distinguishes
     authenticated callers from guests, cannot be bypassed with forged identity,
     and never leaks secrets.
"""

from __future__ import annotations

import json
import logging
import pathlib

import pytest
from fastapi.testclient import TestClient

import archive
import chat.trace as trace
import hardening
import main

REPO = pathlib.Path(__file__).resolve().parents[2]
ASK_PAGE = REPO / "frontend-next" / "app" / "ask" / "page.tsx"
ASK = {"timestamp": "2026-09-21T22:40:00+05:30", "latitude": 28.6139, "longitude": 77.209,
       "timezone": "Asia/Kolkata"}


class FakeStore:
    def __init__(self) -> None:
        self.rows: list[dict] = []

    def configured(self) -> bool:
        return True

    def insert(self, row: dict):
        stored = dict(row)
        stored["id"] = f"id-{len(self.rows) + 1}"
        self.rows.append(stored)
        return stored["id"]

    def verify_token(self, token):
        return None

    def is_admin(self, user_id: str) -> bool:
        return False


@pytest.fixture()
def ask_env(monkeypatch):
    monkeypatch.setattr(archive, "store", FakeStore())
    monkeypatch.setattr("chat.reading.sensitive_response", lambda _q: None)

    def no_reading(_q):
        raise RuntimeError("no tarot in tests")

    monkeypatch.setattr("chat.reading.build_reading", no_reading)
    monkeypatch.setattr(
        "chat.groq.generate_reply_detailed",
        lambda *a, **k: {"text": "A safe answer.", "model": "nvidia/nemotron-3.5-lightning-30b-a3b",
                         "preferred": "nvidia/nemotron-3.5-lightning-30b-a3b", "provider": "groq",
                         "attempts": [{"model": "nvidia/nemotron-3.5-lightning-30b-a3b", "reason": "ok"}],
                         "fallback": False},
    )


@pytest.fixture()
def client():
    return TestClient(main.app)


def _ask(client, conversation_id: str):
    return client.post("/api/ask", json={**ASK, "question": "hello", "conversation_id": conversation_id})


# --- 1. production inspector / trace lock-down ------------------------------
def test_production_records_no_trace_and_returns_no_inspector_data(monkeypatch, ask_env, client):
    conversation = "prod-lockdown"
    trace.clear(conversation)
    monkeypatch.setenv("KAVACH_ENV", "production")
    monkeypatch.setenv("KAVACH_DEV_TOOLS", "1")  # even an explicit opt-in must lose to production

    assert _ask(client, conversation).status_code == 200

    # Nothing was recorded for the production request...
    assert trace.get_event(conversation) is None
    # ...and the inspector/trace endpoints stay unreachable.
    assert client.post("/api/dev/kavach-trace", json={"conversation_id": conversation}).status_code == 404
    assert client.post("/api/dev/kavach-tarot", json={"question": "hi"}).status_code == 404


def test_trace_data_is_only_reachable_behind_the_dev_gate(monkeypatch, ask_env, client):
    """Documents what is protected: the trace does carry private context/routing."""
    conversation = "dev-lockdown"
    trace.clear(conversation)
    monkeypatch.delenv("KAVACH_ENV", raising=False)
    monkeypatch.setenv("KAVACH_DEV_TOOLS", "1")

    assert _ask(client, conversation).status_code == 200
    event = trace.get_event(conversation)
    assert event is not None
    assert "model" in event
    assert client.post("/api/dev/kavach-trace", json={"conversation_id": conversation}).status_code == 200

    # Revoking the explicit development opt-in closes it again immediately.
    monkeypatch.delenv("KAVACH_DEV_TOOLS", raising=False)
    assert client.post("/api/dev/kavach-trace", json={"conversation_id": conversation}).status_code == 404


def test_frontend_never_ships_a_visible_inspector_by_default():
    source = ASK_PAGE.read_text(encoding="utf-8")
    # Explicit opt-in only: an ordinary (even non-production) build shows nothing.
    assert "NEXT_PUBLIC_KAVACH_DEV_TOOLS === '1'" in source
    assert "process.env.NODE_ENV !== 'production'" not in source
    assert "const [devEnabled, setDevEnabled] = useState(true)" not in source
    # Both the trigger and the panel are behind the opt-in flag.
    assert source.count("DEV_TOOLS_ENABLED &&") >= 2
    # No raw network/exception diagnostic is ever surfaced to the user.
    assert "Failed to fetch" not in source
    assert "setTraceError(exc instanceof Error ? exc.message" not in source


# --- 2. rate limiting -------------------------------------------------------
def _enable_tiny_limits(monkeypatch, guest: int = 2, user: int = 3) -> None:
    monkeypatch.setenv("KAVACH_RATELIMIT", "1")
    monkeypatch.setattr(hardening, "RATE_LIMITS", (("/api/health", guest, user),))
    hardening.LIMITER.reset()


def test_normal_ask_conversation_succeeds_under_the_limit(monkeypatch, ask_env, client):
    monkeypatch.setenv("KAVACH_RATELIMIT", "1")
    hardening.LIMITER.reset()
    try:
        for index in range(4):
            assert _ask(client, f"normal-{index}").status_code == 200
    finally:
        hardening.LIMITER.reset()


def test_guest_requests_are_limited(monkeypatch, client):
    _enable_tiny_limits(monkeypatch)
    ip = {"X-Forwarded-For": "203.0.113.99"}
    try:
        assert client.get("/api/health", headers=ip).status_code == 200
        assert client.get("/api/health", headers=ip).status_code == 200
        blocked = client.get("/api/health", headers=ip)
        assert blocked.status_code == 429
        assert int(blocked.headers["retry-after"]) >= 1
    finally:
        hardening.LIMITER.reset()


def test_authenticated_user_cannot_affect_another_users_bucket(monkeypatch, client):
    _enable_tiny_limits(monkeypatch)
    user_a = {"Authorization": "Bearer token-a", "X-Forwarded-For": "198.51.100.1"}
    user_b = {"Authorization": "Bearer token-b", "X-Forwarded-For": "198.51.100.2"}
    try:
        for _ in range(3):
            assert client.get("/api/health", headers=user_a).status_code == 200
        assert client.get("/api/health", headers=user_a).status_code == 429
        # A different authenticated identity is untouched by A's exhaustion.
        assert client.get("/api/health", headers=user_b).status_code == 200
    finally:
        hardening.LIMITER.reset()


def test_forged_or_rotated_identity_cannot_bypass_limits(monkeypatch, client):
    _enable_tiny_limits(monkeypatch)
    ip = {"X-Forwarded-For": "203.0.113.50"}
    try:
        for index in range(3):
            headers = {**ip, "Authorization": f"Bearer forged-token-{index}"}
            assert client.get("/api/health", headers=headers).status_code == 200
        # Inventing a fresh token per request cannot lift the per-IP ceiling.
        blocked = client.get("/api/health", headers={**ip, "Authorization": "Bearer forged-token-final"})
        assert blocked.status_code == 429
    finally:
        hardening.LIMITER.reset()


def test_session_header_is_not_treated_as_authentication(monkeypatch, client):
    """X-Kavach-Session must not buy the authenticated allowance."""
    _enable_tiny_limits(monkeypatch, guest=2, user=5)
    ip = {"X-Forwarded-For": "203.0.113.77", "X-Kavach-Session": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"}
    try:
        assert client.get("/api/health", headers=ip).status_code == 200
        assert client.get("/api/health", headers=ip).status_code == 200
        assert client.get("/api/health", headers=ip).status_code == 429
    finally:
        hardening.LIMITER.reset()


def test_rate_limit_response_and_logs_expose_no_secrets(monkeypatch, client):
    _enable_tiny_limits(monkeypatch, guest=1, user=1)

    records: list[str] = []

    class Capture(logging.Handler):
        def emit(self, record):
            records.append(record.getMessage())

    logger = logging.getLogger("kavach.security")
    handler = Capture()
    logger.addHandler(handler)
    token = "sentinel-secret-token-value"
    try:
        headers = {"Authorization": f"Bearer {token}"}
        client.get("/api/health", headers=headers)
        blocked = client.get("/api/health", headers=headers)
    finally:
        logger.removeHandler(handler)
        hardening.LIMITER.reset()

    assert blocked.status_code == 429
    body = blocked.json()
    assert set(body.keys()) == {"status", "message"}
    assert token not in json.dumps(body)
    joined = "\n".join(records)
    assert token not in joined
    assert "ip:" not in joined and "user:" not in joined, "bucket identifiers must not be logged"
    assert "ratelimit" in joined, "the safe operational log should still be emitted"


def test_user_id_in_body_cannot_change_the_limit_bucket(monkeypatch, ask_env, client):
    """A client-supplied user id is never used as identity for limiting."""
    monkeypatch.setenv("KAVACH_RATELIMIT", "1")
    monkeypatch.setattr(hardening, "RATE_LIMITS", (("/api/ask", 2, 3),))
    hardening.LIMITER.reset()
    ip = {"X-Forwarded-For": "203.0.113.200"}
    try:
        for index in range(2):
            response = client.post("/api/ask", json={**ASK, "question": "hi",
                                                     "conversation_id": f"spoof-{index}",
                                                     "user_id": f"victim-{index}"}, headers=ip)
            assert response.status_code == 200
        assert client.post("/api/ask", json={**ASK, "question": "hi", "conversation_id": "spoof-final",
                                             "user_id": "victim-final"}, headers=ip).status_code == 429
    finally:
        hardening.LIMITER.reset()


# --- 3. dev tooling pages must not be usable production pages ---------------
DEV_PAGES = (
    REPO / "frontend-next" / "app" / "dev" / "kavach-tarot" / "page.tsx",
    REPO / "frontend-next" / "app" / "dev" / "kavach-chat" / "page.tsx",
    REPO / "frontend-next" / "app" / "dev" / "panchang-engine" / "page.tsx",
)
PRODUCTION_GUARD = "process.env.NODE_ENV === 'production'"


@pytest.mark.parametrize("page", DEV_PAGES, ids=lambda path: path.parent.name)
def test_dev_pages_use_a_compile_time_production_guard(page):
    source = page.read_text(encoding="utf-8")
    # A build-time constant (inlined by Next), not CSS and not a runtime flag.
    assert PRODUCTION_GUARD in source
    declaration = source.index("export default function")
    guard_at = source.index(PRODUCTION_GUARD)
    first_return = source.index("return (", declaration)
    # The component's very first action is the production check...
    assert declaration < guard_at < first_return, "the production guard must run before any markup"
    # ...and the notice it returns comes before any tool data call.
    notice_at = source.index("disabled in production")
    assert guard_at < notice_at
    first_fetch = source.find("fetch(", declaration)
    if first_fetch != -1:
        assert notice_at < first_fetch, "the production notice must precede tool data calls"


@pytest.mark.parametrize("page", DEV_PAGES, ids=lambda path: path.parent.name)
def test_dev_page_production_branch_contains_no_tool_markup(page):
    source = page.read_text(encoding="utf-8")
    guard_at = source.index(PRODUCTION_GUARD)
    branch_end = source.index("return (", guard_at) + 900
    branch = source[guard_at:branch_end]
    # The production branch must not reach the tool: no data calls, no private markup.
    for marker in ("fetch(", "/dev/", "private_context", "draw_id", "COPY PRIVATE"):
        assert marker not in branch, marker


def test_no_other_route_references_dev_tooling_unconditionally():
    """Only the ask page and the /dev/* pages talk to dev endpoints."""
    offenders = []
    for path in (REPO / "frontend-next" / "app").rglob("*.tsx"):
        if ".next" in path.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "/api/dev/" not in text:
            continue
        is_dev_page = "dev" in path.parts
        is_ask_page = path.name == "page.tsx" and path.parent.name == "ask"
        if not (is_dev_page or is_ask_page):
            offenders.append(str(path.relative_to(REPO)))
    assert offenders == [], offenders
