"""Groq client for Ask KAVACH - the PRIMARY provider.

OpenAI-compatible endpoint: POST https://api.groq.com/openai/v1/chat/completions
Auth: `Authorization: Bearer $GROQ_API_KEY` (server-side only; never logged,
returned, archived or exposed to the browser).
Model: `openai/gpt-oss-120b`.

Architecture: ONE primary attempt, then the caller falls through to the
existing Gemini emergency fallback. There is no model router, no model list and
no retry of a failed request.

Privacy
-------
Only `choices[0].message.content` is ever read. gpt-oss models return a
`reasoning_content` field; it is never read, logged, returned or archived, and
the KAVACH system prompt is reused from the single existing source so it is
preserved exactly.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, List, Optional, Tuple

import httpx

# Reuse the exact KAVACH instructions so behaviour is unchanged.
from chat.gemini import _system_instruction_for

logger = logging.getLogger("kavach.chat")

ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "openai/gpt-oss-120b"
TIMEOUT_SECONDS = 15.0
MAX_TOKENS = 900
TEMPERATURE = 0.6


def api_key() -> Optional[str]:
    return os.environ.get("GROQ_API_KEY")


def _build_messages(
    history: List[Dict[str, str]], message: str, private_context: str
) -> List[Dict[str, str]]:
    """System instruction + bounded conversation history + the user message."""
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": _system_instruction_for(private_context)}
    ]
    for item in history:
        role = item.get("role")
        content = (item.get("content") or "").strip()
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})
    user_content = f"{private_context}\n\n{message}".strip() if private_context else message
    messages.append({"role": "user", "content": user_content})
    return messages


def _extract_content(payload: Any) -> str:
    """ONLY the final assistant content. reasoning_content is never touched."""
    if not isinstance(payload, dict):
        return ""
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    if not isinstance(message, dict):
        return ""
    content = message.get("content")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):  # defensive: some providers return parts
        parts = [
            part.get("text", "")
            for part in content
            if isinstance(part, dict) and isinstance(part.get("text"), str)
        ]
        return " ".join(part for part in parts).strip()
    return ""


def _classify(status: int) -> str:
    if status == 429:
        return "rate_limited"
    if status in (408, 409, 425):
        return "timeout"
    if status >= 500:
        return "transient_5xx"
    if status == 401 or status == 403:
        return "auth"
    return f"http_{status}"


def generate_reply_detailed(
    message: str, history: List[Dict[str, str]], private_context: str = ""
) -> Dict[str, Any]:
    """One Groq attempt. Same contract as the Gemini implementation."""
    result: Dict[str, Any] = {
        "text": None,
        "model": None,
        "preferred": MODEL,
        "provider": "groq",
        "attempts": [],
        "fallback": True,
    }

    key = api_key()
    if not key:
        result["attempts"].append({"model": MODEL, "reason": "no_api_key"})
        logger.warning("ask_kavach provider=groq model=%s outcome=no_api_key fallback_used=true", MODEL)
        return result

    messages = _build_messages(history, message, private_context)
    started = time.monotonic()

    try:
        response = httpx.post(
            ENDPOINT,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": MODEL, "messages": messages,
                  "temperature": TEMPERATURE, "max_tokens": MAX_TOKENS},
            timeout=TIMEOUT_SECONDS,
        )
    except httpx.TimeoutException:
        result["attempts"].append({"model": MODEL, "reason": "timeout"})
        logger.info("ask_kavach provider=groq model=%s outcome=timeout elapsed_ms=%d fallback_used=true",
                    MODEL, int((time.monotonic() - started) * 1000))
        return result
    except httpx.HTTPError:
        result["attempts"].append({"model": MODEL, "reason": "connection"})
        logger.info("ask_kavach provider=groq model=%s outcome=connection elapsed_ms=%d fallback_used=true",
                    MODEL, int((time.monotonic() - started) * 1000))
        return result

    elapsed_ms = int((time.monotonic() - started) * 1000)

    if response.status_code == 200:
        try:
            payload = response.json()
        except ValueError:
            result["attempts"].append({"model": MODEL, "reason": "malformed"})
            logger.info("ask_kavach provider=groq model=%s outcome=malformed elapsed_ms=%d fallback_used=true",
                        MODEL, elapsed_ms)
            return result
        text = _extract_content(payload)
        if not text:
            result["attempts"].append({"model": MODEL, "reason": "empty"})
            logger.info("ask_kavach provider=groq model=%s outcome=empty elapsed_ms=%d fallback_used=true",
                        MODEL, elapsed_ms)
            return result
        result["text"] = text
        result["model"] = MODEL
        result["fallback"] = False
        logger.info("ask_kavach provider=groq model=%s outcome=success elapsed_ms=%d fallback_used=false",
                    MODEL, elapsed_ms)
        return result

    reason = _classify(response.status_code)
    result["attempts"].append({"model": MODEL, "reason": reason})
    # Retry-After is honoured as information only (no cooldown machinery, no retry).
    retry_after = (response.headers.get("retry-after") or "").strip()
    logger.info(
        "ask_kavach provider=groq model=%s outcome=%s status=%s elapsed_ms=%d retry_after=%s fallback_used=true",
        MODEL, reason, response.status_code, elapsed_ms, retry_after or "none",
    )
    return result
