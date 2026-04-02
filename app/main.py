import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import chat, products
from app.retrieval import _load_and_index  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    _load_and_index()
    yield


app = FastAPI(title="Animal Based Diet Chatbot API", lifespan=lifespan)

allowed_origins = [
    o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api")
app.include_router(products.router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok", "allowed_origins": allowed_origins}
