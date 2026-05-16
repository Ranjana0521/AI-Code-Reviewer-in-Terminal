"""
Repository metadata scanner.

Walks the repository tree to collect structural information used by
the RAG pipeline and context-aware prompts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import git
from git import InvalidGitRepositoryError, Repo


@dataclass
class RepoMetadata:
    """High-level metadata about a git repository."""

    root: str
    name: str
    branch: str
    total_files: int
    languages: dict[str, int]           # extension -> file count
    top_level_dirs: list[str]
    recent_commits: list[str]           # last 10 commit messages
    readme_snippet: str = ""            # first 500 chars of README


# Common source-code extensions → language labels
_EXT_MAP: dict[str, str] = {
    ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
    ".tsx": "TypeScript", ".jsx": "JavaScript", ".java": "Java",
    ".go": "Go", ".rs": "Rust", ".cpp": "C++", ".c": "C",
    ".cs": "C#", ".rb": "Ruby", ".php": "PHP", ".swift": "Swift",
    ".kt": "Kotlin", ".scala": "Scala", ".sh": "Shell",
    ".md": "Markdown", ".yaml": "YAML", ".yml": "YAML",
    ".json": "JSON", ".toml": "TOML", ".sql": "SQL",
}

# Directories to skip when scanning
_IGNORE_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv",
    "dist", "build", ".mypy_cache", ".pytest_cache", ".ruff_cache",
    ".chroma_db", ".cache",
}


def scan_repo(repo_path: str = ".") -> RepoMetadata:
    """
    Scan a git repository and return its metadata.

    Args:
        repo_path: Path to the repository root.

    Returns:
        A ``RepoMetadata`` dataclass with structural information.
    """
    try:
        repo = Repo(repo_path, search_parent_directories=True)
    except InvalidGitRepositoryError as exc:
        raise InvalidGitRepositoryError(
            f"'{repo_path}' is not a Git repository."
        ) from exc

    root = Path(repo.working_tree_dir).resolve()
    name = root.name

    # Branch
    try:
        branch = repo.active_branch.name
    except TypeError:
        branch = "HEAD (detached)"

    # Walk tree
    lang_counts: dict[str, int] = {}
    total_files = 0
    top_dirs: set[str] = set()

    for path in root.rglob("*"):
        if any(skip in path.parts for skip in _IGNORE_DIRS):
            continue
        if path.is_file():
            total_files += 1
            ext = path.suffix.lower()
            lang = _EXT_MAP.get(ext, "Other")
            lang_counts[lang] = lang_counts.get(lang, 0) + 1
            # Collect top-level directories
            relative = path.relative_to(root)
            if len(relative.parts) > 1:
                top_dirs.add(relative.parts[0])

    # Recent commits
    recent: list[str] = []
    try:
        for commit in repo.iter_commits(max_count=10):
            msg = commit.message.strip().splitlines()[0]
            recent.append(f"{commit.hexsha[:7]} {msg}")
    except Exception:
        pass

    # README snippet
    readme_snippet = ""
    for readme_name in ("README.md", "README.rst", "README.txt", "README"):
        readme_path = root / readme_name
        if readme_path.exists():
            readme_snippet = readme_path.read_text(encoding="utf-8", errors="ignore")[:500]
            break

    return RepoMetadata(
        root=str(root),
        name=name,
        branch=branch,
        total_files=total_files,
        languages=lang_counts,
        top_level_dirs=sorted(top_dirs),
        recent_commits=recent,
        readme_snippet=readme_snippet,
    )
