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
_geo_search = Nominatim(user_agent="drishti-place-search")

app = FastAPI(title="DRISHTI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://drishti-u3qt.vercel.app",
        "https://drishti-red.vercel.app",
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/places/search")
async def places_search(q: str = Query(..., min_length=2, max_length=100)):
    """
    Autocomplete endpoint for birthplace search.
    Returns up to 6 location suggestions from Nominatim.
    """
    try:
        results = _geo_search.geocode(q, language="en", timeout=5, exactly_one=False, limit=6)
    except Exception as exc:
        logger.error("Place search failed: %s", exc)
        return JSONResponse(
            status_code=502,
            content={"status": "error", "message": "Location service unavailable."},
        )

    if not results:
        return {"status": "ok", "results": []}

    # geopy returns a single result when limit=1, a list otherwise
    if not isinstance(results, list):
        results = [results]

    return {
        "status": "ok",
        "results": [
            {
                "display": loc.address,
                "lat": round(loc.latitude, 6),
                "lon": round(loc.longitude, 6),
            }
            for loc in results
        ],
    }


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
