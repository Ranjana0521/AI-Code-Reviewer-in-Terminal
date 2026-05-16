"""
``aicodereviewer testgen`` — unit test generator command.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import typer

from app.formatter.rich_output import (
    console,
    make_spinner,
    print_banner,
    print_code,
    print_error,
    print_info,
    print_success,
)
from app.git.diff_reader import read_staged_diff
from app.llm.factory import get_llm_provider
from app.prompts.testgen_prompts import build_testgen_prompt
from app.utils.file_utils import detect_language, read_file_safe, truncate_text
from app.config.settings import get_settings

app = typer.Typer()


@app.command()
def testgen(
    file: str = typer.Argument("", help="Specific file to generate tests for (default: staged diff)."),
    output: str = typer.Option("", "--output", "-o", help="Save generated tests to this file."),
    repo: str = typer.Option(".", "--repo", "-r", help="Repository path."),
) -> None:
    """
    🧪 Generate pytest unit tests for your code changes or a specific file.

    Produces happy-path, edge-case, and error-path tests with mocks.
    """
    print_banner()
    asyncio.run(_testgen_async(file, output, repo))


async def _testgen_async(file: str, output: str, repo: str) -> None:
    settings = get_settings()

    if file:
        file_path = Path(file)
        if not file_path.exists():
            print_error(f"File not found: {file}")
            raise typer.Exit(1)
        code = read_file_safe(file_path, max_chars=20_000)
        filename = file
        language = detect_language(file).capitalize()
    else:
        try:
            diff_result = read_staged_diff(repo)
        except Exception as exc:
            print_error(f"Failed to read git diff: {exc}")
            raise typer.Exit(1)

        if not diff_result.files:
            print_info("No staged changes. Use `git add` first.")
            raise typer.Exit(0)

        # Use the first Python file changed, or the whole diff
        python_files = [f for f in diff_result.files if f.filename.endswith(".py")]
        if python_files:
            code = python_files[0].patch
            filename = python_files[0].filename
        else:
            code = truncate_text(diff_result.full_patch, 300)
            filename = "diff"
        language = "Python"

    system_prompt, user_prompt = build_testgen_prompt(
        code=code,
        filename=filename,
        language=language,
    )

    llm = get_llm_provider()
    print_info(f"Generating tests for: [bold]{filename}[/bold]")

    with make_spinner("Generating unit tests with AI…") as progress:
        task = progress.add_task("testgen")
        response = await llm.complete(system_prompt, user_prompt, temperature=0.15)
        progress.advance(task)

    # Strip markdown fences if present
    clean = _strip_fences(response)

    print_code(clean, language="python", title=f"Generated Tests — {filename}")

    if output:
        out_path = Path(output)
        out_path.write_text(clean, encoding="utf-8")
        print_success(f"Tests saved to: {output}")
    else:
        console.print("[dim]Tip: use --output tests/test_<name>.py to save.[/dim]")

    print_success("Test generation complete.")


def _strip_fences(text: str) -> str:
    """Remove ```python ... ``` code fences from LLM output."""
    lines = text.splitlines()
    if lines and lines[0].strip().startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines)
