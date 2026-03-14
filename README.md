# Animal Based Diet Chatbot - Backend

FastAPI backend for the animal-based diet chatbot. Uses OpenAI to generate diet-aware responses.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration

Copy the example env file and add your OpenAI API key:

```bash
cp .env.example .env
```

Edit `.env` and set your `OPENAI_API_KEY`.

## Run

```bash
uvicorn app.main:app --reload
```

The API runs at `http://localhost:8000`. Docs available at `http://localhost:8000/docs`.

## API

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
