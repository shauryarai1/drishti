# Vedic Kundli Calculator

Phase 1 implementation: birth data → Swiss Ephemeris astronomical calculation → Vedic sidereal chart data → North Indian Kundli visualization.

## Astrology settings

- System: Vedic
- Zodiac: Sidereal
- Ayanamsa: Lahiri
- House system: Placidus
- Layout: North Indian

## Prerequisites

- Python 3.9+
- Node.js 18+
- pip, npm

## Backend setup

```bash
cd backend
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

The backend expects ephemeris data under `backend/ephemeris/`. If missing, install Swiss Ephemeris data files and set `SWISS_EPHEMERIS_PATH` in `config.py`.

## Frontend setup

```bash
cd frontend
npm install
npm run dev
```

The frontend proxies `/api` to `http://localhost:8000`.

## Run tests

```bash
cd backend
pytest
```

## API

`POST /api/chart`
Body:
```json
{
  "date": "1990-01-15",
  "time": "14:30",
  "place": "Delhi, India",
  "ayanamsa": "lahiri"
}
```

## Notes

- All planetary positions and house cusps are calculated by Swiss Ephemeris.
- Place resolution uses `geopy` Nominatim and `timezonefinder`.
- Debug mode in the frontend shows the full calculation trace.