# F2 API

REST API for FIA Formula 2 Championship data — standings, race schedules, session results, and driver/team information.

Built as a portfolio project to learn API design, not as a wrapper around an existing API. The schema, data model, and business logic are all original.

**NOTE** *This is still a work in progress*

## Stack

- **Python 3.12+** / **FastAPI**
- **SQLAlchemy 2.0** (ORM)
- **SQLite** (local dev)
- **Pydantic** (request/response validation)

## Quick Start

```bash
git clone https://github.com/tmannion/f2-api.git
cd f2-api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # then edit .env with your own secret key
make run
```

Open http://localhost:8000/docs for the interactive Swagger UI.

## API Overview

All resource endpoints are under `/api/v1/`. GET endpoints are public. POST endpoints require an API key via the `X-API-Key` header.

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/seasons/` | List seasons |
| `GET /api/v1/rounds/?season_id=` | List rounds (filterable by season) |
| `GET /api/v1/sessions/?round_id=` | List sessions (filterable by round) |
| `GET /api/v1/drivers/` | List drivers |
| `GET /api/v1/teams/` | List teams |
| `GET /api/v1/results/?session_id=&driver_id=` | List results (filterable) |
| `GET /api/v1/standings/?season_id=` | Calculated driver championship standings |
| `GET /health` | Health check |

All list endpoints return paginated responses:

```json
{
  "items": [...],
  "total": 42,
  "limit": 20,
  "offset": 0
}
```

## Standings

The standings endpoint calculates championship positions dynamically by aggregating points across all sessions in a season:

```json
{
  "season_id": 1,
  "season_year": 2026,
  "standings": [
    {
      "position": 1,
      "driver_name": "Nikola Tsolov",
      "team_name": "Campos Racing",
      "points": 25,
      "wins": 1,
      "podiums": 1
    }
  ]
}
```

## Authentication

Write endpoints (POST) are admin-only — they exist for the API owner to manage data. Public consumers only use GET endpoints and don't need any authentication.

The API key is stored in a `.env` file (gitignored, never committed):

```
F2_API_KEY=your-secret-key-here
```

The app loads this automatically on startup via `python-dotenv`. When making POST requests (e.g. via Swagger UI or curl), include the key in the header:

```bash
curl -X POST http://localhost:8000/api/v1/seasons/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-key-here" \
  -d '{"year": 2026}'
```

When deployed, the production key is set on the server and kept secret. Users of the public API never need it.

## Running Tests

```bash
make test
```

Tests use a separate SQLite database and a fresh schema per test — no data leaks between tests.

## Project Structure

```
app/
├── main.py           # App entry point, middleware, router wiring
├── database.py       # Engine, session factory, get_db dependency
├── auth.py           # API key authentication
├── models/           # SQLAlchemy ORM models (database tables)
├── schemas/          # Pydantic schemas (API request/response shapes)
├── routers/          # Route handlers (HTTP layer)
└── crud/             # Database query logic (business layer)
```

## CI/CD

GitHub Actions pipeline:

1. **Lint** — ruff check + format (generates a patch artifact on failure)
2. **Smoke Test** — verifies the app imports cleanly
3. **Test** — runs the full pytest suite
4. **Version Bump** — auto-increments patch version via git tags on merge to main

## Design Decisions

- **Standings are calculated, not stored** — avoids a second source of truth that drifts out of sync
- **Results belong to Sessions, not directly to Rounds** — supports qualifying, sprint, and feature race data in one table
- **`team_id` on both `DriverSeasonEntry` and `Result`** — handles mid-season team switches correctly
- **Schemas are decoupled from models** — the API exposes what consumers need, not raw database structure
- **Pagination on all list endpoints** — consistent, predictable response shape

## Data

Historical data (2020-2025) can be scraped from Wikipedia using the included script:

```bash
python scripts/scrape_historical.py
```

Current season data (2026+) is entered via the POST endpoints or Swagger UI.

## License

MIT
