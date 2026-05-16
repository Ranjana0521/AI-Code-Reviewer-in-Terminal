"""
``aicodereviewer security`` — dedicated security audit command.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import typer

from app.formatter.rich_output import (
    console,
    make_spinner,
    print_banner,
    print_error,
    print_info,
    print_success,
)
from app.formatter.review_renderer import render_review
from app.git.diff_reader import read_staged_diff
from app.llm.factory import get_llm_provider
from app.prompts.security_prompts import build_security_prompt
from app.utils.file_utils import detect_language, read_file_safe, truncate_text
from app.config.settings import get_settings

app = typer.Typer()


@app.command()
def security(
    file: str = typer.Argument("", help="Specific file to audit (default: git diff)."),
    repo: str = typer.Option(".", "--repo", "-r", help="Repository path."),
) -> None:
    """
    🔒 Run a dedicated security audit on your code changes or a specific file.

    Detects SQL injection, hardcoded secrets, insecure auth, path traversal,
    unsafe deserialization, crypto weaknesses, and more.
    """
    print_banner()
    asyncio.run(_security_async(file, repo))


async def _security_async(file: str, repo: str) -> None:
    settings = get_settings()

    if file:
        # Audit a specific file
        file_path = Path(file)
        if not file_path.exists():
            print_error(f"File not found: {file}")
            raise typer.Exit(1)

        code = read_file_safe(file_path, max_chars=30_000)
        code = truncate_text(code, settings.max_diff_lines)
        language = detect_language(file)
        filenames = file
    else:
        # Audit staged diff
        try:
            diff_result = read_staged_diff(repo)
        except Exception as exc:
            print_error(f"Failed to read git diff: {exc}")
            raise typer.Exit(1)

        if not diff_result.files:
            print_info("No staged changes found. Use `git add` first.")
            raise typer.Exit(0)

        code = truncate_text(diff_result.full_patch, settings.max_diff_lines)
        filenames = ", ".join(f.filename for f in diff_result.files[:5])
        language = "mixed"

    system_prompt, user_prompt = build_security_prompt(
        code=code,
        filenames=filenames,
        language=language,
    )

    llm = get_llm_provider()

    with make_spinner("Running security audit…") as progress:
        task = progress.add_task("security")
        response = await llm.complete(system_prompt, user_prompt, temperature=0.1)
        progress.advance(task)

    render_review(response, title="🔒 Security Audit Report")
    print_success("Security audit complete.")
