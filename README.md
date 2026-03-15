# Animal Based Diet Chatbot - Backend

FastAPI backend for the animal-based diet chatbot with Supabase auth and OpenAI integration.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Copy the example env file and configure:

```bash
cp .env.example .env
```

Required environment variables:

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | Your OpenAI API key |
| `OPENAI_MODEL` | Model to use (default: `gpt-4o-mini`) |
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key (for server-side DB access) |
| `SUPABASE_JWT_SECRET` | Supabase JWT secret (for verifying auth tokens) |

## Database Setup

Run the SQL migration in your Supabase SQL Editor:

```bash
# Copy and paste migrations/001_create_tables.sql into the Supabase SQL Editor
```

This creates the `conversations`, `chat_messages`, and `profiles` tables with RLS policies.

## Run

```bash
uvicorn app.main:app --reload
```

The API runs at `http://localhost:8000`. Docs available at `http://localhost:8000/docs`.

## API

All endpoints (except `/health`) require a valid Supabase JWT in the `Authorization: Bearer <token>` header.

### `POST /api/chat`

```json
{
  "message": "What should I eat for breakfast?",
  "history": []
}
```

Response:

```json
{
  "reply": "A great animal-based breakfast would be..."
}
```

### `GET /health`

Returns `{"status": "ok"}`.
