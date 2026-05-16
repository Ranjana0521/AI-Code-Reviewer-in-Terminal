"""
AI Code Reviewer — main CLI entrypoint.

Registers all sub-commands under the ``aicodereviewer`` binary defined
in ``pyproject.toml`` → ``[project.scripts]``.
"""

from __future__ import annotations

import typer

from app.cli.review import review as review_cmd
from app.cli.security import security as security_cmd
from app.cli.testgen import testgen as testgen_cmd
from app.cli.commitmsg import commitmsg as commitmsg_cmd
from app.cli.explain import explain as explain_cmd
from app.cli.chat import chat as chat_cmd
from app.cli.index_repo import index_repo as index_cmd
from app import __version__

# ── Root Typer app ────────────────────────────────────────────────────────────
app = typer.Typer(
    name="aicodereviewer",
    help=(
        "[bold magenta]AI Code Reviewer[/bold magenta] — "
        "LLM-powered code review, security audits, test generation, "
        "commit messages, and more.\n\n"
        "Set [bold]OPENAI_API_KEY[/bold] in your environment or .env file."
    ),
    rich_markup_mode="rich",
    no_args_is_help=True,
    add_completion=True,
)


# ── Register sub-commands ─────────────────────────────────────────────────────
app.command(name="review",    help="📋 Review git diff with AI.")(review_cmd)
app.command(name="security",  help="🔒 Run a dedicated security audit.")(security_cmd)
app.command(name="testgen",   help="🧪 Generate pytest unit tests.")(testgen_cmd)
app.command(name="commitmsg", help="💬 Generate semantic commit messages.")(commitmsg_cmd)
app.command(name="explain",   help="💡 Explain a source file in plain English.")(explain_cmd)
app.command(name="chat",      help="🗨️  Start interactive AI chat.")(chat_cmd)
app.command(name="index",     help="📚 Index repo into RAG vector store.")(index_cmd)


# ── Version flag ──────────────────────────────────────────────────────────────
def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"aicodereviewer v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """AI Code Reviewer — terminal-first AI developer assistant."""


if __name__ == "__main__":
    app()
