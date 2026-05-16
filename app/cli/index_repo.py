"""
``aicodereviewer index`` — index the repository into the RAG vector store.
"""

from __future__ import annotations

import asyncio

import typer
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn, SpinnerColumn

from app.formatter.rich_output import console, print_banner, print_error, print_info, print_success
from app.rag.chunker import chunk_repository
from app.rag.embedder import embed_chunks
from app.rag.vector_store import VectorStore
from app.config.settings import get_settings

app = typer.Typer()

_BATCH = 50  # chunks per embedding batch for display


@app.command()
def index_repo(
    repo: str = typer.Option(".", "--repo", "-r", help="Repository path to index."),
    clear: bool = typer.Option(False, "--clear", help="Clear existing index before indexing."),
    chunk_size: int = typer.Option(60, "--chunk-size", help="Lines per chunk."),
    overlap: int = typer.Option(10, "--overlap", help="Overlap lines between chunks."),
) -> None:
    """
    📚 Index the repository into the RAG vector store.

    Chunks all source files, generates embeddings, and stores them
    in ChromaDB for use by the chat and review commands.
    """
    print_banner()
    asyncio.run(_index_async(repo, clear, chunk_size, overlap))


async def _index_async(
    repo: str,
    clear: bool,
    chunk_size: int,
    overlap: int,
) -> None:
    settings = get_settings()
    store = VectorStore()

    if clear:
        print_info("Clearing existing index…")
        store.clear()

    # ── Chunk repository ──────────────────────────────────────────────────────
    print_info(f"Scanning repository: [bold]{repo}[/bold]")
    chunks = chunk_repository(repo, chunk_size=chunk_size, overlap=overlap)

    if not chunks:
        print_error("No source files found to index.")
        raise typer.Exit(1)

    print_info(f"Found [bold]{len(chunks)}[/bold] chunks across all source files.")

    # ── Embed in batches with progress bar ───────────────────────────────────
    with Progress(
        SpinnerColumn(style="magenta"),
        TextColumn("[bold cyan]{task.description}"),
        BarColumn(bar_width=40, style="magenta", complete_style="green"),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Embedding chunks…", total=len(chunks))

        for i in range(0, len(chunks), _BATCH):
            batch = chunks[i : i + _BATCH]
            embeddings = await embed_chunks(batch)
            store.upsert_chunks(batch, embeddings)
            progress.advance(task, len(batch))

    total = store.count()
    print_success(f"Index complete. [bold]{total}[/bold] chunks stored in ChromaDB.")
    console.print(f"[dim]Location: {settings.chroma_path}[/dim]")
