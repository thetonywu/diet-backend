import os

from openai import AsyncOpenAI

from app.models import MessageEntry

SYSTEM_PROMPT = """You are a knowledgeable and friendly animal-based diet assistant.

The animal-based diet focuses on nutrient-dense animal foods as the foundation, including:
- Meat (beef, bison, lamb, elk, etc.)
- Organs (liver, heart, kidney)
- Raw dairy (milk, cheese, butter, kefir)
- Eggs
- Bone broth
- Honey and raw honey
- Fruit (especially low-toxin fruits like berries, citrus, tropical fruits)
- Raw dairy

Foods typically avoided:
- Seed oils (canola, soybean, sunflower, etc.)
- Grains and legumes
- Processed foods
- Most vegetables (especially nightshades, leafy greens high in oxalates)
- Refined sugar

Be helpful, encouraging, and evidence-aware. Provide practical meal ideas,
nutritional guidance, and explain the reasoning behind food choices on this diet.
If a user asks about something outside your expertise, let them know politely.
Keep responses concise but informative."""

client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global client
    if client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable is not set")
        client = AsyncOpenAI(api_key=api_key)
    return client


MOCK_RESPONSES = {
    "default": (
        "Great question! On an animal-based diet, you'd want to focus on "
        "nutrient-dense animal foods like beef, eggs, and raw dairy, paired "
        "with low-toxin fruits like berries and honey for carbs. "
        "Would you like specific meal ideas?"
    ),
    "breakfast": (
        "A solid animal-based breakfast could be: 3-4 pastured eggs cooked in "
        "butter or tallow, a side of ground beef or steak, and some raw honey "
        "with berries. This gives you quality protein, healthy fats, and "
        "easy-to-digest carbs to start the day."
    ),
}


def _mock_reply(message: str) -> str:
    lower = message.lower()
    for keyword, response in MOCK_RESPONSES.items():
        if keyword in lower:
            return response
    return MOCK_RESPONSES["default"]


async def get_reply(message: str, history: list[MessageEntry]) -> str:
    if not os.getenv("OPENAI_API_KEY"):
        return _mock_reply(message)

    openai_client = _get_client()

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for entry in history:
        messages.append({"role": entry.role, "content": entry.content})

    messages.append({"role": "user", "content": message})

    response = await openai_client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=messages,
        max_tokens=1024,
        temperature=0.7,
    )

    return response.choices[0].message.content
