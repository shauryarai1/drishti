"""
DRISHTI Backend — FastAPI application.

Endpoints:
  POST /api/chart        — Raw chart (existing, preserved)
  POST /api/interpretation — User-facing interpretation (new)
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

logger = logging.getLogger("drishti")
_geo_search = Nominatim(user_agent="drishti-reading-platform-v1.0.0 (+https://drishti-5j3u.onrender.com)")

# Simple in-memory cache for place searches: {normalized_query: (results, timestamp)}
_PLACE_CACHE: dict[str, tuple[list[dict], float]] = {}
CACHE_TTL_SECONDS = 24 * 3600  # 24 hours

app = FastAPI(title="DRISHTI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://drishti-u3qt.vercel.app",
        "https://drishti-red.vercel.app",
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


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
    """Existing chart endpoint — preserved as-is."""
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
