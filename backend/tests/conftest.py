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
