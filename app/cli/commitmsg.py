"""
``aicodereviewer commitmsg`` — semantic commit message generator.
"""

from __future__ import annotations

import asyncio

import typer

from app.formatter.rich_output import (
    console,
    make_spinner,
    print_banner,
    print_error,
    print_info,
    print_success,
)
from app.git.diff_reader import read_staged_diff
from app.llm.factory import get_llm_provider
from app.prompts.commit_prompts import build_commit_prompt
from app.utils.file_utils import truncate_text
from app.config.settings import get_settings
from rich.panel import Panel
from rich import box

app = typer.Typer()


@app.command()
def commitmsg(
    repo: str = typer.Option(".", "--repo", "-r", help="Repository path."),
    copy: bool = typer.Option(False, "--copy", help="Copy the minimal commit to clipboard."),
) -> None:
    """
    💬 Generate semantic commit messages from staged changes.

    Produces three versions: minimal one-liner, standard with body,
    and detailed with changelog bullets.
    """
    print_banner()
    asyncio.run(_commitmsg_async(repo, copy))


async def _commitmsg_async(repo: str, copy: bool) -> None:
    settings = get_settings()

    try:
        diff_result = read_staged_diff(repo)
    except Exception as exc:
        print_error(f"Failed to read staged diff: {exc}")
        raise typer.Exit(1)

    if not diff_result.files:
        print_info("No staged changes. Use `git add` first.")
        raise typer.Exit(0)

    diff = truncate_text(diff_result.full_patch, settings.max_diff_lines)
    repo_name = diff_result.repo_root.split("\\")[-1].split("/")[-1]

    system_prompt, user_prompt = build_commit_prompt(
        diff=diff,
        repo_name=repo_name,
        branch=diff_result.branch,
        file_count=len(diff_result.files),
    )

    llm = get_llm_provider()

    with make_spinner("Generating commit messages…") as progress:
        task = progress.add_task("commit")
        response = await llm.complete(system_prompt, user_prompt, temperature=0.3)
        progress.advance(task)

    # Display in a styled panel
    console.print(
        Panel(
            __import__("rich.markdown", fromlist=["Markdown"]).Markdown(response),
            title="[bold bright_white]💬 Commit Messages[/bold bright_white]",
            border_style="bright_green",
            padding=(1, 2),
            box=box.ROUNDED,
        )
    )

    # Optionally copy minimal commit to clipboard
    if copy:
        minimal = _extract_minimal(response)
        if minimal:
            try:
                import subprocess
                subprocess.run(["clip"], input=minimal.encode(), check=True, capture_output=True)
                print_success("Minimal commit message copied to clipboard.")
            except Exception:
                print_info(f"Copy manually: {minimal}")

    print_success("Commit message generation complete.")


def _extract_minimal(response: str) -> str:
    """Pull the first non-empty, non-header line as the minimal commit."""
    for line in response.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and not stripped.startswith("**") and not stripped.startswith("---"):
            return stripped
    return ""
