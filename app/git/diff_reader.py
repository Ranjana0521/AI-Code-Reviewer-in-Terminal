"""
Git diff reader.

Reads staged, unstaged, or commit-range diffs from the current repository
using GitPython.  Returns a clean ``DiffResult`` dataclass.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import git
from git import InvalidGitRepositoryError, Repo


@dataclass
class FileDiff:
    """Represents the diff of a single file."""

    filename: str
    change_type: str          # A=added, D=deleted, M=modified, R=renamed
    additions: int
    deletions: int
    patch: str                # raw unified diff text


@dataclass
class DiffResult:
    """Aggregated diff information for a repository."""

    repo_root: str
    branch: str
    commit_hash: str
    files: list[FileDiff] = field(default_factory=list)

    @property
    def total_additions(self) -> int:
        return sum(f.additions for f in self.files)

    @property
    def total_deletions(self) -> int:
        return sum(f.deletions for f in self.files)

    @property
    def full_patch(self) -> str:
        """Concatenate all file patches into one string."""
        return "\n\n".join(
            f"--- {f.filename} ({f.change_type}) ---\n{f.patch}"
            for f in self.files
        )


def _count_lines(patch: str) -> tuple[int, int]:
    """Count ``+`` / ``-`` lines in a unified diff patch."""
    additions = sum(1 for ln in patch.splitlines() if ln.startswith("+") and not ln.startswith("+++"))
    deletions = sum(1 for ln in patch.splitlines() if ln.startswith("-") and not ln.startswith("---"))
    return additions, deletions


def read_staged_diff(repo_path: str = ".") -> DiffResult:
    """
    Return the diff of all *staged* (index vs HEAD) changes.

    Args:
        repo_path: Path to the git repository root. Defaults to CWD.

    Returns:
        A populated ``DiffResult``.

    Raises:
        InvalidGitRepositoryError: If ``repo_path`` is not inside a git repo.
        ValueError: If there are no staged changes.
    """
    try:
        repo = Repo(repo_path, search_parent_directories=True)
    except InvalidGitRepositoryError as exc:
        raise InvalidGitRepositoryError(
            f"'{repo_path}' is not inside a Git repository."
        ) from exc

    # Diff staged changes against HEAD (or empty tree if no commits yet)
    if repo.head.is_valid():
        diffs = repo.index.diff(repo.head.commit)
        raw_patch = repo.git.diff("--cached")
    else:
        # Brand-new repo — diff against the empty tree
        diffs = repo.index.diff(None)
        raw_patch = repo.git.diff("--cached")

    branch = _safe_branch(repo)
    commit_hash = repo.head.commit.hexsha[:8] if repo.head.is_valid() else "initial"

    result = DiffResult(
        repo_root=str(Path(repo.working_tree_dir).resolve()),
        branch=branch,
        commit_hash=commit_hash,
    )

    # Parse per-file diffs from the raw patch
    result.files = _parse_patch(raw_patch)
    return result


def read_unstaged_diff(repo_path: str = ".") -> DiffResult:
    """
    Return the diff of all *unstaged* (working tree vs index) changes.

    Args:
        repo_path: Path to the git repository root.

    Returns:
        A populated ``DiffResult``.
    """
    try:
        repo = Repo(repo_path, search_parent_directories=True)
    except InvalidGitRepositoryError as exc:
        raise InvalidGitRepositoryError(
            f"'{repo_path}' is not inside a Git repository."
        ) from exc

    raw_patch = repo.git.diff()
    branch = _safe_branch(repo)
    commit_hash = repo.head.commit.hexsha[:8] if repo.head.is_valid() else "initial"

    result = DiffResult(
        repo_root=str(Path(repo.working_tree_dir).resolve()),
        branch=branch,
        commit_hash=commit_hash,
    )
    result.files = _parse_patch(raw_patch)
    return result


def read_diff_between(
    repo_path: str = ".",
    base: str = "HEAD~1",
    head: str = "HEAD",
) -> DiffResult:
    """
    Return diff between two git refs (commits, branches, tags).

    Args:
        repo_path: Repository path.
        base: Base ref (older).
        head: Head ref (newer).

    Returns:
        A populated ``DiffResult``.
    """
    try:
        repo = Repo(repo_path, search_parent_directories=True)
    except InvalidGitRepositoryError as exc:
        raise InvalidGitRepositoryError(
            f"'{repo_path}' is not inside a Git repository."
        ) from exc

    raw_patch = repo.git.diff(base, head)
    branch = _safe_branch(repo)
    commit_hash = repo.head.commit.hexsha[:8]

    result = DiffResult(
        repo_root=str(Path(repo.working_tree_dir).resolve()),
        branch=branch,
        commit_hash=commit_hash,
    )
    result.files = _parse_patch(raw_patch)
    return result


# ── Internal helpers ──────────────────────────────────────────────────────────

def _safe_branch(repo: Repo) -> str:
    """Return the current branch name, or 'HEAD' if detached."""
    try:
        return repo.active_branch.name
    except TypeError:
        return "HEAD (detached)"


def _parse_patch(raw_patch: str) -> list[FileDiff]:
    """
    Split a raw unified diff into per-file ``FileDiff`` objects.

    Args:
        raw_patch: The full unified diff string.

    Returns:
        List of ``FileDiff`` instances.
    """
    if not raw_patch.strip():
        return []

    files: list[FileDiff] = []
    current_file: str | None = None
    current_lines: list[str] = []
    change_type = "M"

    for line in raw_patch.splitlines(keepends=True):
        if line.startswith("diff --git "):
            # Flush previous file
            if current_file and current_lines:
                patch = "".join(current_lines)
                adds, dels = _count_lines(patch)
                files.append(FileDiff(current_file, change_type, adds, dels, patch))
                current_lines = []

            # Extract filename — take the b/ path
            parts = line.strip().split(" b/")
            current_file = parts[-1] if len(parts) > 1 else line.strip().split()[-1]
            change_type = "M"

        elif line.startswith("new file mode"):
            change_type = "A"
        elif line.startswith("deleted file mode"):
            change_type = "D"
        elif line.startswith("rename "):
            change_type = "R"
        else:
            current_lines.append(line)

    # Flush the last file
    if current_file and current_lines:
        patch = "".join(current_lines)
        adds, dels = _count_lines(patch)
        files.append(FileDiff(current_file, change_type, adds, dels, patch))

    return files
