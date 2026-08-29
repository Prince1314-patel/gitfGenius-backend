# Xata and AI Notes

## Xata

Xata is hosted Postgres. In this app it belongs behind the FastAPI backend as `DATABASE_URL`; the Vite frontend should never receive Xata credentials.

Local development:

```env
DATABASE_URL=sqlite:///./giftgenius.db
```

Xata:

```env
DATABASE_URL=postgresql://<user>:<password>@<host>/<database>?sslmode=require
```

Run `backend/migrations/001_xata_schema.sql` in Xata's SQL console if you want to see the tables before starting the app. Starting the backend also creates the tables automatically.

Use `GET /api/v1/dev/db-snapshot` while `ENVIRONMENT=development` to verify what database the app is writing to. It returns row counts and recent rows, but no password hashes.

## Security

- Keep DB and AI keys in `backend/.env` only.
- Auth is removed for development. Before production, add auth back and filter contacts by the current user.
- Use a limited DB user for the app, not an owner/admin credential.
- Contact notes are private data. Sending notes to an AI provider should be opt-in before production.

## Recommendation Architecture

1. Frontend calls `/api/v1/contacts/{id}/recommendations`.
2. Backend loads contact and memories.
3. Backend calls OpenRouter `openrouter/free` when `OPENROUTER_API_KEY` exists.
4. Backend falls back to local deterministic suggestions when the key is missing or the provider fails.

This keeps secrets server-side and keeps the app usable with no paid services.

## Free AI Defaults

- `openrouter/free`: best dev default because OpenRouter routes to available free models.
- Gemini API free tier: good direct provider option later if you want one Google model instead of a router.
- Groq free tier: good for fast chat-style suggestions, but rate limits are stricter.

Keep the app on `openrouter/free` until a specific free model clearly performs better for your gift data.
