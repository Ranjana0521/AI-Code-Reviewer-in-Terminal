"""
Global application settings loaded from environment variables / .env file.

All settings are validated by Pydantic and accessible as a singleton via
``get_settings()``.
"""

from __future__ import annotations

from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ModelProvider(str, Enum):
    """Supported LLM backend providers."""

    OPENAI = "openai"
    OLLAMA = "ollama"


class Settings(BaseSettings):
    """
    Central configuration object.

    Values are read (in priority order) from:
    1. Environment variables
    2. ``.env`` file in the working directory
    3. Defaults defined here
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── LLM Provider ────────────────────────────────────────────────────────
    model_provider: ModelProvider = Field(
        default=ModelProvider.OPENAI,
        description="Which LLM backend to use: 'openai' or 'ollama'.",
    )

    # ── OpenAI ──────────────────────────────────────────────────────────────
    openai_api_key: str = Field(default="", description="OpenAI API key.")
    openai_model: str = Field(default="gpt-4o", description="OpenAI chat model name.")
    openai_embedding_model: str = Field(
        default="text-embedding-3-small",
        description="OpenAI embedding model name.",
    )

    # ── Ollama ───────────────────────────────────────────────────────────────
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Base URL for the local Ollama server.",
    )
    ollama_model: str = Field(
        default="llama3",
        description="Ollama model tag (e.g. 'llama3', 'codellama', 'mistral').",
    )

    # ── Langfuse Observability ───────────────────────────────────────────────
    langfuse_public_key: str = Field(default="", description="Langfuse public key.")
    langfuse_secret_key: str = Field(default="", description="Langfuse secret key.")
    langfuse_host: str = Field(
        default="https://cloud.langfuse.com",
        description="Langfuse host URL.",
    )
    langfuse_enabled: bool = Field(
        default=False,
        description="Toggle Langfuse tracing on/off.",
    )

    # ── ChromaDB / RAG ───────────────────────────────────────────────────────
    chroma_persist_dir: str = Field(
        default=".chroma_db",
        description="Directory where ChromaDB stores its data.",
    )
    chroma_collection_name: str = Field(
        default="repo_codebase",
        description="ChromaDB collection name for the current repo.",
    )

    # ── CLI Behaviour ────────────────────────────────────────────────────────
    max_diff_lines: int = Field(
        default=500,
        ge=0,
        description="Max lines of diff to send to LLM (0 = unlimited).",
    )
    stream_responses: bool = Field(
        default=True,
        description="Whether to stream LLM tokens to the terminal.",
    )
    cache_enabled: bool = Field(
        default=True,
        description="Cache LLM responses to disk to save tokens.",
    )
    cache_dir: str = Field(
        default=".cache",
        description="Directory for disk-based LLM response cache.",
    )

    # ── Derived helpers ──────────────────────────────────────────────────────
    @property
    def cache_path(self) -> Path:
        """Absolute path to the cache directory."""
        return Path(self.cache_dir).resolve()

    @property
    def chroma_path(self) -> Path:
        """Absolute path to the ChromaDB persistence directory."""
        return Path(self.chroma_persist_dir).resolve()

    @field_validator("openai_api_key", mode="before")
    @classmethod
    def _strip_api_key(cls, v: str) -> str:
        return v.strip() if v else ""


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton Settings instance."""
    return Settings()
