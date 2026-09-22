"""HTTP surface for KAVACH YES / NO.

This router is intentionally NOT mounted on the application: wiring it into
`main.py` would modify an existing frozen file, so that integration change is
left for explicit owner approval. The router is fully functional on its own and
is exercised through its own TestClient in the tests.

To expose the feature publicly, an authorized change to `backend/main.py` would
be needed:

    from yesno.api import router as yes_no_router
    app.include_router(yes_no_router)

No existing endpoint, router or archive behaviour is altered by this module.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from .engine import evaluate_yes_no
from .timezone import resolve_local_time

logger = logging.getLogger("kavach.yesno")

router = APIRouter(prefix="/api/yes-no", tags=["yes-no"])


class YesNoRequest(BaseModel):
    question: str
    # ISO-8601 instant. A timezone-aware value is converted into the resolved
    # local zone; a naive value is treated as the user's local wall-clock time.
    timestamp: str = ""
    timezone: str = ""
    # Browser UTC offset in minutes east of UTC (IST = +330). Optional: older
    # clients that omit it keep working exactly as before.
    utc_offset_minutes: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


def _parse_instant(value: str) -> Optional[datetime]:
    text = (value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def _log_resolution(instant: datetime, timezone_name: str, local: datetime,
                    resolution: Dict[str, object]) -> None:
    """Privacy-safe diagnostics: time resolution only.

    Never logs the question, identity, tokens, planets, the relationship or the
    interpretation.
    """
    logger.info(
        "yesno_time_resolution instant=%s timezone=%s submitted_offset=%s "
        "resolved_local=%s source=%s matched=%s",
        instant.isoformat(),
        timezone_name or "-",
        resolution.get("submitted_offset_minutes"),
        local.strftime("%H:%M"),
        resolution.get("source"),
        resolution.get("matched"),
    )


@router.post("")
def yes_no(payload: YesNoRequest) -> Dict[str, Any]:
    """Deterministic YES / NO / 50-50 from the exact local time of the question."""
    instant = _parse_instant(payload.timestamp)
    if instant is None:
        return {"status": "invalid", "message": "A valid ISO-8601 timestamp is required."}

    try:
        local, resolution = resolve_local_time(
            instant,
            timezone_name=payload.timezone,
            utc_offset_minutes=payload.utc_offset_minutes,
        )
    except ValueError:
        return {"status": "invalid", "message": "A timezone or coordinates are required."}

    _log_resolution(instant, payload.timezone, local, resolution)

    result = evaluate_yes_no(payload.question, local, timezone_name=payload.timezone)
    # Public payload: the verdict, the explanation and the resolved wall clock.
    # No numbers, planets, relationship or other internal mechanics.
    return {"status": "ok", **result.to_public(), "local_time": local.strftime("%H:%M")}
