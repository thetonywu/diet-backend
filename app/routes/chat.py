import asyncio
import logging

from fastapi import APIRouter, Depends, Request

from app.auth import get_optional_user
from app.db import insert_chat_request
from app.limiter import rate_limit
from app.models import ChatRequest, ChatResponse
from app.diet_assistant import get_reply

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: Request, body: ChatRequest, user: dict | None = Depends(get_optional_user), _: None = Depends(rate_limit)):
    reply, matched_articles = await get_reply(body.message, body.history, body.use_rag)

    input_messages = [{"role": e.role, "content": e.content} for e in body.history]

    if user:
        asyncio.ensure_future(
            _log_request(user["sub"], body.message, input_messages, reply, matched_articles)
        )
    else:
        ip = request.client.host if request.client else "unknown"
        logger.info("Logged-out chat from %s: %s", ip, body.message)

    return ChatResponse(reply=reply)


async def _log_request(user_id: str, message: str, input: list[dict], response: str, matched_articles: list[dict]) -> None:
    try:
        await insert_chat_request(user_id, message, input, response, matched_articles)
    except Exception:
        logger.exception("Failed to log chat request")
