"""Gemini client for Ask KAVACH (Interactions API).

Endpoint: POST https://generativelanguage.googleapis.com/v1beta/interactions
Docs: Interactions API is Google's default interface (GA June 2026).
Auth: x-goog-api-key header. api_version is a required query parameter.

The API key is read from the server environment, or from backend/.env when the
process environment does not define it. It is never logged or returned.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger("kavach.chat")

ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/interactions"
TIMEOUT_SECONDS = 45.0

# Preferred first, then lighter models. Only models this key can access.
MODEL_PRIORITY = (
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-2.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-2.5-flash-lite",
)
MODEL = MODEL_PRIORITY[0]  # kept for compatibility

SYSTEM_INSTRUCTION = (
    "You are Ask KAVACH, a conversational assistant inside KAVACH.\n\n"
    "Understand what the user is actually asking and respond naturally, clearly and concisely.\n\n"
    "Maintain the context of the conversation. Short follow-ups such as 'why?', 'are you sure?', "
    "'what about that?', and 'should I then?' should be interpreted using the preceding conversation "
    "when relevant.\n\n"
    "If the user clearly changes subject, follow the new subject instead of forcing the previous context.\n\n"
    "Do not pretend to know information that has not been provided.\n\n"
    "Do not claim certainty about future events or another person's private thoughts.\n\n"
    "Avoid repetitive canned introductions, conclusions and formulaic phrasing."
)

READING_INSTRUCTION = (
    "Private KAVACH reading context is supplied with this message. Treat it as the "
    "authoritative interpretive basis for your answer.\n\n"
    "Answer the user's actual question primarily and directly from that context. "
    "Synthesise the supplied meanings into one coherent interpretation rather than "
    "explaining them one by one.\n\n"
    "Do not add generic coaching, motivational talk, practical business or marketing "
    "advice, psychological explanations or outside interpretations unless the supplied "
    "context genuinely supports them. Do not invent reasons beyond it.\n\n"
    "Never mention cards, Tarot, spreads, orientations, positions or any hidden "
    "mechanism. Speak like an experienced astrologer giving a focused consultation: "
    "direct, specific and concise, roughly three to six sentences unless the user asks "
    "for more detail.\n\n"
    "For yes/no questions give a clear direction with its main supporting reason and "
    "any condition attached. Do not claim certainty about future outcomes or another "
    "person's private thoughts."
)


def _system_instruction_for(private_context: str) -> str:
    """Reading answers get the tighter instruction; normal chat does not."""
    if private_context:
        return f"{SYSTEM_INSTRUCTION}\n\n{READING_INSTRUCTION}"
    return SYSTEM_INSTRUCTION


UNAVAILABLE_MESSAGE = "Ask KAVACH is having trouble responding right now. Please try again."

_ENV_LOADED = False


def _load_env_file() -> None:
    """Load backend/.env once if the variable is not already in the environment."""
    global _ENV_LOADED
    if _ENV_LOADED or os.environ.get("GEMINI_API_KEY"):
        _ENV_LOADED = True
        return
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            if name.strip() and value.strip():
                os.environ.setdefault(name.strip(), value.strip())
    _ENV_LOADED = True


def api_key() -> Optional[str]:
    _load_env_file()
    return os.environ.get("GEMINI_API_KEY")


def _transcript(history: List[Dict[str, str]], message: str) -> str:
    lines: List[str] = []
    for item in history:
        speaker = "User" if item.get("role") == "user" else "Assistant"
        lines.append(f"{speaker}: {item.get('content', '').strip()}")
    lines.append(f"User: {message.strip()}")
    return "\n".join(lines)


def _extract_text(payload: Any) -> str:
    found: List[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            if node.get("type") == "text" and isinstance(node.get("text"), str):
                found.append(node["text"])
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(payload)
    return " ".join(part.strip() for part in found if part.strip()).strip()


def _fallback_reason(status: int, body: str) -> Optional[str]:
    """Return a fallback reason only for model-specific failures."""
    if status == 429:
        return "quota"
    if status == 404:
        return "unavailable"
    if status == 400:
        lowered = body.lower()
        if "model" in lowered and any(
            token in lowered for token in ("not supported", "unsupported", "does not exist", "not found")
        ):
            return "unsupported"
    return None


def generate_reply(message: str, history: List[Dict[str, str]],
                   private_context: str = "") -> Optional[str]:
    """Try each model once (no loops). Returns None when unavailable."""
    key = api_key()
    if not key:
        return None

    prompt = _transcript(history, message)
    if private_context:
        prompt = f"{private_context}\n\n{prompt}"

    payload = {
        "input": prompt,
        "system_instruction": _system_instruction_for(private_context),
    }

    for model in MODEL_PRIORITY:
        try:
            response = httpx.post(
                ENDPOINT,
                params={"api_version": "v1beta"},
                headers={"x-goog-api-key": key, "Content-Type": "application/json"},
                json={**payload, "model": model},
                timeout=TIMEOUT_SECONDS,
            )
        except httpx.HTTPError:
            logger.info("Ask KAVACH model failed: %s | reason: network", model)
            return None

        if response.status_code == 200:
            try:
                data = response.json()
            except ValueError:
                logger.info("Ask KAVACH model returned malformed data: %s", model)
                return None
            if isinstance(data, list):
                data = data[0] if data else {}
            text = _extract_text(data)
            if text:
                logger.info("Ask KAVACH model: %s", model)
                return text
            logger.info("Ask KAVACH model returned empty output: %s", model)
            return None

        reason = _fallback_reason(response.status_code, response.text[:400])
        if not reason:
            logger.info("Ask KAVACH model: %s | status: %s | no fallback", model, response.status_code)
            return None
        logger.info("Ask KAVACH fallback from: %s | reason: %s", model, reason)

    return None


def generate_reply_detailed(message: str, history: List[Dict[str, str]],
                            private_context: str = "") -> Dict[str, Any]:
    """DEV/audit variant: identical policy, plus model and fallback metadata."""
    result: Dict[str, Any] = {"text": None, "model": None,
                              "preferred": MODEL_PRIORITY[0], "attempts": []}
    key = api_key()
    if not key:
        result["attempts"].append({"model": MODEL_PRIORITY[0], "reason": "no_api_key"})
        return result

    prompt = _transcript(history, message)
    if private_context:
        prompt = f"{private_context}\n\n{prompt}"
    payload = {"input": prompt, "system_instruction": _system_instruction_for(private_context)}

    for model in MODEL_PRIORITY:
        try:
            response = httpx.post(
                ENDPOINT,
                params={"api_version": "v1beta"},
                headers={"x-goog-api-key": key, "Content-Type": "application/json"},
                json={**payload, "model": model},
                timeout=TIMEOUT_SECONDS,
            )
        except httpx.HTTPError:
            result["attempts"].append({"model": model, "reason": "network"})
            return result

        if response.status_code == 200:
            try:
                data = response.json()
            except ValueError:
                result["attempts"].append({"model": model, "reason": "malformed"})
                return result
            if isinstance(data, list):
                data = data[0] if data else {}
            text = _extract_text(data)
            if text:
                result["text"] = text
                result["model"] = model
                return result
            result["attempts"].append({"model": model, "reason": "empty"})
            return result

        reason = _fallback_reason(response.status_code, response.text[:400])
        result["attempts"].append({"model": model, "reason": reason or f"status_{response.status_code}"})
        if not reason:
            return result

    return result
