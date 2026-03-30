from pydantic import BaseModel


class MessageEntry(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[MessageEntry] = []
    use_rag: bool = True


class ChatResponse(BaseModel):
    reply: str
