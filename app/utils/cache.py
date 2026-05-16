"""
Disk-based LLM response cache.

Uses ``diskcache`` to store prompt → response mappings so repeated
identical requests don't consume API tokens.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from app.config.settings import get_settings


class LLMCache:
    """
    Simple key-value cache backed by diskcache.

    The cache key is a SHA-256 hash of (model, system_prompt, user_prompt).
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._enabled = settings.cache_enabled
        self._cache: Any = None

        if self._enabled:
            try:
                import diskcache  # type: ignore[import-untyped]

                cache_dir = settings.cache_path
                cache_dir.mkdir(parents=True, exist_ok=True)
                self._cache = diskcache.Cache(str(cache_dir))
            except Exception:
                self._enabled = False

    def _make_key(self, model: str, system: str, user: str) -> str:
        """Create a deterministic cache key."""
        payload = json.dumps({"model": model, "system": system, "user": user}, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()

    def get(self, model: str, system: str, user: str) -> str | None:
        """
        Retrieve a cached response.

        Returns:
            Cached string, or ``None`` if not found.
        """
        if not self._enabled or self._cache is None:
            return None
        key = self._make_key(model, system, user)
        return self._cache.get(key)  # type: ignore[no-any-return]

    def set(self, model: str, system: str, user: str, response: str) -> None:
        """
        Store a response in the cache.

        Args:
            model: Model identifier.
            system: System prompt.
            user: User prompt.
            response: LLM response to cache.
        """
        if not self._enabled or self._cache is None:
            return
        key = self._make_key(model, system, user)
        self._cache.set(key, response, expire=60 * 60 * 24 * 7)  # 7 days

    def clear(self) -> None:
        """Wipe all cached entries."""
        if self._cache is not None:
            self._cache.clear()

    def close(self) -> None:
        """Close the cache handle."""
        if self._cache is not None:
            self._cache.close()


_cache_instance: LLMCache | None = None


def get_cache() -> LLMCache:
    """Return the global ``LLMCache`` singleton."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = LLMCache()
    return _cache_instance
