"""
CLI integration tests using Typer's test runner.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from typer.testing import CliRunner

from app.main import app

runner = CliRunner(mix_stderr=False)


class TestCLIHelp:
    def test_help_exits_zero(self) -> None:
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "review" in result.output

    def test_version_flag(self) -> None:
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "1.0.0" in result.output

    def test_review_help(self) -> None:
        result = runner.invoke(app, ["review", "--help"])
        assert result.exit_code == 0

    def test_security_help(self) -> None:
        result = runner.invoke(app, ["security", "--help"])
        assert result.exit_code == 0

    def test_testgen_help(self) -> None:
        result = runner.invoke(app, ["testgen", "--help"])
        assert result.exit_code == 0

    def test_commitmsg_help(self) -> None:
        result = runner.invoke(app, ["commitmsg", "--help"])
        assert result.exit_code == 0

    def test_explain_help(self) -> None:
        result = runner.invoke(app, ["explain", "--help"])
        assert result.exit_code == 0

    def test_chat_help(self) -> None:
        result = runner.invoke(app, ["chat", "--help"])
        assert result.exit_code == 0

    def test_index_help(self) -> None:
        result = runner.invoke(app, ["index", "--help"])
        assert result.exit_code == 0


class TestExplainCommand:
    def test_explain_missing_file_exits_nonzero(self) -> None:
        result = runner.invoke(app, ["explain", "nonexistent_file_xyz.py"])
        assert result.exit_code != 0

    def test_explain_real_file(self, tmp_path) -> None:
        src = tmp_path / "example.py"
        src.write_text("def add(a, b):\n    return a + b\n")

        mock_llm = MagicMock()
        mock_llm.complete = AsyncMock(return_value="## What This File Does\nAdds two numbers.")

        with patch("app.cli.explain.get_llm_provider", return_value=mock_llm):
            result = runner.invoke(app, ["explain", str(src)])

        assert result.exit_code == 0


class TestTestgenCommand:
    def test_testgen_real_file(self, tmp_path) -> None:
        src = tmp_path / "calc.py"
        src.write_text("def multiply(a, b):\n    return a * b\n")

        mock_llm = MagicMock()
        mock_llm.complete = AsyncMock(
            return_value="def test_multiply():\n    assert multiply(2, 3) == 6\n"
        )

        with patch("app.cli.testgen.get_llm_provider", return_value=mock_llm):
            result = runner.invoke(app, ["testgen", str(src)])

        assert result.exit_code == 0

    def test_testgen_saves_output(self, tmp_path) -> None:
        src = tmp_path / "calc.py"
        src.write_text("def add(a, b): return a + b")
        out = tmp_path / "test_calc.py"

        mock_llm = MagicMock()
        mock_llm.complete = AsyncMock(return_value="def test_add():\n    assert add(1, 2) == 3\n")

        with patch("app.cli.testgen.get_llm_provider", return_value=mock_llm):
            result = runner.invoke(app, ["testgen", str(src), "--output", str(out)])

        assert result.exit_code == 0
        assert out.exists()
