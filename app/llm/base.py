"""
Abstract base class for LLM providers.

All concrete providers (OpenAI, Ollama) must implement this interface so
the rest of the application is completely decoupled from the backend.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncIterator


class BaseLLMProvider(ABC):
    """Contract that every LLM backend must satisfy."""

    # ── Non-streaming ────────────────────────────────────────────────────────

    @abstractmethod
    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> str:
        """
        Send a prompt and return the full completion as a string.

        Args:
            system_prompt: The system-level instruction.
            user_prompt: The user-level content/question.
            temperature: Sampling temperature (lower = more deterministic).
            max_tokens: Maximum tokens in the response.

        Returns:
            The model's text response.
        """

    # ── Streaming ────────────────────────────────────────────────────────────

    @abstractmethod
    async def stream(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        """
        Yield response tokens as they arrive from the model.

        Args:
            system_prompt: The system-level instruction.
            user_prompt: The user-level content/question.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens in the response.

        Yields:
            Individual text chunks/tokens.
        """
        # ``yield`` makes this a generator; subclasses must yield too.
        return
        yield  # noqa: unreachable — required for ABC typing

    # ── Embeddings ───────────────────────────────────────────────────────────

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """
        Return embedding vectors for a list of text strings.

        Args:
            texts: Strings to embed.

        Returns:
            List of float vectors, one per input text.
        """

    # ── Metadata ─────────────────────────────────────────────────────────────

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Human-readable model identifier (used in traces/logs)."""
