"""
Observability tracer using Langfuse.

Wraps Langfuse SDK calls in a safe no-op layer so the app works even
when tracing is disabled or credentials are missing.
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Any, Generator

from app.config.settings import get_settings


class _NoOpSpan:
    """Silent stand-in when Langfuse is disabled."""

    def update(self, **kwargs: Any) -> None:  # noqa: D102
        pass

    def end(self, **kwargs: Any) -> None:  # noqa: D102
        pass


class _NoOpTrace:
    """Silent stand-in trace when Langfuse is disabled."""

    def span(self, **kwargs: Any) -> _NoOpSpan:  # noqa: D102
        return _NoOpSpan()

    def generation(self, **kwargs: Any) -> _NoOpSpan:  # noqa: D102
        return _NoOpSpan()

    def update(self, **kwargs: Any) -> None:  # noqa: D102
        pass

    def end(self, **kwargs: Any) -> None:  # noqa: D102
        pass


class Tracer:
    """
    Thin wrapper around Langfuse for prompt / token / latency tracing.

    Usage::

        tracer = Tracer()
        with tracer.trace("review", input=diff) as span:
            result = await llm.complete(...)
            span.update(output=result, usage={"tokens": 1000})
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        self._client: Any = None
        self._enabled = False

        if self._settings.langfuse_enabled:
            try:
                from langfuse import Langfuse  # type: ignore[import-untyped]

                self._client = Langfuse(
                    public_key=self._settings.langfuse_public_key,
                    secret_key=self._settings.langfuse_secret_key,
                    host=self._settings.langfuse_host,
                )
                self._enabled = True
            except Exception:
                # Graceful degradation — tracing unavailable
                self._enabled = False

    @property
    def enabled(self) -> bool:
        """Whether Langfuse tracing is active."""
        return self._enabled

    @contextmanager
    def trace(
        self,
        name: str,
        *,
        input: Any = None,
        metadata: dict[str, Any] | None = None,
    ) -> Generator[Any, None, None]:
        """
        Context manager that creates a Langfuse trace.

        Args:
            name: Human-readable operation name.
            input: The input payload to log.
            metadata: Extra metadata dict to attach.

        Yields:
            A Langfuse trace object (or no-op if disabled).
        """
        if not self._enabled:
            yield _NoOpTrace()
            return

        trace = self._client.trace(
            name=name,
            input=input,
            metadata=metadata or {},
        )
        start = time.perf_counter()
        try:
            yield trace
        finally:
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            trace.update(metadata={"latency_ms": elapsed_ms})
            trace.end()

    def log_generation(
        self,
        trace: Any,
        *,
        name: str,
        model: str,
        prompt: str,
        completion: str,
        usage: dict[str, int] | None = None,
    ) -> None:
        """
        Log an LLM generation inside an existing trace.

        Args:
            trace: Active Langfuse trace object.
            name: Generation step name.
            model: Model identifier string.
            prompt: The prompt sent to the model.
            completion: The model's response.
            usage: Token usage dict (``prompt_tokens``, ``completion_tokens``).
        """
        if not self._enabled:
            return

        gen = trace.generation(
            name=name,
            model=model,
            input=prompt,
            output=completion,
            usage=usage,
        )
        gen.end()

    def flush(self) -> None:
        """Flush all pending Langfuse events (call before process exit)."""
        if self._enabled and self._client:
            try:
                self._client.flush()
            except Exception:
                pass


# Module-level singleton
_tracer: Tracer | None = None


def get_tracer() -> Tracer:
    """Return the global ``Tracer`` singleton."""
    global _tracer
    if _tracer is None:
        _tracer = Tracer()
    return _tracer
