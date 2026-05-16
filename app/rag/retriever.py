"""
Semantic retriever for the RAG pipeline.

Combines the embedder and vector store into a single high-level API
that answers "what code in this repo is relevant to this query?".
"""

from __future__ import annotations

from typing import Any

from app.rag.embedder import embed_query
from app.rag.vector_store import VectorStore


class Retriever:
    """
    Retrieve the most relevant code chunks for a query.

    Usage::

        retriever = Retriever()
        results = await retriever.retrieve("how is authentication handled?")
        context = retriever.format_context(results)
    """

    def __init__(self) -> None:
        self._store = VectorStore()

    async def retrieve(
        self,
        query: str,
        n_results: int = 5,
        language_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Find the top-N most relevant code chunks.

        Args:
            query: Natural language or code query.
            n_results: Number of results to return.
            language_filter: Optionally restrict to a specific language.

        Returns:
            List of result dicts (id, document, metadata, distance).
        """
        if self._store.count() == 0:
            return []

        query_vec = await embed_query(query)
        where = {"language": language_filter} if language_filter else None
        return self._store.search(query_vec, n_results=n_results, where=where)

    def format_context(
        self,
        results: list[dict[str, Any]],
        max_chars: int = 4000,
    ) -> str:
        """
        Format retrieved chunks into an LLM-ready context string.

        Args:
            results: Output from ``retrieve()``.
            max_chars: Maximum total characters in context.

        Returns:
            Formatted context block.
        """
        parts: list[str] = []
        total = 0

        for r in results:
            meta = r.get("metadata", {})
            filepath = meta.get("filepath", "unknown")
            start = meta.get("start_line", "?")
            end = meta.get("end_line", "?")
            lang = meta.get("language", "text")
            doc = r.get("document", "")

            snippet = (
                f"### {filepath} (lines {start}–{end}, {lang})\n"
                f"```{lang}\n{doc}\n```\n"
            )
            if total + len(snippet) > max_chars:
                break
            parts.append(snippet)
            total += len(snippet)

        return "\n".join(parts) if parts else "No relevant context found in repository."
