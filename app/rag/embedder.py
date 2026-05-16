"""
Embedding pipeline for the RAG system.

Handles batched embedding of code chunks using the configured LLM provider.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from app.llm.factory import get_llm_provider
from app.rag.chunker import CodeChunk

if TYPE_CHECKING:
    pass

# Maximum texts per embedding API call
_BATCH_SIZE = 50


async def embed_chunks(chunks: list[CodeChunk]) -> list[list[float]]:
    """
    Generate embedding vectors for a list of code chunks.

    Sends requests in batches to respect API limits.

    Args:
        chunks: Code chunks to embed.

    Returns:
        List of float vectors in the same order as ``chunks``.
    """
    provider = get_llm_provider()
    texts = [c.content for c in chunks]
    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), _BATCH_SIZE):
        batch = texts[i : i + _BATCH_SIZE]
        vectors = await provider.embed(batch)
        all_embeddings.extend(vectors)

    return all_embeddings


async def embed_query(query: str) -> list[float]:
    """
    Embed a single query string for similarity search.

    Args:
        query: Natural language or code query.

    Returns:
        Embedding vector.
    """
    provider = get_llm_provider()
    results = await provider.embed([query])
    return results[0]
