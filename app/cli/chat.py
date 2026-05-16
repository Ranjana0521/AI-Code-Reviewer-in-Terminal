"""
``aicodereviewer chat`` — interactive AI chat about your codebase.
"""

from __future__ import annotations

import asyncio

import typer
from rich.prompt import Prompt

from app.formatter.rich_output import (
    console,
    print_banner,
    print_info,
    print_success,
    print_warning,
)
from app.llm.factory import get_llm_provider
from app.rag.retriever import Retriever

app = typer.Typer()

_SYSTEM = """\
You are an expert AI code assistant with deep knowledge of this repository.
Answer questions clearly, referencing specific files and functions when relevant.
If provided with repository context, use it to give accurate, grounded answers.
Keep responses concise but complete. Use Markdown for code blocks.
"""


@app.command()
def chat(
    repo: str = typer.Option(".", "--repo", "-r", help="Repository path for RAG context."),
    no_rag: bool = typer.Option(False, "--no-rag", help="Disable RAG context retrieval."),
) -> None:
    """
    💬 Start an interactive AI chat session about your codebase.

    Ask questions about code, architecture, bugs, or anything else.
    Type 'exit' or 'quit' to end the session. Ctrl+C also works.
    """
    print_banner()
    asyncio.run(_chat_async(repo, no_rag))


async def _chat_async(repo: str, no_rag: bool) -> None:
    llm = get_llm_provider()
    retriever = Retriever() if not no_rag else None

    console.print(
        "\n[bold magenta]🤖 AI Chat Mode[/bold magenta]  "
        "[dim]Type your question. 'exit' to quit.[/dim]\n"
    )

    history: list[dict[str, str]] = []

    while True:
        try:
            user_input = Prompt.ask("[bold cyan]You[/bold cyan]")
        except (EOFError, KeyboardInterrupt):
            break

        if user_input.strip().lower() in {"exit", "quit", "q", ":q"}:
            break

        if not user_input.strip():
            continue

        # Retrieve RAG context
        context = ""
        if retriever:
            try:
                results = await retriever.retrieve(user_input, n_results=4)
                context = retriever.format_context(results, max_chars=2500)
            except Exception:
                pass

        # Build prompt with history + context
        history_text = "\n".join(
            f"{m['role'].capitalize()}: {m['content']}" for m in history[-6:]
        )
        user_prompt = user_input
        if context and context != "No relevant context found in repository.":
            user_prompt = f"Repository context:\n{context}\n\n---\n\nUser question: {user_input}"
        if history_text:
            user_prompt = f"Conversation so far:\n{history_text}\n\n{user_prompt}"

        # Stream response
        console.print("\n[bold green]AI[/bold green]: ", end="")
        response_parts: list[str] = []
        try:
            async for chunk in llm.stream(_SYSTEM, user_prompt):
                console.print(chunk, end="", markup=False)
                response_parts.append(chunk)
        except Exception as exc:
            console.print(f"\n[red]Error: {exc}[/red]")
            continue

        response = "".join(response_parts)
        console.print("\n")

        # Update history
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": response})

    print_success("Chat session ended. Goodbye! 👋")
