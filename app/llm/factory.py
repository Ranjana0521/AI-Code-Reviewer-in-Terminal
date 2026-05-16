"""
LLM provider factory.

Returns the correct ``BaseLLMProvider`` instance based on the
``MODEL_PROVIDER`` setting.  Import and call ``get_llm_provider()``
anywhere in the application — it is cached so only one instance is created.
"""

from __future__ import annotations

from functools import lru_cache

from app.config.settings import ModelProvider, get_settings
from app.llm.base import BaseLLMProvider


@lru_cache(maxsize=1)
def get_llm_provider() -> BaseLLMProvider:
    """
    Instantiate and cache the configured LLM provider.

    Returns:
        A ``BaseLLMProvider`` subclass ready for use.

    Raises:
        ValueError: If the configured provider is not supported.
    """
    settings = get_settings()

    if settings.model_provider == ModelProvider.OPENAI:
        from app.llm.openai_provider import OpenAIProvider
        return OpenAIProvider()

    if settings.model_provider == ModelProvider.OLLAMA:
        from app.llm.ollama_provider import OllamaProvider
        return OllamaProvider()

    if settings.model_provider == ModelProvider.MOCK:
        from app.llm.mock_provider import MockProvider
        return MockProvider()

    raise ValueError(
        f"Unsupported MODEL_PROVIDER '{settings.model_provider}'. "
        "Choose 'openai' or 'ollama'."
    )
