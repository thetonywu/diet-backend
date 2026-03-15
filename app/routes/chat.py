from fastapi import APIRouter, Depends

from app.auth import get_current_user
from app.models import ChatRequest, ChatResponse
from app.diet_assistant import get_reply

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, user: dict = Depends(get_current_user)):
    reply = await get_reply(request.message, request.history)
    return ChatResponse(reply=reply)
