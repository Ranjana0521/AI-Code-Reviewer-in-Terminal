"""
Tests for the multi-agent system.
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.agents.base_agent import AgentResult, BaseReviewAgent
from app.agents.security_agent import SecurityAgent, _infer_severity as sec_severity
from app.agents.performance_agent import PerformanceAgent
from app.agents.readability_agent import ReadabilityAgent
from app.agents.architecture_agent import ArchitectureAgent
from app.agents.testcoverage_agent import TestCoverageAgent


# ── AgentResult dataclass ─────────────────────────────────────────────────────

class TestAgentResult:
    def test_agent_result_defaults(self) -> None:
        """AgentResult should have sensible defaults."""
        result = AgentResult(
            agent_name="Test",
            findings="some findings",
            severity="medium",
        )
        assert result.token_estimate == 0
        assert result.error is None

    def test_agent_result_with_error(self) -> None:
        """AgentResult captures error field."""
        result = AgentResult(
            agent_name="Test",
            findings="",
            severity="pass",
            error="timeout",
        )
        assert result.error == "timeout"


# ── Severity inference ────────────────────────────────────────────────────────

class TestSeverityInference:
    @pytest.mark.parametrize("text,expected", [
        ("found CRITICAL vulnerability", "critical"),
        ("This is HIGH risk", "high"),
        ("medium concern here", "medium"),
        ("LOW impact issue", "low"),
        ("No issues found", "pass"),
        ("", "pass"),
    ])
    def test_security_infer_severity(self, text: str, expected: str) -> None:
        """Severity inference returns highest matching level."""
        assert sec_severity(text) == expected


# ── Individual agents ─────────────────────────────────────────────────────────

def _make_mock_llm(response: str) -> MagicMock:
    """Create a mock LLM provider that returns a fixed response."""
    llm = MagicMock()
    llm.complete = AsyncMock(return_value=response)
    return llm


class TestSecurityAgent:
    @pytest.mark.asyncio
    async def test_analyze_returns_agent_result(self) -> None:
        """SecurityAgent.analyze returns a properly typed AgentResult."""
        llm = _make_mock_llm("### [HIGH] SQL Injection\n- Risk: bad\n- Fix: use params")
        agent = SecurityAgent(llm)
        result = await agent.analyze("SELECT * FROM users WHERE id = " + "input")
        assert isinstance(result, AgentResult)
        assert result.agent_name == "Security Agent"
        assert result.severity in {"critical", "high", "medium", "low", "pass"}

    @pytest.mark.asyncio
    async def test_analyze_no_issues(self) -> None:
        """SecurityAgent returns 'pass' severity when no issues found."""
        llm = _make_mock_llm("✅ No security issues detected.")
        agent = SecurityAgent(llm)
        result = await agent.analyze("x = 1")
        assert result.severity == "pass"

    @pytest.mark.asyncio
    async def test_analyze_with_context(self) -> None:
        """SecurityAgent appends context to the user prompt."""
        llm = _make_mock_llm("✅ No security issues detected.")
        agent = SecurityAgent(llm)
        result = await agent.analyze("code", context="some rag context")
        assert result.agent_name == "Security Agent"
        # Context should cause the LLM to be called
        llm.complete.assert_called_once()
        call_args = llm.complete.call_args
        assert "some rag context" in call_args[0][1]


class TestPerformanceAgent:
    @pytest.mark.asyncio
    async def test_analyze_returns_result(self) -> None:
        llm = _make_mock_llm("### [HIGH] N+1 Query\n- Impact: slow\n- Fix: batch")
        agent = PerformanceAgent(llm)
        result = await agent.analyze("for item in items: db.query(item)")
        assert result.agent_name == "Performance Agent"
        assert result.severity == "high"


class TestReadabilityAgent:
    @pytest.mark.asyncio
    async def test_analyze_clean_code(self) -> None:
        llm = _make_mock_llm("✅ Code readability is excellent.")
        agent = ReadabilityAgent(llm)
        result = await agent.analyze("def greet(name: str) -> str:\n    return f'Hello {name}'")
        assert result.severity == "pass"


class TestArchitectureAgent:
    @pytest.mark.asyncio
    async def test_analyze_returns_result(self) -> None:
        llm = _make_mock_llm("### [MEDIUM] God Class\n- Principle: SRP\n- Fix: split")
        agent = ArchitectureAgent(llm)
        result = await agent.analyze("class God: pass")
        assert result.agent_name == "Architecture Agent"


class TestTestCoverageAgent:
    @pytest.mark.asyncio
    async def test_analyze_identifies_missing_tests(self) -> None:
        llm = _make_mock_llm("### [HIGH] Missing Test\n- What: auth function\n- Fix: add test")
        agent = TestCoverageAgent(llm)
        result = await agent.analyze("def authenticate(user, pwd): pass")
        assert result.severity == "high"


# ── Orchestrator ──────────────────────────────────────────────────────────────

class TestOrchestrator:
    @pytest.mark.asyncio
    async def test_run_returns_report(self) -> None:
        """Orchestrator.run returns OrchestratorReport with results."""
        from app.agents.orchestrator import MultiAgentOrchestrator, OrchestratorReport

        mock_result = AgentResult("Mock Agent", "No issues.", "pass")
        good_response = "## Executive Summary\nLooks good."

        with patch("app.agents.orchestrator.SecurityAgent") as MockSec, \
             patch("app.agents.orchestrator.PerformanceAgent") as MockPerf, \
             patch("app.agents.orchestrator.ReadabilityAgent") as MockRead, \
             patch("app.agents.orchestrator.ArchitectureAgent") as MockArch, \
             patch("app.agents.orchestrator.TestCoverageAgent") as MockTest, \
             patch("app.agents.orchestrator.get_llm_provider") as mock_factory, \
             patch("app.agents.orchestrator.get_tracer") as mock_tracer:

            for MockCls in (MockSec, MockPerf, MockRead, MockArch, MockTest):
                instance = MockCls.return_value
                instance.analyze = AsyncMock(return_value=mock_result)

            llm = MagicMock()
            llm.model_name = "gpt-4o"
            llm.complete = AsyncMock(return_value=good_response)
            mock_factory.return_value = llm

            tracer = MagicMock()
            tracer.enabled = False
            tracer.trace.return_value.__enter__ = MagicMock(return_value=MagicMock())
            tracer.trace.return_value.__exit__ = MagicMock(return_value=False)
            mock_tracer.return_value = tracer

            orchestrator = MultiAgentOrchestrator()
            report = await orchestrator.run("some code diff")

            assert isinstance(report, OrchestratorReport)
            assert report.final_report == good_response

    def test_highest_severity_ordering(self) -> None:
        """OrchestratorReport.highest_severity returns the most severe level."""
        from app.agents.orchestrator import OrchestratorReport

        report = OrchestratorReport(
            results=[
                AgentResult("A", "", "low"),
                AgentResult("B", "", "high"),
                AgentResult("C", "", "medium"),
            ]
        )
        assert report.highest_severity == "high"
