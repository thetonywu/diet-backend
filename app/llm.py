"""
LLM provider abstraction. Switch between OpenAI and Anthropic via env vars:

  LLM_PROVIDER=openai      OPENAI_API_KEY=...    OPENAI_MODEL=gpt-4.1
  LLM_PROVIDER=anthropic   ANTHROPIC_API_KEY=... ANTHROPIC_MODEL=claude-haiku-4-5-20251001
"""

import os
from abc import ABC, abstractmethod


class LLMProvider(ABC):
    @abstractmethod
    async def complete(self, system: str, messages: list[dict], max_tokens: int = 1024) -> str:
        """
        messages: [{"role": "user"|"assistant", "content": "..."}]
        Returns the assistant reply as a string.
        """


class OpenAIProvider(LLMProvider):
    def __init__(self):
        from openai import AsyncOpenAI
        self._client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
        self._model = os.getenv("OPENAI_MODEL", "gpt-4.1")

    async def complete(self, system: str, messages: list[dict], max_tokens: int = 1024) -> str:
        resp = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "system", "content": system}, *messages],
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content


class AnthropicProvider(LLMProvider):
    def __init__(self):
        import anthropic
        self._client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        self._model = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")

    async def complete(self, system: str, messages: list[dict], max_tokens: int = 1024) -> str:
        resp = await self._client.messages.create(
            model=self._model,
            system=system,
            messages=messages,
            max_tokens=max_tokens,
        )
        return resp.content[0].text


_provider: LLMProvider | None = None


def get_llm() -> LLMProvider:
    global _provider
    if _provider is None:
        name = os.getenv("LLM_PROVIDER", "openai").lower()
        if name == "anthropic":
            _provider = AnthropicProvider()
        else:
            _provider = OpenAIProvider()
    return _provider
