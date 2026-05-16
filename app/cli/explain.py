"""
``aicodereviewer explain <file>`` — plain-English code explanation.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import typer

from app.formatter.rich_output import (
    make_spinner,
    print_banner,
    print_error,
    print_success,
)
from app.formatter.review_renderer import render_review
from app.llm.factory import get_llm_provider
from app.prompts.explain_prompts import build_explain_prompt
from app.utils.file_utils import detect_language, read_file_safe

app = typer.Typer()


@app.command()
def explain(
    file: str = typer.Argument(..., help="Path to the source file to explain."),
    max_chars: int = typer.Option(20_000, "--max-chars", help="Max characters to read from file."),
) -> None:
    """
    💡 Get a plain-English explanation of any source file.

    Explains what the file does, its architecture, code flow,
    key functions, and things to be aware of.
    """
    print_banner()
    asyncio.run(_explain_async(file, max_chars))


async def _explain_async(file: str, max_chars: int) -> None:
    file_path = Path(file)
    if not file_path.exists():
        print_error(f"File not found: {file}")
        raise typer.Exit(1)

    code = read_file_safe(file_path, max_chars=max_chars)
    if not code.strip():
        print_error("File is empty.")
        raise typer.Exit(1)

    language = detect_language(file_path.name).capitalize()
    system_prompt, user_prompt = build_explain_prompt(
        code=code,
        filename=file,
        language=language,
    )

    llm = get_llm_provider()

    with make_spinner(f"Explaining {file_path.name}…") as progress:
        task = progress.add_task("explain")
        response = await llm.complete(system_prompt, user_prompt, temperature=0.2)
        progress.advance(task)

    render_review(response, title=f"💡 Explanation — {file_path.name}")
    print_success("Explanation complete.")
