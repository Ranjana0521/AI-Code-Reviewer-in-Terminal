"""
Ollama local LLM provider implementation.

Communicates with a locally-running Ollama server via its REST API.
Supports chat completions (streaming + non-streaming) and uses a simple
cosine-based stub for embeddings when the model doesn't support them.
"""

from __future__ import annotations

import json
from typing import AsyncIterator

import httpx
from tenacity import retry, stop_after_attempt, wait_fixed

from app.config.settings import get_settings
from app.llm.base import BaseLLMProvider


class OllamaProvider(BaseLLMProvider):
    """Concrete LLM provider backed by a local Ollama server."""

    def __init__(self) -> None:
        settings = get_settings()
        self._base_url = settings.ollama_base_url.rstrip("/")
        self._model = settings.ollama_model
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=120.0)

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def model_name(self) -> str:  # noqa: D102
        return f"ollama/{self._model}"

    # ── Non-streaming completion ───────────────────────────────────────────────

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(1), reraise=True)
    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> str:
        """Return the full completion from Ollama as a single string."""
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
            "stream": False,
        }
        response = await self._client.post("/api/chat", json=payload)
        response.raise_for_status()
        data = response.json()
        return data.get("message", {}).get("content", "")

    # ── Streaming completion ───────────────────────────────────────────────────

    async def stream(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        """Yield tokens from a streaming Ollama completion."""
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
            "stream": True,
        }
        async with self._client.stream("POST", "/api/chat", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.strip():
                    continue
                try:
                    chunk = json.loads(line)
                    content = chunk.get("message", {}).get("content", "")
                    if content:
                        yield content
                except json.JSONDecodeError:
                    continue

    # ── Embeddings ────────────────────────────────────────────────────────────

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings via Ollama's ``/api/embeddings`` endpoint.

        Falls back gracefully if the model doesn't support embeddings.
        """
        embeddings: list[list[float]] = []
        for text in texts:
            try:
                resp = await self._client.post(
                    "/api/embeddings",
                    json={"model": self._model, "prompt": text},
                )
                resp.raise_for_status()
                embeddings.append(resp.json()["embedding"])
            except Exception:
                # Return a zero vector as a safe fallback
                embeddings.append([0.0] * 384)
        return embeddings
