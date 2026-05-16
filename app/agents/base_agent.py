"""
Base agent class for the multi-agent review system.

All specialised review agents inherit from ``BaseReviewAgent`` and
implement the ``analyze`` coroutine.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.llm.base import BaseLLMProvider


@dataclass
class AgentResult:
    """Structured output returned by every agent."""

    agent_name: str
    findings: str               # Markdown-formatted findings
    severity: str               # overall: critical | high | medium | low | pass
    token_estimate: int = 0     # rough tokens used (for observability)
    error: str | None = None    # set if the agent failed


class BaseReviewAgent(ABC):
    """
    Abstract base for all specialised review agents.

    Concrete agents receive a code diff/snippet and return an
    ``AgentResult`` with their specialised analysis.
    """

    #: Override in subclasses — used in result labels and logs
    name: str = "BaseAgent"

    def __init__(self, llm: BaseLLMProvider) -> None:
        self._llm = llm

    @abstractmethod
    async def analyze(self, code: str, context: str = "") -> AgentResult:
        """
        Analyse code and return structured findings.

        Args:
            code: Diff or source code to review.
            context: Optional RAG context snippets.

        Returns:
            ``AgentResult`` with findings and overall severity.
        """

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimate: ~4 chars per token."""
        return len(text) // 4

    async def _call_llm(
        self, system: str, user: str, *, temperature: float = 0.1
    ) -> str:
        """
        Call the LLM with error handling.

        Returns:
            LLM response string, or error message.
        """
        try:
            return await self._llm.complete(
                system, user, temperature=temperature, max_tokens=2048
            )
        except Exception as exc:
            return f"[Agent error: {exc}]"
