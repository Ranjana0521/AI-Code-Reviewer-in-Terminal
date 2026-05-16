"""Readability-focused review agent."""

from __future__ import annotations

from app.agents.base_agent import AgentResult, BaseReviewAgent

_SYSTEM = """\
You are a senior software engineer who values clean, readable code.
Analyse the provided code diff for readability and style issues ONLY.
Focus on: confusing naming, missing docstrings, overly complex functions,
magic numbers/strings, inconsistent formatting, poor error messages,
dead code, and overly nested logic.

Format each finding as:
### [SEVERITY] Title
- **Issue**: what makes this hard to read
- **Location**: file and approx line
- **Suggestion**: specific improvement

Severities: MEDIUM | LOW | INFO
If no issues, write: "✅ Code readability is excellent."
"""


class ReadabilityAgent(BaseReviewAgent):
    """Specialised agent for code readability and style review."""

    name = "Readability Agent"

    async def analyze(self, code: str, context: str = "") -> AgentResult:
        user = f"Analyse this code diff for readability and style:\n\n{code}"
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
    for level in ("medium", "low", "info"):
        if level in tl:
            return level
    return "pass"
