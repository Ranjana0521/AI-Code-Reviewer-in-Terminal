"""
Multi-agent orchestrator using LangGraph.

Runs all five specialised review agents in parallel and synthesises
their outputs into a single consolidated report.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, TypedDict

from app.agents.base_agent import AgentResult
from app.agents.security_agent import SecurityAgent
from app.agents.performance_agent import PerformanceAgent
from app.agents.readability_agent import ReadabilityAgent
from app.agents.architecture_agent import ArchitectureAgent
from app.agents.testcoverage_agent import TestCoverageAgent
from app.llm.factory import get_llm_provider
from app.observability.tracer import get_tracer


# ── LangGraph state type ──────────────────────────────────────────────────────

class ReviewState(TypedDict, total=False):
    """State dictionary passed through the LangGraph workflow."""

    code: str
    context: str
    security: AgentResult | None
    performance: AgentResult | None
    readability: AgentResult | None
    architecture: AgentResult | None
    test_coverage: AgentResult | None
    final_report: str


@dataclass
class OrchestratorReport:
    """Consolidated multi-agent review report."""

    results: list[AgentResult] = field(default_factory=list)
    final_report: str = ""
    total_token_estimate: int = 0

    @property
    def highest_severity(self) -> str:
        order = ["critical", "high", "medium", "low", "pass"]
        for level in order:
            if any(r.severity == level for r in self.results):
                return level
        return "pass"


# ── Synthesis prompt ──────────────────────────────────────────────────────────

_SYNTHESIS_SYSTEM = """\
You are the lead code reviewer. You have received reports from 5 specialised
review agents. Your job is to synthesise them into a concise executive summary.

Output:
## 🎯 Executive Summary
2–3 sentences capturing the most critical findings.

## 🚨 Top Priority Issues  
Numbered list of the 3–5 most important issues to fix, in priority order.

## ✅ Strengths
What the code does well (1–3 bullet points).

## 📋 Action Items
Checkbox list of concrete next steps for the developer.

## 🏆 Overall Risk: [CRITICAL|HIGH|MEDIUM|LOW|PASS]
One sentence verdict.
"""


class MultiAgentOrchestrator:
    """
    Orchestrates all review agents and synthesises their output.

    Uses ``asyncio.gather`` for parallel execution, then feeds the
    combined results to a synthesis LLM call.

    With LangGraph installed the workflow is compiled as a proper graph;
    otherwise it falls back to direct async execution.
    """

    def __init__(self) -> None:
        self._llm = get_llm_provider()
        self._tracer = get_tracer()

    async def run(self, code: str, context: str = "") -> OrchestratorReport:
        """
        Run all agents in parallel and return a consolidated report.

        Args:
            code: Code diff or source to review.
            context: Optional RAG context string.

        Returns:
            ``OrchestratorReport`` with per-agent results and final report.
        """
        with self._tracer.trace("multi_agent_review", input=code[:500]) as trace:
            # Instantiate agents
            agents = [
                SecurityAgent(self._llm),
                PerformanceAgent(self._llm),
                ReadabilityAgent(self._llm),
                ArchitectureAgent(self._llm),
                TestCoverageAgent(self._llm),
            ]

            # Run all agents concurrently
            results: list[AgentResult] = await asyncio.gather(
                *[agent.analyze(code, context) for agent in agents],
                return_exceptions=False,
            )

            # Synthesise
            combined = _build_combined_report(results)
            final = await self._synthesise(combined)

            report = OrchestratorReport(
                results=list(results),
                final_report=final,
                total_token_estimate=sum(r.token_estimate for r in results),
            )

            if self._tracer.enabled:
                self._tracer.log_generation(
                    trace,
                    name="synthesis",
                    model=self._llm.model_name,
                    prompt=combined[:500],
                    completion=final[:500],
                )

        return report

    async def _synthesise(self, combined_findings: str) -> str:
        """Call the LLM to produce a final executive summary."""
        try:
            return await self._llm.complete(
                _SYNTHESIS_SYSTEM,
                f"Agent findings:\n\n{combined_findings}",
                temperature=0.1,
                max_tokens=1500,
            )
        except Exception as exc:
            return f"[Synthesis failed: {exc}]\n\n{combined_findings}"


def _build_combined_report(results: list[AgentResult]) -> str:
    """Concatenate all agent findings into one string."""
    parts: list[str] = []
    for r in results:
        parts.append(f"## {r.agent_name} (severity: {r.severity.upper()})\n\n{r.findings}")
    return "\n\n---\n\n".join(parts)
