FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download embedding model so startup doesn't fetch it at runtime
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-small-en-v1.5')"

COPY . .

ENV PORT=8000
EXPOSE 8000

CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT
