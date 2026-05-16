"""General-purpose file utilities."""

from __future__ import annotations

from pathlib import Path


def read_file_safe(path: str | Path, max_chars: int = 50_000) -> str:
    """
    Read a file and return its content as a string.

    Args:
        path: File path.
        max_chars: Maximum characters to read (avoids huge files).

    Returns:
        File content string, or empty string if the file can't be read.
    """
    try:
        content = Path(path).read_text(encoding="utf-8", errors="ignore")
        return content[:max_chars] if max_chars else content
    except (OSError, PermissionError):
        return ""


def truncate_text(text: str, max_lines: int) -> str:
    """
    Truncate text to at most ``max_lines`` lines.

    Args:
        text: Input text.
        max_lines: Maximum number of lines to keep (0 = no limit).

    Returns:
        Truncated text, appending a note if truncation occurred.
    """
    if not max_lines:
        return text
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text
    kept = lines[:max_lines]
    kept.append(f"\n... [truncated — {len(lines) - max_lines} lines omitted] ...")
    return "\n".join(kept)


def detect_language(filename: str) -> str:
    """
    Guess programming language from a file extension.

    Args:
        filename: File name or path.

    Returns:
        Language label string (e.g. ``"python"``, ``"javascript"``).
    """
    ext_map: dict[str, str] = {
        ".py": "python", ".js": "javascript", ".ts": "typescript",
        ".tsx": "typescript", ".jsx": "javascript", ".java": "java",
        ".go": "go", ".rs": "rust", ".cpp": "cpp", ".c": "c",
        ".cs": "csharp", ".rb": "ruby", ".php": "php",
        ".swift": "swift", ".kt": "kotlin", ".sh": "bash",
        ".sql": "sql", ".yaml": "yaml", ".yml": "yaml",
        ".json": "json", ".toml": "toml", ".md": "markdown",
        ".html": "html", ".css": "css",
    }
    suffix = Path(filename).suffix.lower()
    return ext_map.get(suffix, "text")


def collect_source_files(
    root: str | Path,
    extensions: set[str] | None = None,
    exclude_dirs: set[str] | None = None,
) -> list[Path]:
    """
    Recursively collect source files under ``root``.

    Args:
        root: Root directory to scan.
        extensions: Allowed file extensions (e.g. ``{".py", ".js"}``).
            ``None`` means all files.
        exclude_dirs: Directory names to skip.

    Returns:
        Sorted list of absolute ``Path`` objects.
    """
    root = Path(root)
    default_exclude = {
        ".git", "__pycache__", "node_modules", ".venv", "venv",
        "dist", "build", ".chroma_db", ".cache", ".mypy_cache",
    }
    skip = (exclude_dirs or set()) | default_exclude

    result: list[Path] = []
    for path in root.rglob("*"):
        if any(part in skip for part in path.parts):
            continue
        if not path.is_file():
            continue
        if extensions and path.suffix.lower() not in extensions:
            continue
        result.append(path)

    return sorted(result)
