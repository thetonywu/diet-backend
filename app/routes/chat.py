from fastapi import APIRouter

from app.models import ChatRequest, ChatResponse
from app.diet_assistant import get_reply

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    reply = await get_reply(request.message, request.history)
    return ChatResponse(reply=reply)
