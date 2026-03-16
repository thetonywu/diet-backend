import asyncio
import logging

from fastapi import APIRouter, Depends

from app.auth import get_current_user
from app.db import insert_chat_request
from app.models import ChatRequest, ChatResponse
from app.diet_assistant import get_reply

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, user: dict = Depends(get_current_user)):
    reply = await get_reply(request.message, request.history)

    input_messages = [{"role": e.role, "content": e.content} for e in request.history]
    input_messages.append({"role": "user", "content": request.message})

    asyncio.ensure_future(
        _log_request(user["sub"], input_messages, reply)
    )

    return ChatResponse(reply=reply)


async def _log_request(user_id: str, input: list[dict], response: str) -> None:
    try:
        await insert_chat_request(user_id, input, response)
    except Exception:
        logger.exception("Failed to log chat request")
