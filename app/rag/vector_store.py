"""
ChromaDB vector store client for the RAG pipeline.

Manages a persistent ChromaDB collection that stores code chunk embeddings.
Provides upsert and similarity search operations.
"""

from __future__ import annotations

from typing import Any

from app.config.settings import get_settings
from app.rag.chunker import CodeChunk


class VectorStore:
    """
    Thin wrapper around a ChromaDB persistent collection.

    Uses cosine similarity by default (ChromaDB's ``hnsw:space`` setting).
    """

    def __init__(self) -> None:
        import chromadb  # type: ignore[import-untyped]
        from chromadb.config import Settings as ChromaSettings  # type: ignore

        settings = get_settings()
        chroma_dir = str(settings.chroma_path)

        self._client = chromadb.PersistentClient(
            path=chroma_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=settings.chroma_collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    # ── Write ─────────────────────────────────────────────────────────────────

    def upsert_chunks(
        self,
        chunks: list[CodeChunk],
        embeddings: list[list[float]],
    ) -> None:
        """
        Insert or update code chunks with their embeddings.

        Args:
            chunks: Code chunk objects.
            embeddings: Embedding vectors, one per chunk.
        """
        if not chunks:
            return

        ids = [c.chunk_id for c in chunks]
        documents = [c.content for c in chunks]
        metadatas: list[dict[str, Any]] = [
            {
                "filepath": c.filepath,
                "language": c.language,
                "start_line": c.start_line,
                "end_line": c.end_line,
            }
            for c in chunks
        ]

        # ChromaDB upsert handles duplicates gracefully
        self._collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

    # ── Read ──────────────────────────────────────────────────────────────────

    def search(
        self,
        query_embedding: list[float],
        n_results: int = 5,
        where: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Find the most semantically similar chunks to a query embedding.

        Args:
            query_embedding: Query vector.
            n_results: Maximum results to return.
            where: Optional ChromaDB metadata filter.

        Returns:
            List of result dicts with keys:
            ``id``, ``document``, ``metadata``, ``distance``.
        """
        kwargs: dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": min(n_results, max(1, self._collection.count())),
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            kwargs["where"] = where

        results = self._collection.query(**kwargs)

        output: list[dict[str, Any]] = []
        for i, doc_id in enumerate(results["ids"][0]):
            output.append(
                {
                    "id": doc_id,
                    "document": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i],
                }
            )
        return output

    def count(self) -> int:
        """Return the number of chunks stored in the collection."""
        return self._collection.count()

    def clear(self) -> None:
        """Delete all entries from the collection."""
        settings = get_settings()
        self._client.delete_collection(settings.chroma_collection_name)
        import chromadb
        from chromadb.config import Settings as ChromaSettings
        self._collection = self._client.get_or_create_collection(
            name=settings.chroma_collection_name,
            metadata={"hnsw:space": "cosine"},
        )
