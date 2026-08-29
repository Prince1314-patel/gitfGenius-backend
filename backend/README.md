# GiftGenius Backend

FastAPI backend for contacts, memories, birthdays, and gift recommendations.

## Run

```bash
cp .env.example .env
uv run --with-requirements requirements.txt uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- API: http://127.0.0.1:8000
- Swagger: http://127.0.0.1:8000/docs

## Environment

Local development uses SQLite by default:

```bash
DATABASE_URL=sqlite:///./giftgenius.db
SECRET_KEY=change-this-before-production
ENVIRONMENT=development
DEBUG=False
OPENROUTER_API_KEY=
OPENROUTER_MODEL=openrouter/free
```

For Xata, set `DATABASE_URL` to the Postgres connection string from Xata:

```bash
DATABASE_URL=postgresql://<user>:<password>@<host>/<database>?sslmode=require
```

Then run [migrations/001_xata_schema.sql](C:/Projects/gitfGenius-backend/backend/migrations/001_xata_schema.sql) in Xata's SQL console, or just start the backend and let SQLModel create the same tables.

Keep database credentials only on the backend. The Vite frontend should never receive the Xata URL, password, or any service/database key.

## AI

Recommendations use OpenRouter when `OPENROUTER_API_KEY` is set. Without a key, the API returns local fallback recommendations so the app stays usable during development.

## Test

```bash
uv run --with-requirements requirements.txt --with pytest pytest -q
```

## Endpoints

- `GET /health`
- `GET /api/v1/contacts`
- `POST /api/v1/contacts`
- `PUT /api/v1/contacts/{contact_id}`
- `DELETE /api/v1/contacts/{contact_id}`
- `GET /api/v1/contacts/{contact_id}/memories`
- `POST /api/v1/contacts/{contact_id}/memories`
- `DELETE /api/v1/contacts/{contact_id}/memories/{memory_id}`
- `GET /api/v1/contacts/{contact_id}/recommendations`
- `GET /api/v1/dev/db-snapshot` development-only database and AI snapshot

## Production Notes

Authentication is intentionally removed for development. Before production, add auth back, filter every contact and memory by the signed-in user, and avoid sending more personal note data to AI providers than the recommendation needs.
