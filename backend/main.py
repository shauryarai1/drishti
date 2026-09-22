"""
DRISHTI Backend â€” FastAPI application.

Endpoints:
  POST /api/chart        â€” Raw chart (existing, preserved)
  POST /api/interpretation â€” User-facing interpretation (new)
"""

import logging
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from geopy.geocoders import Nominatim

from models import BirthData
from calculator import generate_chart
from interpretation import compute_interpretation
from datetime import date as date_type
from panchang import PanchangRequest, compute_panchang
from pydantic import BaseModel
from question_engine import answer_question
from prediction.panchang_natal.summary import build_channel_interpretations
from prediction.panchang_natal import (
    build_life_summary,
    compute_daily_moon_signal,
    compute_panchang_natal_significators,
)

logger = logging.getLogger("drishti")


# Render captures stdout/stderr. The KAVACH loggers previously had no handler, so
# provider routing diagnostics were silently dropped; give the "kavach" logger tree
# a handler so Ask KAVACH operational logs actually appear in application logs.
# Only model ids, outcome categories and timings are ever logged - never keys,
# headers, prompts, user messages, private context or response text.
def _configure_kavach_logging() -> None:
    import os as _os

    kavach_logger = logging.getLogger("kavach")
    if kavach_logger.handlers:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    kavach_logger.addHandler(handler)
    kavach_logger.setLevel(_os.environ.get("KAVACH_LOG_LEVEL", "INFO").upper())
    kavach_logger.propagate = False


_configure_kavach_logging()
_geo_search = Nominatim(user_agent="drishti-reading-platform-v1.0.0 (+https://drishti-5j3u.onrender.com)")

# Simple in-memory cache for place searches: {normalized_query: (results, timestamp)}
_PLACE_CACHE: dict[str, tuple[list[dict], float]] = {}
CACHE_TTL_SECONDS = 24 * 3600  # 24 hours

app = FastAPI(title="DRISHTI")

# Trusted browser origins: the deployed frontends plus local development.
# Kept as an explicit list because authenticated calls carry credentials, and
# allow_origins=["*"] must never be combined with allow_credentials=True.
ALLOWED_ORIGINS = [
    "https://kavachtoday.com",
    "https://www.kavachtoday.com",
    "https://kavachastrology.vercel.app",
    "https://drishti-u3qt.vercel.app",
    "https://drishti-red.vercel.app",
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://127.0.0.1:3002",
]

# Request headers the browser may send, including the preflight for authenticated
# POSTs (Content-Type, Authorization) and the visitor session header.
ALLOWED_HEADERS = [
    "Content-Type",
    "Authorization",
    "X-Kavach-Session",
    "Accept",
    "Origin",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=ALLOWED_HEADERS,
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/panchang")
async def panchang_endpoint(
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    latitude: float = Query(..., description="Latitude in decimal degrees"),
    longitude: float = Query(..., description="Longitude in decimal degrees"),
    timezone: str = Query(..., description="IANA timezone name"),
    label: str = Query("", description="Optional location label"),
):
    """
    Standalone Panchang for a date and location.

    Independent astronomical/traditional calculation layer â€” it does not use or
    expose KAVACH's interpretation theory.
    """
    try:
        request = PanchangRequest(
            on_date=date_type.fromisoformat(date),
            latitude=latitude,
            longitude=longitude,
            timezone_name=timezone,
            label=label,
        )
        result = compute_panchang(request)
        from archive import record_submission

        record_submission(
            "panchang",
            {"date": date, "latitude": latitude, "longitude": longitude,
             "timezone": timezone, "label": label},
            result,
        )
        return result
    except ValueError as exc:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": str(exc)},
        )
    except Exception as exc:
        logger.error("Panchang failed: %s", exc, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": "Unable to calculate Panchang."},
        )


@app.get("/api/places/search")
async def places_search(q: str = Query(..., min_length=3, max_length=100)):
    """
    Autocomplete endpoint for birthplace search.
    Returns up to 6 location suggestions from Nominatim with caching and rate-limit handling.
    """
    normalized_q = q.strip().lower()
    
    # Check server-side cache first
    now = __import__("time").time()
    if normalized_q in _PLACE_CACHE:
        cached_results, cached_at = _PLACE_CACHE[normalized_q]
        if now - cached_at < CACHE_TTL_SECONDS:
            return {"status": "ok", "results": cached_results}
        # Stale cache entry, remove it
        del _PLACE_CACHE[normalized_q]
    
    try:
        results = _geo_search.geocode(normalized_q, language="en", timeout=5, exactly_one=False, limit=6)
    except Exception as exc:
        logger.error("Place search failed: %s", exc)
        # On any error (including 429), return cached if available, else empty
        if normalized_q in _PLACE_CACHE:
            return {"status": "ok", "results": _PLACE_CACHE[normalized_q][0]}
        return JSONResponse(
            status_code=502,
            content={"status": "error", "message": "Location service unavailable."},
        )
    
    # Convert geopy results to API response format
    if not results:
        result_dicts = []
    else:
        # geopy returns a single result when limit=1, a list otherwise
        if not isinstance(results, list):
            results = [results]
        result_dicts = [
            {
                "display": loc.address,
                "lat": round(loc.latitude, 6),
                "lon": round(loc.longitude, 6),
            }
            for loc in results
        ]
    
    # Store in cache
    _PLACE_CACHE[normalized_q] = (result_dicts, now)
    
    return {"status": "ok", "results": result_dicts}


@app.post("/api/chart")
async def chart_endpoint(payload: BirthData):
    """Existing chart endpoint â€” preserved as-is."""
    try:
        result = generate_chart(payload)
        return result
    except Exception as exc:
        return JSONResponse(
            status_code=400,
            content={"status": "ERROR", "reason": str(exc)},
        )


@app.post("/api/interpretation")
async def interpretation_endpoint(payload: BirthData):
    """
    User-facing interpretation endpoint.

    Returns only the mapped life-area guidance.
    Never exposes calculation details, planets, or astrological data.
    """
    try:
        result = compute_interpretation(payload)
        from archive import record_submission

        record_submission("reading", payload.model_dump(), result)
        return result
    except Exception as exc:
        logger.error("Interpretation failed: %s", exc, exc_info=True)
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": "We couldn't complete your reading. Please try again.",
            },
        )


#


# ---------------------------------------------------------------------------
# DEV-ONLY: Panchang natal significator engine test endpoint.
# ---------------------------------------------------------------------------
class PanchangEngineRequest(BaseModel):
    date: str
    time: str = "12:00"
    place: str = ""
    latitude: float | None = None
    longitude: float | None = None
    timezone: str = "Asia/Kolkata"


@app.post("/api/dev/panchang-engine")
async def dev_panchang_engine(payload: PanchangEngineRequest):
    try:
        result = compute_panchang_natal_significators(
            birth_date=payload.date,
            birth_time=payload.time,
            latitude=payload.latitude if payload.latitude is not None else 28.6139,
            longitude=payload.longitude if payload.longitude is not None else 77.2090,
            timezone=payload.timezone,
            place=payload.place,
        )
        result["interpretation"] = build_channel_interpretations(
            birth_date=payload.date,
            birth_time=payload.time,
            latitude=payload.latitude if payload.latitude is not None else 28.6139,
            longitude=payload.longitude if payload.longitude is not None else 77.2090,
            timezone_name=payload.timezone,
            place=payload.place,
        )
        return result
    except Exception as exc:
        logger.error("Panchang engine failed: %s", exc, exc_info=True)
        return JSONResponse(status_code=400, content={"status": "error", "message": str(exc)})

@app.post("/api/dev/daily-moon")
async def dev_daily_moon(payload: PanchangEngineRequest):
    """DEV-ONLY: daily Moon day-quality signal for a date and location."""
    try:
        return compute_daily_moon_signal(
            on_date=date_type.fromisoformat(payload.date),
            latitude=payload.latitude if payload.latitude is not None else 28.6139,
            longitude=payload.longitude if payload.longitude is not None else 77.2090,
            timezone=payload.timezone,
            label=payload.place,
        )
    except Exception as exc:
        logger.error("Daily moon signal failed: %s", exc, exc_info=True)
        return JSONResponse(status_code=400, content={"status": "error", "message": str(exc)})

# ---------------------------------------------------------------------------
# DEV-ONLY: KAVACH question chat (System B — exact question moment).
# No birth details, no natal chart.
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    conversation_id: str = ""
    question: str
    timestamp: str
    latitude: float | None = None
    longitude: float | None = None
    timezone: str = "Asia/Kolkata"
    location_label: str = ""
    is_follow_up: bool = False
    original_timestamp: str | None = None


@app.post("/api/dev/chat")
async def dev_chat(payload: ChatRequest):
    try:
        return answer_question(
            question=payload.question,
            question_timestamp=payload.timestamp,
            latitude=payload.latitude if payload.latitude is not None else 28.6139,
            longitude=payload.longitude if payload.longitude is not None else 77.2090,
            timezone_name=payload.timezone,
            location_label=payload.location_label,
            is_follow_up=payload.is_follow_up,
            original_timestamp=payload.original_timestamp,
        )
    except Exception as exc:
        logger.error("Chat failed: %s", exc, exc_info=True)
        return JSONResponse(status_code=400, content={"status": "error", "message": str(exc)})

# ---------------------------------------------------------------------------
# USER-FACING endpoints. No methodology, no debug, no raw calculation.
# ---------------------------------------------------------------------------
@app.post("/api/life-summary")
async def life_summary_endpoint(payload: PanchangEngineRequest):
    """User-facing Life Summary. Only approved interpretations are returned."""
    try:
        result = build_life_summary(
            birth_date=payload.date,
            birth_time=payload.time,
            latitude=payload.latitude if payload.latitude is not None else 28.6139,
            longitude=payload.longitude if payload.longitude is not None else 77.2090,
            timezone_name=payload.timezone,
            place=payload.place,
        )
        result.pop("_internal_engine_status", None)
        from archive import record_submission

        record_submission(
            "life_summary",
            {
                "date": payload.date,
                "time": payload.time,
                "place": payload.place,
                "latitude": payload.latitude,
                "longitude": payload.longitude,
                "timezone": payload.timezone,
            },
            result,
        )
        return result
    except Exception as exc:
        logger.error("Life summary failed: %s", exc, exc_info=True)
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "We couldn't prepare your summary right now."},
        )


_CARD_TERMS = ("tarot", "card", "cards", "upright", "reversed", "spread", "arcana",
               "wands", "cups", "swords", "pentacles", "private kavach reading",
               "situation:", "influence:")


def _sanitise_public_answer(text: str) -> str:
    """No internal mechanism may ever reach the public answer."""
    import re as _re2

    kept = []
    for sentence in _re2.split(r"(?<=[.!?])\s+", text or ""):
        if any(term in sentence.lower() for term in _CARD_TERMS):
            continue
        kept.append(sentence.strip())
    return " ".join(part for part in kept if part).strip()


@app.post("/api/ask")
async def ask_endpoint(payload: ChatRequest):
    """Public Ask KAVACH: chat first, hidden Tarot only when a reading is asked for."""
    from chat import append, get_history
    from chat.session import get_reading, set_reading
    from chat.gemini import UNAVAILABLE_MESSAGE, generate_reply_detailed
    from chat.router import NEW_READING, READING_FOLLOWUP, route_message

    question = (getattr(payload, "question", "") or "").strip()
    conversation_id = (getattr(payload, "conversation_id", "") or "").strip()
    if not conversation_id:
        label = getattr(payload, "location_label", "") or f"{getattr(payload, 'latitude', '')},{getattr(payload, 'longitude', '')}"
        conversation_id = "loc-" + str(label).strip().lower()

    # Safety first: some questions deserve real-world support, not a reading.
    try:
        from chat.reading import sensitive_response

        urgent = sensitive_response(question)
    except Exception as exc:
        logger.warning("Safety check skipped: %s", type(exc).__name__)
        urgent = None
    if urgent:
        append(conversation_id, "user", question)
        append(conversation_id, "assistant", urgent)
        from archive import record_submission

        record_submission(
            "ask",
            {"question": question, "conversation_id": conversation_id},
            {"answered": True, "answer": urgent},
        )
        return {"status": "ok", "answered": True, "answer": urgent,
                "conversation_id": conversation_id}

    history = get_history(conversation_id)
    active = get_reading(conversation_id)
    route = route_message(question, bool(active), active)

    reading = active if route == READING_FOLLOWUP else None
    tarot = "REUSED" if reading else "NOT USED"
    if route == NEW_READING:
        try:
            from chat.reading import build_reading

            reading = build_reading(question)
            tarot = "USED"
        except Exception as exc:
            logger.warning("Reading skipped, continuing as chat: %s", type(exc).__name__)
            reading, route, tarot = None, "NORMAL_CHAT", "NOT USED"

    private = ""
    if reading:
        try:
            from chat.reading import private_context

            private = private_context(reading)
        except Exception as exc:
            logger.warning("Reading context skipped: %s", type(exc).__name__)
            private = ""

    detail = {}
    answer = None
    safe_error = None

    # Operational logging: model ids, outcome categories and timings only.
    # Never keys, headers, prompts, user messages, private context or response text.
    import logging as _logging
    import time as _time

    chat_log = _logging.getLogger("kavach.chat")

    def _gemini_category(detail_map: dict) -> str:
        attempts = detail_map.get("attempts") or []
        if not attempts:
            return "other"
        reason = str(attempts[-1].get("reason") or "other")
        if reason == "quota":
            return "429"
        if reason in ("unavailable", "not_found"):
            return "404"
        if reason == "network":
            return "connection"
        if reason in ("malformed", "empty"):
            return reason
        if reason.startswith("status_5"):
            return "5xx"
        return "other"

    # Primary provider: NVIDIA NIM router (multiple approved models, bounded attempts).
    try:
        from chat.nvidia import generate_reply_detailed as nvidia_reply

        detail = nvidia_reply(question, history, private_context=private)
        answer = detail.get("text")
    except Exception as exc:
        safe_error = type(exc).__name__
        logger.error("Ask KAVACH NVIDIA provider failed: %s", safe_error)

    # Emergency fallback: the existing Gemini implementation, unchanged.
    if not answer:
        gemini_started = _time.monotonic()
        try:
            fallback = generate_reply_detailed(question, history, private_context=private)
            gemini_ms = int((_time.monotonic() - gemini_started) * 1000)
            if fallback.get("text"):
                # A different provider answered after NVIDIA failed.
                detail = {**fallback, "provider": "gemini", "fallback": True}
                answer = fallback.get("text")
                chat_log.info(
                    "ask_kavach provider=gemini success=true model=%s elapsed_ms=%d outcome=success",
                    fallback.get("model") or "unknown", gemini_ms,
                )
            else:
                if not detail:
                    detail = {**fallback, "provider": "gemini", "fallback": True}
                chat_log.info(
                    "ask_kavach provider=gemini success=false elapsed_ms=%d outcome=%s",
                    gemini_ms, _gemini_category(fallback),
                )
        except Exception as exc:
            safe_error = safe_error or type(exc).__name__
            chat_log.info(
                "ask_kavach provider=gemini success=false elapsed_ms=%d outcome=other",
                int((_time.monotonic() - gemini_started) * 1000),
            )
            logger.error("Ask KAVACH fallback provider failed: %s", type(exc).__name__)

    if answer:
        chat_log.info(
            "ask_kavach answered=true provider=%s model=%s fallback=%s",
            detail.get("provider") or "unknown",
            detail.get("model") or "unknown",
            "true" if detail.get("fallback") else "false",
        )
    else:
        chat_log.info("ask_kavach answered=false provider=none fallback=true")

    def safe_trace(status: str, raw, public) -> None:
        """Dev tracing is optional: never let it affect the answer."""
        try:
            from chat.trace import dev_tools_enabled, record_event

            if not dev_tools_enabled():
                return
            event = record_event(
                conversation_id, question=question, reading=reading,
                reused=route == READING_FOLLOWUP,
                before=active.get("draw_id") if active else None,
                model=detail, raw=raw, public=public,
                pipeline={"status": status, "stage": "generation",
                          "safe_error": safe_error or ("all_models_unavailable" if status != "ok" else None)})
            if event is not None:
                event["route"] = route
                event["tarot"] = tarot
        except Exception as trace_exc:
            logger.warning("Dev trace skipped: %s", type(trace_exc).__name__)

    from archive import record_submission

    def _archive_ask(reply: str, answered: bool, error: str | None = None) -> None:
        record_submission(
            "ask",
            {"question": question, "conversation_id": conversation_id},
            {"answered": answered, "answer": reply},
            status="SUCCEEDED" if answered else "FAILED",
            error_category=error,
        )

    if not answer:
        safe_trace("model_unavailable", None, None)
        _archive_ask(UNAVAILABLE_MESSAGE, False, "model_unavailable")
        return {"status": "ok", "answered": False, "answer": UNAVAILABLE_MESSAGE,
                "conversation_id": conversation_id}

    clean = _sanitise_public_answer(answer)
    if not clean:
        safe_trace("error", answer, None)
        _archive_ask(UNAVAILABLE_MESSAGE, False, "empty_answer")
        return {"status": "ok", "answered": False, "answer": UNAVAILABLE_MESSAGE,
                "conversation_id": conversation_id}

    safe_trace("ok", answer, clean)
    if reading is not None and route != READING_FOLLOWUP:
        set_reading(conversation_id, reading)
    append(conversation_id, "user", question)
    append(conversation_id, "assistant", clean)
    _archive_ask(clean, True)
    return {"status": "ok", "answered": True, "answer": clean,
            "conversation_id": conversation_id}


class DevTarotRequest(BaseModel):
    question: str = ""
    conversation_id: str = ""
    timestamp: str = ""
    mode: str = "local"
    generate: bool = False
    force: list[str] = []
    orientation: str = "auto"
    simulate: int = 0


@app.post("/api/dev/kavach-tarot")
async def dev_kavach_tarot(payload: DevTarotRequest):
    """DEV ONLY: Ask KAVACH inspector. Reuses the same reading engine."""
    import os

    if os.environ.get("KAVACH_ENV", "").lower() == "production" or os.environ.get("KAVACH_DEV_TOOLS") == "0":
        return JSONResponse(status_code=404, content={"status": "error", "message": "Not found"})

    from chat.inspector import inspect
    from tarot.engine import simulate_draws

    try:
        if payload.simulate:
            return {"simulation": simulate_draws(payload.simulate)}
        return inspect(
            conversation_id=payload.conversation_id.strip() or "dev-inspector",
            question=payload.question,
            mode=payload.mode if payload.mode in ("local", "chat", "redraw") else "local",
            force=payload.force or None,
            orientation=payload.orientation,
            generate=bool(payload.generate or payload.mode == "chat"),
        )
    except Exception as exc:
        logger.error("Inspector failed: %s", exc, exc_info=True)
        return JSONResponse(status_code=400, content={"status": "error", "message": "Inspector failed."})


class DevTraceRequest(BaseModel):
    conversation_id: str = ""
    index: int = 0
    probe: bool = False


@app.post("/api/dev/kavach-trace")
async def dev_kavach_trace(payload: DevTraceRequest):
    """DEV ONLY: read the trace of readings that produced real answers."""
    from chat.trace import dev_tools_enabled, get_event, list_events

    if not dev_tools_enabled():
        return JSONResponse(status_code=404, content={"status": "error", "message": "Not found"})

    conversation_id = payload.conversation_id.strip()
    if payload.probe:
        return {"status": "ok", "dev_tools": True,
                "count": len(list_events(conversation_id)) if conversation_id else 0}

    event = get_event(conversation_id, payload.index or None)
    if not event:
        return JSONResponse(status_code=404,
                            content={"status": "error", "message": "No trace for this conversation."})
    return {**event, "status": "ok"}


class KundliRequest(BaseModel):
    name: str = ""
    date: str
    time: str
    place: str = ""
    latitude: float
    longitude: float
    timezone: str = "Asia/Kolkata"


# Public Kundli Generator: calculated chart data only.
@app.post("/api/kundli")
async def kundli_endpoint(payload: KundliRequest):
    from kundli import build_kundli

    try:
        result = build_kundli(payload.model_dump())
        # Additive technical-analysis layer. A failure here must not corrupt the
        # existing Kundli response, and it must not be reported as empty astrology.
        try:
            from kundli.analysis import build_analysis

            result["analysis"] = build_analysis(result.get("chart") or {})
        except (KeyError, TypeError, ValueError, ArithmeticError) as analysis_exc:
            logger.warning("Kundli analysis section skipped: %s", type(analysis_exc).__name__)
            result["analysis"] = None
            result["analysisStatus"] = "UNAVAILABLE"
        from archive import record_submission

        record_submission("kundli", payload.model_dump(), result)
        return result
    except Exception as exc:
        logger.error("Kundli generation failed: %s", exc, exc_info=True)
        return JSONResponse(status_code=400, content={"status": "error", "message": "We could not generate this Kundli. Please check the birth details."})


# Current sidereal transits mapped to the natal houses. No interpretation.
@app.post("/api/kundli/transits")
async def kundli_transits_endpoint(payload: KundliRequest):
    from kundli import build_transits

    try:
        return build_transits(payload.model_dump())
    except Exception as exc:
        logger.error("Transit calculation failed: %s", exc, exc_info=True)
        return JSONResponse(status_code=400, content={"status": "error", "message": "We could not calculate current transits right now."})


class DailyRequest(BaseModel):
    latitude: float = 28.6139
    longitude: float = 77.209
    timezone: str = "Asia/Kolkata"
    natal_moon: str = ""
    at: str = ""
    date: str = ""
    time: str = ""
    place: str = ""


# Public Daily Prediction: natal Moon as house 1 + current transit Moon.
@app.post("/api/daily")
async def daily_endpoint(payload: DailyRequest):
    from daily import build_daily_prediction

    data = payload.model_dump()
    if not data.get("natal_moon"):
        data.pop("natal_moon", None)
    if not (data.get("date") and data.get("time")):
        for key in ("date", "time", "place"):
            data.pop(key, None)
    try:
        result = build_daily_prediction(data)
        from archive import record_submission

        record_submission("daily", data, result)
        return result
    except Exception as exc:
        logger.error("Daily prediction failed: %s", exc, exc_info=True)
        return JSONResponse(status_code=400, content={"status": "error", "message": "We could not calculate today's prediction."})


class WeeklyBirth(BaseModel):
    date: str
    time: str
    place: str = ""
    latitude: float
    longitude: float
    timezone: str = "Asia/Kolkata"


class WeeklyForecastInput(BaseModel):
    startDate: str
    place: str = ""
    latitude: float
    longitude: float
    timezone: str = "Asia/Kolkata"


class WeeklyRequest(BaseModel):
    birth: WeeklyBirth
    forecast: WeeklyForecastInput


# Public Your Week: returns ONLY the customer-safe weekly DTO.
@app.post("/api/weekly")
async def weekly_endpoint(payload: WeeklyRequest):
    from weekly import build_weekly_forecast, to_public

    try:
        week = build_weekly_forecast(
            birth=payload.birth.model_dump(),
            forecast_start=payload.forecast.startDate,
            forecast_latitude=payload.forecast.latitude,
            forecast_longitude=payload.forecast.longitude,
            forecast_timezone=payload.forecast.timezone,
        )
        public = to_public(week)
        from archive import record_submission

        record_submission(
            "weekly",
            {"birth": payload.birth.model_dump(), "forecast": payload.forecast.model_dump()},
            public,
        )
        return public
    except Exception as exc:
        logger.error("Weekly forecast failed: %s", exc, exc_info=True)
        return JSONResponse(status_code=400, content={"status": "error", "message": "We couldn't prepare your week with those details. Check your birth and location information and try again."})


class CurrentDashaRequest(BaseModel):
    birth: WeeklyBirth
    asOf: str = ""


# Public Current Dasha Reading: returns ONLY the customer-safe reading.
@app.post("/api/current-dasha-reading")
async def current_dasha_endpoint(payload: CurrentDashaRequest):
    from dasha_reading import build_current_dasha_reading

    try:
        result = build_current_dasha_reading(
            payload.birth.model_dump(), payload.asOf or None)
        from archive import record_submission

        record_submission(
            "dasha",
            {"birth": payload.birth.model_dump(), "asOf": payload.asOf},
            result,
        )
        return result
    except Exception as exc:
        logger.error("Current dasha reading failed: %s", exc, exc_info=True)
        return JSONResponse(status_code=400, content={"status": "error", "message": "We couldn't prepare the current dasha reading with those details."})


# ---------------------------------------------------------------------------
# Owner archive: request identity + the protected /api/admin API.
# Archiving is fail-open and never alters a product response.
# ---------------------------------------------------------------------------
from archive import install_archive  # noqa: E402

install_archive(app)
