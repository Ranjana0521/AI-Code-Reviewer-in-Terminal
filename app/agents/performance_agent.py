"""Performance-focused review agent."""

from __future__ import annotations

from app.agents.base_agent import AgentResult, BaseReviewAgent

_SYSTEM = """\
You are a performance engineering expert.
Analyse the provided code diff for performance issues ONLY.
Focus on: N+1 queries, unnecessary loops, blocking I/O in async code,
missing pagination, inefficient data structures, redundant computations,
memory leaks, missing caching opportunities.

Format each finding as:
### [SEVERITY] Title
- **Impact**: expected latency/memory effect
- **Location**: file and approx line
- **Fix**: concrete optimisation

Severities: HIGH | MEDIUM | LOW | INFO
If no issues found, write: "✅ No performance issues detected."
"""


class PerformanceAgent(BaseReviewAgent):
    """Specialised agent for performance bottleneck detection."""

    name = "Performance Agent"

    async def analyze(self, code: str, context: str = "") -> AgentResult:
        user = f"Analyse this code diff for performance issues:\n\n{code}"
        if context:
            user += f"\n\nRepository context:\n{context}"

        findings = await self._call_llm(_SYSTEM, user)
        severity = _infer_severity(findings)

        return AgentResult(
            agent_name=self.name,
            findings=findings,
            severity=severity,
            token_estimate=self._estimate_tokens(code + findings),
        )


def _infer_severity(text: str) -> str:
    tl = text.lower()
    for level in ("high", "medium", "low"):
        if level in tl:
            return level
    return "pass"
