"""Test-wide guard: no test may ever contact Google's Gemini API."""

from __future__ import annotations

import json

import pytest


class _StubResponse:
    status_code = 200
    text = ""

    def json(self):
        return {
            "status": "completed",
            "steps": [{"type": "model_output", "content": [{"type": "text", "text": "Stubbed reply."}]}],
        }


@pytest.fixture(autouse=True)
def block_real_gemini(monkeypatch):
    import chat.gemini as gemini

    def _stub_post(*args, **kwargs):
        return _StubResponse()

    monkeypatch.setattr(gemini.httpx, "post", _stub_post)
    yield


@pytest.fixture(autouse=True)
def security_test_env(monkeypatch):
    """Deterministic security-related environment for tests.

    Dev tooling is explicitly opted in (tests call /api/dev/*), the rate limiter
    is off so suites are not throttled, and the app is not treated as production.
    Tests that verify the hardening itself re-enable these explicitly.
    """
    monkeypatch.setenv("KAVACH_DEV_TOOLS", "1")
    monkeypatch.setenv("KAVACH_RATELIMIT", "0")
    monkeypatch.delenv("KAVACH_ENV", raising=False)
    yield


@pytest.fixture(autouse=True)
def archive_isolation(monkeypatch):
    """Guarantee tests can never write to the real (production) archive.

    Every test gets an in-memory store by default, so an instrumented endpoint
    exercised through TestClient cannot create rows in Supabase. Suites that need
    to assert on archived rows install their own fake, which overrides this one.
    """
    import archive

    class _MemoryStore:
        def __init__(self):
            self.rows = []

        def configured(self):
            return True

        def insert(self, row):
            stored = dict(row)
            stored["id"] = f"mem-{len(self.rows) + 1}"
            self.rows.append(stored)
            return stored["id"]

        def verify_token(self, token):
            return None

        def is_admin(self, user_id):
            return False

        def email_for(self, user_id):
            return None

        def query(self, filters, select, limit, offset, count=False):
            return [], 0

        def get(self, submission_id):
            return None

        def delete(self, submission_id):
            return False

        def stats(self, since_iso):
            return {"total": len(self.rows)}

    monkeypatch.setattr(archive, "store", _MemoryStore())
    yield


@pytest.fixture(autouse=True)
def natal_state_isolation():
    """Natal birth details are per-conversation, never shared across tests."""
    import chat.natal

    chat.natal.clear()
    yield
    chat.natal.clear()
