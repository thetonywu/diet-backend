from pydantic import BaseModel


class MessageEntry(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[MessageEntry] = []
    include_related_articles: bool = False


class RelatedArticle(BaseModel):
    title: str
    filename: str


class ChatResponse(BaseModel):
    reply: str
    related_articles: list[RelatedArticle] | None = None
