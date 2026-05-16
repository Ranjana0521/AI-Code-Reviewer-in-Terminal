"""
``aicodereviewer review`` — full git diff code review command.
"""

from __future__ import annotations

import asyncio

import typer

from app.config.settings import get_settings
from app.formatter.rich_output import (
    console,
    make_spinner,
    print_banner,
    print_diff_stats,
    print_error,
    print_info,
    print_success,
)
from app.formatter.review_renderer import render_review
from app.git.diff_reader import read_staged_diff, read_unstaged_diff
from app.llm.factory import get_llm_provider
from app.observability.tracer import get_tracer
from app.prompts.review_prompts import build_review_prompt
from app.utils.cache import get_cache
from app.utils.file_utils import truncate_text

app = typer.Typer()


@app.command()
def review(
    staged: bool = typer.Option(True, "--staged/--unstaged", help="Review staged or unstaged changes."),
    base: str = typer.Option("", "--base", help="Base git ref for range diff (e.g. HEAD~1)."),
    head: str = typer.Option("HEAD", "--head", help="Head git ref for range diff."),
    repo: str = typer.Option(".", "--repo", "-r", help="Path to the git repository."),
    use_agents: bool = typer.Option(False, "--agents", help="Run multi-agent review workflow."),
    no_cache: bool = typer.Option(False, "--no-cache", help="Bypass the response cache."),
) -> None:
    """
    📋 Review staged or unstaged git changes using AI.

    Reads the current git diff, sends it to the configured LLM, and
    produces a structured review covering bugs, security, performance,
    readability, architecture, and best practices.
    """
    print_banner()
    asyncio.run(_review_async(staged, base, head, repo, use_agents, no_cache))


async def _review_async(
    staged: bool,
    base: str,
    head: str,
    repo: str,
    use_agents: bool,
    no_cache: bool,
) -> None:
    settings = get_settings()
    tracer = get_tracer()
    cache = get_cache()

    # ── Read diff ────────────────────────────────────────────────────────────
    try:
        if base:
            from app.git.diff_reader import read_diff_between
            diff_result = read_diff_between(repo, base, head)
        elif staged:
            diff_result = read_staged_diff(repo)
        else:
            diff_result = read_unstaged_diff(repo)
    except Exception as exc:
        print_error(f"Failed to read git diff: {exc}")
        raise typer.Exit(1)

    if not diff_result.files:
        print_info("No changes detected. Stage some files first with `git add`.")
        raise typer.Exit(0)

    # ── Show diff summary ────────────────────────────────────────────────────
    console.print(
        f"\n[bold cyan]Repository:[/] {diff_result.repo_root}"
        f"  [bold cyan]Branch:[/] {diff_result.branch}"
        f"  [bold cyan]Commit:[/] {diff_result.commit_hash}\n"
    )
    print_diff_stats(
        [
            {
                "filename": f.filename,
                "change_type": f.change_type,
                "additions": f.additions,
                "deletions": f.deletions,
            }
            for f in diff_result.files
        ]
    )
    console.print()

    # ── Truncate diff ─────────────────────────────────────────────────────────
    full_diff = truncate_text(diff_result.full_patch, settings.max_diff_lines)

    if use_agents:
        await _run_multi_agent(full_diff)
        return

    # ── Standard single-pass review ───────────────────────────────────────────
    system_prompt, user_prompt = build_review_prompt(
        diff=full_diff,
        repo_name=diff_result.repo_root.split("\\")[-1].split("/")[-1],
        branch=diff_result.branch,
        commit_hash=diff_result.commit_hash,
        file_count=len(diff_result.files),
        total_additions=diff_result.total_additions,
        total_deletions=diff_result.total_deletions,
    )

    # Check cache
    llm = get_llm_provider()
    if not no_cache:
        cached = cache.get(llm.model_name, system_prompt, user_prompt)
        if cached:
            print_info("(Loaded from cache — use --no-cache to force refresh)")
            render_review(cached, title="AI Code Review")
            return

    # Call LLM
    with tracer.trace("review", input=user_prompt[:500]):
        with make_spinner("Reviewing your code with AI…") as progress:
            task = progress.add_task("review")

            if settings.stream_responses:
                response_parts: list[str] = []
                progress.stop()
                console.print()
                async for chunk in llm.stream(system_prompt, user_prompt):
                    console.print(chunk, end="", markup=False)
                    response_parts.append(chunk)
                console.print("\n")
                response = "".join(response_parts)
            else:
                response = await llm.complete(system_prompt, user_prompt)
                progress.advance(task)

    if not settings.stream_responses:
        render_review(response, title="AI Code Review")

    if not no_cache:
        cache.set(llm.model_name, system_prompt, user_prompt, response)

    print_success("Review complete.")


async def _run_multi_agent(diff: str) -> None:
    """Run the multi-agent orchestrator."""
    from app.agents.orchestrator import MultiAgentOrchestrator
    from app.formatter.review_renderer import render_review
    from rich.panel import Panel
    from rich import box

    orchestrator = MultiAgentOrchestrator()

    with make_spinner("Running 5 specialised AI agents in parallel…") as progress:
        task = progress.add_task("agents")
        report = await orchestrator.run(diff)
        progress.advance(task)

    # Render individual agent results
    for result in report.results:
        render_review(result.findings, title=result.agent_name)

    # Render consolidated executive summary
    console.print(
        Panel(
            __import__("rich.markdown", fromlist=["Markdown"]).Markdown(report.final_report),
            title="[bold bright_white]🎯 Executive Summary[/bold bright_white]",
            border_style="bright_white",
            box=box.DOUBLE_EDGE,
            padding=(1, 2),
        )
    )
    print_success(f"Multi-agent review complete. Overall risk: {report.highest_severity.upper()}")
