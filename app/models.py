from pydantic import BaseModel, Field


class MessageEntry(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[MessageEntry] = []
    use_rag: bool = True


class ChatResponse(BaseModel):
    reply: str


class ProductRecommendationRequest(BaseModel):
    message: str
    limit: int = Field(default=3, ge=1, le=5)


class ProductRecommendation(BaseModel):
    name: str
    url: str
    price_usd: float | None
    image_url: str | None
    best_for: str | None
    why_relevant: str


class ProductRecommendationResponse(BaseModel):
    products: list[ProductRecommendation]
