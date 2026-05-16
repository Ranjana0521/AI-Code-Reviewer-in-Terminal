"""Security-focused review agent."""

from __future__ import annotations

from app.agents.base_agent import AgentResult, BaseReviewAgent

_SYSTEM = """\
You are an elite application security engineer (AppSec).
Analyse the provided code diff for security vulnerabilities ONLY.
Focus on: SQL/command injection, hardcoded secrets, insecure auth,
unsafe deserialization, path traversal, SSRF, crypto weaknesses,
sensitive data exposure, and vulnerable patterns.

Format each finding as:
### [SEVERITY] Title
- **Risk**: ...
- **Location**: ...
- **Fix**: ...

Severities: CRITICAL | HIGH | MEDIUM | LOW | INFO
End with: **Security Score: X/10**
If no issues found, write: "✅ No security issues detected."
"""


class SecurityAgent(BaseReviewAgent):
    """Specialised agent for security vulnerability detection."""

    name = "Security Agent"

    async def analyze(self, code: str, context: str = "") -> AgentResult:
        user = f"Analyse this code diff for security vulnerabilities:\n\n{code}"
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
    for level in ("critical", "high", "medium", "low"):
        if level in tl:
            return level
    return "pass"
