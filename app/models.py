from pydantic import BaseModel


class MessageEntry(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[MessageEntry] = []


class ChatResponse(BaseModel):
    reply: str
