"""Test coverage analysis agent."""

from __future__ import annotations

from app.agents.base_agent import AgentResult, BaseReviewAgent

_SYSTEM = """\
You are a QA engineer and testing expert.
Analyse the provided code diff for test coverage issues ONLY.
Focus on: missing unit tests for new code, missing edge case tests,
missing integration tests, missing mocks for external calls,
untested error paths, missing assertions, fragile tests.

Format each finding as:
### [SEVERITY] Missing Test
- **What's untested**: specific function/class/branch
- **Risk**: what bug could slip through
- **Suggested test**: brief outline of the test to write

Severities: HIGH | MEDIUM | LOW | INFO
If coverage looks adequate, write: "✅ Test coverage appears adequate."
"""


class TestCoverageAgent(BaseReviewAgent):
    """Specialised agent for test coverage gap analysis."""

    name = "Test Coverage Agent"

    async def analyze(self, code: str, context: str = "") -> AgentResult:
        user = f"Analyse this code diff for test coverage gaps:\n\n{code}"
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
