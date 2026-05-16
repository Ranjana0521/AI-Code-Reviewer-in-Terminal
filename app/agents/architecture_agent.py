"""Architecture-focused review agent."""

from __future__ import annotations

from app.agents.base_agent import AgentResult, BaseReviewAgent

_SYSTEM = """\
You are a software architect with 15 years of experience.
Analyse the provided code diff for architectural and design issues ONLY.
Focus on: SOLID violations, tight coupling, missing abstractions,
god classes/functions, circular dependencies, incorrect layer separation,
missing interfaces, inappropriate design patterns, scalability concerns.

Format each finding as:
### [SEVERITY] Title
- **Principle violated**: e.g., SRP, OCP, DIP
- **Location**: file and approx area
- **Refactoring**: concrete architectural suggestion

Severities: HIGH | MEDIUM | LOW | INFO
If no issues, write: "✅ Architecture looks clean and well-structured."
"""


class ArchitectureAgent(BaseReviewAgent):
    """Specialised agent for architectural and design pattern review."""

    name = "Architecture Agent"

    async def analyze(self, code: str, context: str = "") -> AgentResult:
        user = f"Analyse this code diff for architectural issues:\n\n{code}"
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
