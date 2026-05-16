"""
Code chunker for the RAG pipeline.

Splits source files into semantically meaningful chunks suitable for
embedding and retrieval.  Uses a line-window strategy for simplicity
and compatibility across all languages.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class CodeChunk:
    """A single embeddable chunk of source code."""

    chunk_id: str           # unique identifier: "<filepath>:<start>-<end>"
    filepath: str           # relative path within the repository
    language: str           # programming language label
    content: str            # actual code text
    start_line: int         # 1-indexed start line in original file
    end_line: int           # 1-indexed end line in original file


def chunk_file(
    filepath: str | Path,
    repo_root: str | Path,
    chunk_size: int = 60,
    overlap: int = 10,
) -> list[CodeChunk]:
    """
    Split a single source file into overlapping line-window chunks.

    Args:
        filepath: Absolute path to the file.
        repo_root: Repository root (used to compute relative path).
        chunk_size: Number of lines per chunk.
        overlap: Number of lines shared between adjacent chunks.

    Returns:
        List of ``CodeChunk`` objects.
    """
    filepath = Path(filepath)
    repo_root = Path(repo_root)

    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
    except (OSError, PermissionError):
        return []

    lines = content.splitlines()
    if not lines:
        return []

    try:
        relative = str(filepath.relative_to(repo_root))
    except ValueError:
        relative = str(filepath)

    # Detect language
    from app.utils.file_utils import detect_language
    language = detect_language(filepath.name)

    chunks: list[CodeChunk] = []
    step = max(1, chunk_size - overlap)
    i = 0

    while i < len(lines):
        end = min(i + chunk_size, len(lines))
        chunk_lines = lines[i:end]
        chunk_text = "\n".join(chunk_lines).strip()

        if chunk_text:
            chunk_id = f"{relative}:{i + 1}-{end}"
            chunks.append(
                CodeChunk(
                    chunk_id=chunk_id,
                    filepath=relative,
                    language=language,
                    content=chunk_text,
                    start_line=i + 1,
                    end_line=end,
                )
            )

        i += step
        if end >= len(lines):
            break

    return chunks


def chunk_repository(
    repo_root: str | Path,
    extensions: set[str] | None = None,
    chunk_size: int = 60,
    overlap: int = 10,
) -> list[CodeChunk]:
    """
    Chunk all source files in a repository.

    Args:
        repo_root: Repository root directory.
        extensions: File extensions to include. Defaults to common source files.
        chunk_size: Lines per chunk.
        overlap: Overlap lines between chunks.

    Returns:
        All chunks from all matched files.
    """
    from app.utils.file_utils import collect_source_files

    default_extensions = {
        ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs",
        ".cpp", ".c", ".cs", ".rb", ".php", ".swift", ".kt", ".scala",
        ".sh", ".sql", ".yaml", ".yml", ".toml", ".md",
    }
    exts = extensions or default_extensions

    files = collect_source_files(repo_root, extensions=exts)
    all_chunks: list[CodeChunk] = []

    for f in files:
        all_chunks.extend(chunk_file(f, repo_root, chunk_size, overlap))

    return all_chunks
