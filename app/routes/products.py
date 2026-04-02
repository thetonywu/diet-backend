import json
import logging
import os

from fastapi import APIRouter, Depends
from openai import AsyncOpenAI

from app.auth import get_optional_user
from app.models import ProductRecommendation, ProductRecommendationRequest, ProductRecommendationResponse
from app.retrieval import get_relevant_products

logger = logging.getLogger(__name__)

router = APIRouter()

_openai = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

_SYSTEM_PROMPT = """\
You are a product recommendation assistant for Heart and Soil and Lineage Provisions — \
Paul Saladino's animal-based supplement and food brands.

Given a user message and a list of product candidates, return a JSON object with a \
"products" array containing only the products that are genuinely relevant to what the \
user is asking about.

Rules:
- Only include products that directly address the user's question or health goal.
- If the user is not asking for product recommendations or nothing is relevant, return {"products": []}.
- For each included product, write a concise "why_relevant" sentence explaining the match.
- Preserve the exact "name", "url", "price_usd", "image_url", and "best_for" values from the candidates.
- Return valid JSON only. No markdown, no explanation outside the JSON.

Response shape:
{
  "products": [
    {
      "name": "...",
      "url": "...",
      "price_usd": 52.0,
      "image_url": "...",
      "best_for": "...",
      "why_relevant": "..."
    }
  ]
}
"""


def _format_candidates(candidates: list[dict]) -> str:
    lines = []
    for i, p in enumerate(candidates, 1):
        lines.append(f"{i}. {p['name']} (${p.get('price_usd', 'N/A')}) — {p.get('brand', '')}")
        if p.get("best_for"):
            lines.append(f"   Best for: {p['best_for']}")
        if p.get("benefits"):
            lines.append(f"   Benefits: {', '.join(p['benefits'])}")
        if p.get("health_goals"):
            lines.append(f"   Health goals: {', '.join(p['health_goals'])}")
        lines.append(f"   URL: {p.get('url', '')}")
        lines.append(f"   Image URL: {p.get('image_url', '')}")
        lines.append("")
    return "\n".join(lines)


@router.post("/recommended-products", response_model=ProductRecommendationResponse)
async def recommended_products(
    body: ProductRecommendationRequest,
    _user: dict | None = Depends(get_optional_user),
) -> ProductRecommendationResponse:
    candidates, _ = get_relevant_products(body.message, top_n=body.limit + 3)

    logger.info("Product RAG candidates=%d for message: %s", len(candidates), body.message[:80])

    user_msg = f"User message: {body.message}\n\nProduct candidates:\n{_format_candidates(candidates)}\n\nReturn up to {body.limit} relevant products."

    resp = await _openai.chat.completions.create(
        model=_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )

    raw = json.loads(resp.choices[0].message.content)
    products = [ProductRecommendation(**p) for p in raw.get("products", [])]

    logger.info("Returning %d product recommendations", len(products))
    return ProductRecommendationResponse(products=products)
