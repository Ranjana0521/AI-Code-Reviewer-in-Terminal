"""
OpenAI LLM provider implementation.

Wraps the official ``openai`` async client and supports both streaming
and non-streaming completions, plus text embeddings.
"""

from __future__ import annotations

import asyncio
from typing import AsyncIterator

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config.settings import get_settings
from app.llm.base import BaseLLMProvider


class OpenAIProvider(BaseLLMProvider):
    """Concrete LLM provider backed by OpenAI's API."""

    def __init__(self) -> None:
        settings = get_settings()
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_model
        self._embedding_model = settings.openai_embedding_model

    # ── Properties ───────────────────────────────────────────────────────────

    @property
    def model_name(self) -> str:  # noqa: D102
        return self._model

    # ── Non-streaming completion ──────────────────────────────────────────────

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> str:
        """Return the full LLM response as a single string."""
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

    # ── Streaming completion ──────────────────────────────────────────────────

    async def stream(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        """Yield tokens from a streaming OpenAI completion."""
        async with await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        ) as response:
            async for chunk in response:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta

    # ── Embeddings ────────────────────────────────────────────────────────────

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Return embedding vectors for a batch of texts."""
        response = await self._client.embeddings.create(
            model=self._embedding_model,
            input=texts,
        )
        return [item.embedding for item in response.data]
