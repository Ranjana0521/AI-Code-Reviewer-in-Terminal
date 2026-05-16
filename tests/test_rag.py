"""
Tests for the RAG pipeline: chunker, embedder, and retriever.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.rag.chunker import CodeChunk, chunk_file, chunk_repository


class TestChunker:
    def test_chunk_file_basic(self, tmp_path: Path) -> None:
        source = tmp_path / "test.py"
        source.write_text("\n".join(f"line_{i} = {i}" for i in range(100)))
        chunks = chunk_file(source, tmp_path, chunk_size=20, overlap=5)
        assert len(chunks) > 1
        assert all(isinstance(c, CodeChunk) for c in chunks)

    def test_chunk_file_empty(self, tmp_path: Path) -> None:
        source = tmp_path / "empty.py"
        source.write_text("")
        assert chunk_file(source, tmp_path) == []

    def test_chunk_file_small_file(self, tmp_path: Path) -> None:
        source = tmp_path / "small.py"
        source.write_text("x = 1\ny = 2\n")
        chunks = chunk_file(source, tmp_path, chunk_size=60)
        assert len(chunks) == 1

    def test_chunk_ids_are_unique(self, tmp_path: Path) -> None:
        source = tmp_path / "big.py"
        source.write_text("\n".join(f"line = {i}" for i in range(200)))
        chunks = chunk_file(source, tmp_path, chunk_size=20, overlap=5)
        ids = [c.chunk_id for c in chunks]
        assert len(ids) == len(set(ids))

    def test_chunk_repository_collects_files(self, tmp_path: Path) -> None:
        (tmp_path / "app").mkdir()
        (tmp_path / "app" / "main.py").write_text("\n".join(f"x={i}" for i in range(30)))
        chunks = chunk_repository(tmp_path, extensions={".py"}, chunk_size=15, overlap=3)
        assert any("main.py" in c.filepath for c in chunks)

    def test_chunk_repository_skips_pycache(self, tmp_path: Path) -> None:
        (tmp_path / "__pycache__").mkdir()
        (tmp_path / "__pycache__" / "ignore.pyc").write_text("garbage")
        (tmp_path / "real.py").write_text("x = 1\n" * 30)
        chunks = chunk_repository(tmp_path, extensions={".py", ".pyc"}, chunk_size=10)
        assert not any("__pycache__" in c.filepath for c in chunks)


class TestEmbedder:
    @pytest.mark.asyncio
    async def test_embed_chunks_calls_provider(self) -> None:
        fake_vec = [0.1] * 384
        mock_provider = MagicMock()
        mock_provider.embed = AsyncMock(return_value=[fake_vec])
        chunks = [CodeChunk("id1", "f.py", "python", "x = 1", 1, 1)]
        with patch("app.rag.embedder.get_llm_provider", return_value=mock_provider):
            from app.rag.embedder import embed_chunks
            result = await embed_chunks(chunks)
        assert result == [fake_vec]

    @pytest.mark.asyncio
    async def test_embed_query_returns_vector(self) -> None:
        fake_vec = [0.5] * 384
        mock_provider = MagicMock()
        mock_provider.embed = AsyncMock(return_value=[fake_vec])
        with patch("app.rag.embedder.get_llm_provider", return_value=mock_provider):
            from app.rag.embedder import embed_query
            result = await embed_query("find auth code")
        assert result == fake_vec


class TestRetriever:
    @pytest.mark.asyncio
    async def test_retrieve_empty_store(self) -> None:
        mock_store = MagicMock()
        mock_store.count.return_value = 0
        with patch("app.rag.retriever.VectorStore", return_value=mock_store):
            from app.rag.retriever import Retriever
            retriever = Retriever()
            results = await retriever.retrieve("anything")
        assert results == []

    def test_format_context_empty(self) -> None:
        with patch("app.rag.retriever.VectorStore"):
            from app.rag.retriever import Retriever
            retriever = Retriever()
            ctx = retriever.format_context([])
        assert "No relevant context" in ctx

    def test_format_context_max_chars(self) -> None:
        results = [
            {
                "id": f"file.py:{i}",
                "document": "x = 1\n" * 50,
                "metadata": {"filepath": "file.py", "language": "python", "start_line": i, "end_line": i + 10},
                "distance": 0.1,
            }
            for i in range(20)
        ]
        with patch("app.rag.retriever.VectorStore"):
            from app.rag.retriever import Retriever
            retriever = Retriever()
            ctx = retriever.format_context(results, max_chars=300)
        assert len(ctx) < 1000
