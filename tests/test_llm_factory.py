"""
Tests for app.llm.factory and provider abstractions.
"""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

from app.config.settings import ModelProvider, Settings
from app.llm.base import BaseLLMProvider


# ── Factory tests ──────────────────────────────────────────────────────────────

class TestLLMFactory:
    def test_openai_provider_returned_when_configured(self) -> None:
        """Factory returns OpenAIProvider when MODEL_PROVIDER=openai."""
        mock_settings = Settings(
            model_provider=ModelProvider.OPENAI,
            openai_api_key="sk-test-key",
        )
        with patch("app.llm.factory.get_settings", return_value=mock_settings):
            with patch("app.llm.factory.get_llm_provider.cache_clear"):
                from app.llm.factory import get_llm_provider
                get_llm_provider.cache_clear()

                with patch("app.llm.openai_provider.AsyncOpenAI"):
                    provider = get_llm_provider()
                    from app.llm.openai_provider import OpenAIProvider
                    assert isinstance(provider, OpenAIProvider)
                    get_llm_provider.cache_clear()

    def test_ollama_provider_returned_when_configured(self) -> None:
        """Factory returns OllamaProvider when MODEL_PROVIDER=ollama."""
        mock_settings = Settings(model_provider=ModelProvider.OLLAMA)
        with patch("app.llm.factory.get_settings", return_value=mock_settings):
            from app.llm.factory import get_llm_provider
            get_llm_provider.cache_clear()

            with patch("httpx.AsyncClient"):
                provider = get_llm_provider()
                from app.llm.ollama_provider import OllamaProvider
                assert isinstance(provider, OllamaProvider)
                get_llm_provider.cache_clear()

    def test_invalid_provider_raises_value_error(self) -> None:
        """Factory raises ValueError for unknown provider string."""
        mock_settings = MagicMock()
        mock_settings.model_provider = "unknown_provider"

        with patch("app.llm.factory.get_settings", return_value=mock_settings):
            from app.llm.factory import get_llm_provider
            get_llm_provider.cache_clear()

            with pytest.raises((ValueError, AttributeError)):
                get_llm_provider()
            get_llm_provider.cache_clear()


# ── Settings tests ─────────────────────────────────────────────────────────────

class TestSettings:
    def test_default_model_provider_is_openai(self) -> None:
        """Default provider should be openai."""
        s = Settings()
        assert s.model_provider == ModelProvider.OPENAI

    def test_openai_api_key_stripped(self) -> None:
        """Leading/trailing whitespace stripped from API key."""
        s = Settings(openai_api_key="  sk-abc  ")
        assert s.openai_api_key == "sk-abc"

    def test_cache_path_is_absolute(self) -> None:
        """cache_path property returns absolute Path."""
        s = Settings(cache_dir=".cache")
        assert s.cache_path.is_absolute()

    def test_chroma_path_is_absolute(self) -> None:
        """chroma_path property returns absolute Path."""
        s = Settings(chroma_persist_dir=".chroma_db")
        assert s.chroma_path.is_absolute()

    def test_max_diff_lines_non_negative(self) -> None:
        """max_diff_lines must be >= 0."""
        s = Settings(max_diff_lines=0)
        assert s.max_diff_lines == 0

        with pytest.raises(Exception):
            Settings(max_diff_lines=-1)

    def test_model_provider_enum_values(self) -> None:
        """ModelProvider enum has expected values."""
        assert ModelProvider.OPENAI.value == "openai"
        assert ModelProvider.OLLAMA.value == "ollama"


# ── BaseLLMProvider contract tests ────────────────────────────────────────────

class TestBaseLLMProvider:
    def test_cannot_instantiate_abstract_class(self) -> None:
        """BaseLLMProvider is abstract and cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseLLMProvider()  # type: ignore[abstract]

    def test_concrete_subclass_must_implement_all_methods(self) -> None:
        """A subclass missing any abstract method cannot be instantiated."""
        class IncompleteProvider(BaseLLMProvider):
            @property
            def model_name(self) -> str:
                return "test"
            # Missing: complete, stream, embed

        with pytest.raises(TypeError):
            IncompleteProvider()  # type: ignore[abstract]
