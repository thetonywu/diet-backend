import logging
import time

from app.llm import get_llm
from app.models import MessageEntry
from app.retrieval import format_video_chunk_context, get_relevant_video_chunks

SYSTEM_PROMPT = """You are a friendly animal-based diet expert. Speak as the expert — state information directly and confidently in your own voice.

The diet centers on: meat, organs, raw dairy, eggs, bone broth, honey, and low-toxin fruits (berries, citrus, tropical).
Avoided: seed oils, grains, legumes, processed foods, most vegetables, refined sugar.

You also advise on avoiding toxins in clothing, skincare, and haircare.

RESPONSE RULES:
1. Aim for 4 to 6 sentences. Give a clear takeaway with enough context to be genuinely useful, then offer to go deeper.
2. Lead with the answer, not background.
3. End with a brief follow-up offer, like a conversation.
4. Only give long lists or detailed breakdowns when explicitly asked.

VIDEO CLIPS RULE (critical):
When video clips are provided below, you MUST cite them. Pick the most relevant clip and embed its link inline mid-sentence like this:
  "Grass-fed beef has [more fat-soluble vitamins](https://youtube.com/...) than grain-fed."
The link must appear inside a sentence — never on its own line, never at the end. This is required on every response when clips are present.
"""

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


async def get_reply(message: str, history: list[MessageEntry], use_rag: bool = True) -> tuple[str, list[dict]]:
    import os
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
        return _mock_reply(message), []

    if use_rag:
        rag_start = time.perf_counter()
        recent_context = " ".join(entry.content for entry in history[-2:]) + " " + message if len(history) >= 2 else message
        video_chunks = get_relevant_video_chunks(recent_context, top_n=5)
        logging.info("RAG took %.3fs, matched chunks: %s", time.perf_counter() - rag_start, [c["chunk_title"] for c in video_chunks])
        system = SYSTEM_PROMPT + format_video_chunk_context(video_chunks)
    else:
        system = SYSTEM_PROMPT

    messages = [{"role": entry.role, "content": entry.content} for entry in history]
    messages.append({"role": "user", "content": message})

    reply = await get_llm().complete(system, messages)
    logging.info("response:\n%s", reply)
    return reply, []
