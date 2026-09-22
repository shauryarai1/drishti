"""NVIDIA NIM client for Ask KAVACH — primary provider.

OpenAI-compatible endpoint: POST https://integrate.api.nvidia.com/v1/chat/completions
Auth: `Authorization: Bearer $NVIDIA_API_KEY` (account/API-level key, never bound
to a single model).

Design
------
* One centralized approved model registry (below or `NVIDIA_MODELS` in the
  environment) — the list is never duplicated elsewhere.
* Tiers: FAST -> QUALITY -> GENERAL_FALLBACK. Within a tier, healthy models are
  preferred, ordered by recent failures then recent latency; a model that has
  tripped a problem is parked (cooldown) so it is not retried immediately.
* Latency-first failover: at most `MAX_ATTEMPTS` NVIDIA attempts for one user
  message, short per-attempt timeouts, and a hard overall ceiling. Each attempt's
  timeout is clipped to the remaining budget, so a hanging model can never
  overrun it. After that the caller falls through to Gemini.
* Gemini (chat.gemini) remains the emergency fallback and is applied by the
  caller, not here.

Privacy
-------
Only the final assistant content is ever extracted. `reasoning_content` (and any
other hidden chain-of-thought field) is never read, logged, returned or
archived — NVIDIA has been live-confirmed to return `reasoning_content`, so this
is a hard boundary: only `choices[0].message.content` can become an answer.
Provider API keys, headers and raw provider payloads are never logged or
returned.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx

# Reuse the exact KAVACH instructions so behaviour is unchanged.
from chat.gemini import _system_instruction_for

logger = logging.getLogger("kavach.chat")

try:  # server-side only; a real environment always wins
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
except Exception:  # pragma: no cover - dotenv is optional
    pass

BASE_URL = "https://integrate.api.nvidia.com/v1"
ENDPOINT = f"{BASE_URL}/chat/completions"

TIER_FAST = "FAST"
TIER_QUALITY = "QUALITY"
TIER_FALLBACK = "GENERAL_FALLBACK"
TIER_ORDER: Tuple[str, ...] = (TIER_FAST, TIER_QUALITY, TIER_FALLBACK)

# Approved provider registry: ONE primary model, chosen from live evidence.
#
# Every id was verified present for this account via `GET /v1/models` (200).
# Operational evidence from this deployment:
#   * nvidia/nemotron-3-super-120b-a12b answered 200 (sub-second) -> PRIMARY.
#   * nvidia/nemotron-3.5-lightning-30b-a3b timed out repeatedly (never a
#     usable first attempt), and the other candidates either timed out or
#     returned 503, so they were removed rather than left as slow dead weight.
# Ask KAVACH is therefore: one NVIDIA primary attempt, then the Gemini
# emergency fallback - no long chain of models.
MODEL_REGISTRY: Tuple[Tuple[str, str, float], ...] = (
    ("nvidia/nemotron-3-super-120b-a12b", TIER_FAST, 12.0),
)

DEFAULT_MODEL_TIMEOUT = 12.0

# One primary attempt, one short budget: a dead model must never make the user
# wait. After the single attempt the caller falls through to the Gemini
# emergency fallback.
MAX_ATTEMPTS = 1
TOTAL_BUDGET_SECONDS = 12.0

# Transient problems park a model briefly. An account-specific unavailable model
# is parked far longer so repeated users do not keep wasting attempts on it.
COOLDOWN_SECONDS = 90.0
UNAVAILABLE_COOLDOWN_SECONDS = 3600.0

# Transient provider/model conditions -> short cooldown, try another model.
TRANSIENT_STATUS = frozenset({408, 409, 425, 429, 500, 502, 503, 504, 529})
# Model-level conditions -> this model is unusable for now; park it for a long time.
MODEL_STATUS = frozenset({404, 410})
# Provider-level auth failure -> trying other models cannot help; stop.
AUTH_STATUS = frozenset({401, 403})


# Minimal in-memory health. Deterministic and cheap: no benchmarking.
@dataclass
class ModelHealth:
    successes: int = 0
    failures: int = 0
    last_latency: Optional[float] = None
    cooldown_until: float = 0.0


_HEALTH: Dict[str, ModelHealth] = {}


def approved_models() -> Tuple[Tuple[str, str, float], ...]:
    """The registry, or a `NVIDIA_MODELS` env override (comma-separated ids)."""
    override = (os.environ.get("NVIDIA_MODELS") or "").strip()
    if not override:
        return MODEL_REGISTRY
    ids = [item.strip() for item in override.split(",") if item.strip()]
    if not ids:
        return MODEL_REGISTRY
    known = {model_id: (tier, timeout) for model_id, tier, timeout in MODEL_REGISTRY}
    return tuple(
        (model_id, *known.get(model_id, (TIER_FAST, DEFAULT_MODEL_TIMEOUT))) for model_id in ids
    )


def primary_model() -> str:
    """The intended first model for this deployment."""
    return MODEL_REGISTRY[0][0]


def api_key() -> Optional[str]:
    return os.environ.get("NVIDIA_API_KEY")


def health_snapshot() -> Dict[str, Dict[str, Any]]:
    return {
        model_id: {
            "successes": h.successes,
            "failures": h.failures,
            "last_latency": h.last_latency,
            "cooldown_for": max(0.0, round(h.cooldown_until - time.monotonic(), 1)),
        }
        for model_id, h in _HEALTH.items()
    }


def reset_health() -> None:
    _HEALTH.clear()


def _health(model_id: str) -> ModelHealth:
    return _HEALTH.setdefault(model_id, ModelHealth())


def _note_success(model_id: str, latency: float) -> None:
    health = _health(model_id)
    health.successes += 1
    health.last_latency = latency
    health.cooldown_until = 0.0


def _note_failure(model_id: str, *, cooldown: float) -> None:
    """Record a failure and park the model for `cooldown` seconds (0 = no park)."""
    health = _health(model_id)
    health.failures += 1
    if cooldown > 0:
        health.cooldown_until = time.monotonic() + cooldown


def select_order(now: Optional[float] = None) -> List[Tuple[str, float]]:
    """Deterministic attempt order: healthy before parked, then tier order.

    Health comes first so a parked model never outranks a healthy one; among
    healthy models the tier order applies (FAST -> QUALITY -> GENERAL_FALLBACK),
    then recent failures and recent latency.
    """
    now = time.monotonic() if now is None else now
    tier_position = {tier: index for index, tier in enumerate(TIER_ORDER)}

    def rank(item: Tuple[str, str, float]):
        model_id, tier, _timeout = item
        health = _health(model_id)
        return (
            0 if health.cooldown_until <= now else 1,
            tier_position.get(tier, len(TIER_ORDER)),
            health.failures,
            health.last_latency if health.last_latency is not None else 0.0,
        )

    ordered = sorted(approved_models(), key=rank)
    return [(model_id, timeout) for model_id, _tier, timeout in ordered]


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


def _classify(status: int, body: str) -> Tuple[str, bool]:
    """Return (reason, retry_with_another_model)."""
    if status in AUTH_STATUS:
        return "auth", False
    if status in TRANSIENT_STATUS:
        return f"transient_{status}", True
    if status in MODEL_STATUS:
        return f"model_{status}", True
    if status == 400:
        lowered = body.lower()
        if "model" in lowered and any(
            token in lowered
            for token in ("not supported", "unsupported", "does not exist", "not found", "eol")
        ):
            return "unsupported", True
    return f"request_{status}", False


# Stable, low-cardinality vocabulary for operational logs. Never user data.
def _log_outcome(reason: str) -> str:
    if reason == "ok":
        return "success"
    if reason in ("timeout", "connection", "auth", "malformed", "empty", "budget_exhausted"):
        return reason
    if reason.startswith("transient_"):
        status = reason.split("_", 1)[1]
        if status == "429":
            return "429"
        if status.startswith("5"):
            return "5xx"
        return "other"
    if reason.startswith("model_"):
        status = reason.split("_", 1)[1]
        return status if status in ("404", "410") else "other"
    return "other"


def _fallback_occurred(result: Dict[str, Any]) -> bool:
    """True only when the preferred model did not answer on its first attempt."""
    attempts = result.get("attempts") or []
    actual = result.get("model")
    preferred = result.get("preferred")
    if not attempts or actual is None:
        return True
    first = attempts[0]
    return not (
        first.get("model") == preferred
        and first.get("reason") == "ok"
        and actual == preferred
    )


def _call_model(
    model_id: str, timeout: float, messages: List[Dict[str, str]], key: str
) -> Tuple[Optional[str], str, Optional[float]]:
    """One attempt. Returns (text, reason, latency)."""
    started = time.monotonic()
    try:
        response = httpx.post(
            ENDPOINT,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": model_id, "messages": messages, "temperature": 0.6, "max_tokens": 900},
            timeout=timeout,
        )
    except httpx.TimeoutException:
        return None, "timeout", time.monotonic() - started
    except httpx.HTTPError:
        # Connection refused/reset, DNS and other transport failures.
        return None, "connection", time.monotonic() - started
    latency = time.monotonic() - started

    if response.status_code == 200:
        try:
            payload = response.json()
        except ValueError:
            return None, "malformed", latency
        text = _extract_content(payload)
        return (text or None), ("ok" if text else "empty"), latency

    reason, _retry = _classify(response.status_code, response.text[:400])
    return None, reason, latency


def generate_reply_detailed(
    message: str, history: List[Dict[str, str]], private_context: str = ""
) -> Dict[str, Any]:
    """Primary provider call. Same contract as the Gemini implementation."""
    order = select_order()
    preferred = order[0][0] if order else MODEL_REGISTRY[0][0]
    result: Dict[str, Any] = {
        "text": None,
        "model": None,
        "preferred": preferred,
        "provider": "nvidia",
        "attempts": [],
    }

    started_all = time.monotonic()
    key = api_key()
    if not key:
        result["attempts"].append({"model": preferred, "reason": "no_api_key"})
        result["fallback"] = True
        logger.info(
            "ask_kavach provider=nvidia model=%s attempt=1/%d outcome=other elapsed_ms=0 cooldown=false",
            preferred, MAX_ATTEMPTS,
        )
        logger.info(
            "ask_kavach provider=nvidia nvidia_success=false attempts=0 elapsed_ms=0 gemini_fallback=true"
        )
        return result

    messages = _build_messages(history, message, private_context)
    deadline = time.monotonic() + TOTAL_BUDGET_SECONDS
    attempts = 0

    for model_id, timeout in order:
        if attempts >= MAX_ATTEMPTS:
            break

        remaining = deadline - time.monotonic()
        if remaining <= 0.5:
            result["attempts"].append({"model": model_id, "reason": "budget_exhausted"})
            logger.info(
                "ask_kavach provider=nvidia model=%s attempt=%d/%d outcome=budget_exhausted elapsed_ms=0 cooldown=false",
                model_id, attempts + 1, MAX_ATTEMPTS,
            )
            break

        attempts += 1
        # Never wait past the remaining budget: latency stays bounded even if the
        # model would otherwise hang until its own timeout.
        text, reason, latency = _call_model(model_id, min(timeout, remaining), messages, key)
        result["attempts"].append({"model": model_id, "reason": reason})
        elapsed_ms = int((latency or 0.0) * 1000)

        if text:
            _note_success(model_id, latency or 0.0)
            result["text"] = text
            result["model"] = model_id
            result["latency_ms"] = elapsed_ms
            result["fallback"] = _fallback_occurred(result)
            logger.info(
                "ask_kavach provider=nvidia model=%s attempt=%d/%d outcome=success elapsed_ms=%d cooldown=false",
                model_id, attempts, MAX_ATTEMPTS, elapsed_ms,
            )
            logger.info(
                "ask_kavach provider=nvidia nvidia_success=true attempts=%d elapsed_ms=%d gemini_fallback=false",
                attempts, int((time.monotonic() - started_all) * 1000),
            )
            return result

        if reason.startswith("model_") or reason == "unsupported":
            # Account-specific unavailability or a dead model id: park it for a
            # long time so later users do not keep burning attempts on it.
            cooldown = UNAVAILABLE_COOLDOWN_SECONDS
        elif reason.startswith("transient") or reason in ("timeout", "connection", "empty", "malformed"):
            cooldown = COOLDOWN_SECONDS
        else:
            cooldown = 0.0
        _note_failure(model_id, cooldown=cooldown)

        logger.info(
            "ask_kavach provider=nvidia model=%s attempt=%d/%d outcome=%s elapsed_ms=%d cooldown=%s",
            model_id, attempts, MAX_ATTEMPTS, _log_outcome(reason), elapsed_ms,
            "true" if cooldown > 0 else "false",
        )

        if reason == "auth" or reason.startswith("request_"):
            # Provider-level auth failure, or a problem with our own request:
            # another model cannot improve the outcome, so stop immediately.
            break

    result["fallback"] = True
    logger.info(
        "ask_kavach provider=nvidia nvidia_success=false attempts=%d elapsed_ms=%d gemini_fallback=true",
        attempts, int((time.monotonic() - started_all) * 1000),
    )
    return result


def generate_reply(
    message: str, history: List[Dict[str, str]], private_context: str = ""
) -> Optional[str]:
    """Simple variant: final assistant text, or None."""
    return generate_reply_detailed(message, history, private_context).get("text")
