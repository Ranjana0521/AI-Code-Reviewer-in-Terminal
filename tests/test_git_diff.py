"""
Tests for app.git.diff_reader module.

Verifies staged/unstaged diff reading, patch parsing, and FileDiff
dataclass correctness using a temporary git repository.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
import git

from app.git.diff_reader import (
    FileDiff,
    DiffResult,
    _count_lines,
    _parse_patch,
    read_unstaged_diff,
    read_staged_diff,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture()
def tmp_repo(tmp_path: Path) -> git.Repo:
    """Create a minimal git repository with one initial commit."""
    repo = git.Repo.init(tmp_path)
    repo.config_writer().set_value("user", "name", "Test").release()
    repo.config_writer().set_value("user", "email", "test@test.com").release()

    initial = tmp_path / "hello.py"
    initial.write_text("# hello\nprint('hello')\n")
    repo.index.add(["hello.py"])
    repo.index.commit("initial commit")
    return repo


# ── _count_lines ──────────────────────────────────────────────────────────────

class TestCountLines:
    def test_count_lines_additions_and_deletions(self) -> None:
        """Should count + lines as additions and - lines as deletions."""
        patch = "+++ b/file.py\n+new line\n-old line\n unchanged\n"
        adds, dels = _count_lines(patch)
        assert adds == 1
        assert dels == 1

    def test_count_lines_empty_patch(self) -> None:
        """Empty patch should return zero counts."""
        assert _count_lines("") == (0, 0)

    def test_count_lines_only_additions(self) -> None:
        """Patch with only additions."""
        patch = "+line1\n+line2\n+line3\n"
        adds, dels = _count_lines(patch)
        assert adds == 3
        assert dels == 0

    def test_count_lines_ignores_diff_headers(self) -> None:
        """Lines starting with +++ or --- should not be counted."""
        patch = "+++ b/foo.py\n--- a/foo.py\n+real addition\n"
        adds, dels = _count_lines(patch)
        assert adds == 1
        assert dels == 0


# ── _parse_patch ──────────────────────────────────────────────────────────────

class TestParsePatch:
    def test_parse_empty_patch(self) -> None:
        """Empty or whitespace-only patch returns empty list."""
        assert _parse_patch("") == []
        assert _parse_patch("   \n  ") == []

    def test_parse_single_file(self) -> None:
        """Single file diff produces one FileDiff."""
        patch = (
            "diff --git a/app/main.py b/app/main.py\n"
            "index abc..def 100644\n"
            "+++ b/app/main.py\n"
            "+new line\n"
            "-old line\n"
        )
        files = _parse_patch(patch)
        assert len(files) == 1
        assert files[0].filename == "app/main.py"

    def test_parse_new_file(self) -> None:
        """A 'new file mode' line sets change_type to 'A'."""
        patch = (
            "diff --git a/new.py b/new.py\n"
            "new file mode 100644\n"
            "+++ b/new.py\n"
            "+print('hi')\n"
        )
        files = _parse_patch(patch)
        assert files[0].change_type == "A"

    def test_parse_deleted_file(self) -> None:
        """A 'deleted file mode' line sets change_type to 'D'."""
        patch = (
            "diff --git a/old.py b/old.py\n"
            "deleted file mode 100644\n"
            "--- a/old.py\n"
            "-bye\n"
        )
        files = _parse_patch(patch)
        assert files[0].change_type == "D"

    def test_parse_multiple_files(self) -> None:
        """Multiple diff sections produce multiple FileDiff objects."""
        patch = (
            "diff --git a/a.py b/a.py\n"
            "+line\n"
            "diff --git a/b.py b/b.py\n"
            "+other\n"
        )
        files = _parse_patch(patch)
        assert len(files) == 2


# ── DiffResult properties ─────────────────────────────────────────────────────

class TestDiffResult:
    def test_total_additions(self) -> None:
        """total_additions sums all file additions."""
        dr = DiffResult(
            repo_root="/repo",
            branch="main",
            commit_hash="abc1234",
            files=[
                FileDiff("a.py", "M", 5, 2, ""),
                FileDiff("b.py", "A", 10, 0, ""),
            ],
        )
        assert dr.total_additions == 15

    def test_total_deletions(self) -> None:
        """total_deletions sums all file deletions."""
        dr = DiffResult(
            repo_root="/repo",
            branch="main",
            commit_hash="abc1234",
            files=[
                FileDiff("a.py", "M", 5, 3, ""),
                FileDiff("b.py", "D", 0, 7, ""),
            ],
        )
        assert dr.total_deletions == 10

    def test_full_patch_combines_files(self) -> None:
        """full_patch joins all file patches with separators."""
        dr = DiffResult(
            repo_root="/repo",
            branch="main",
            commit_hash="abc",
            files=[
                FileDiff("a.py", "M", 1, 0, "+hello"),
                FileDiff("b.py", "M", 1, 0, "+world"),
            ],
        )
        assert "+hello" in dr.full_patch
        assert "+world" in dr.full_patch
        assert "a.py" in dr.full_patch


# ── Integration: real repo diff ───────────────────────────────────────────────

class TestReadDiffIntegration:
    def test_read_unstaged_diff_no_changes(self, tmp_repo: git.Repo) -> None:
        """Unstaged diff on clean repo returns no files."""
        result = read_unstaged_diff(str(tmp_repo.working_tree_dir))
        assert result.files == []

    def test_read_unstaged_diff_with_changes(self, tmp_repo: git.Repo) -> None:
        """Modified file appears in unstaged diff."""
        file = Path(tmp_repo.working_tree_dir) / "hello.py"
        file.write_text("# modified\nprint('changed')\n")
        result = read_unstaged_diff(str(tmp_repo.working_tree_dir))
        assert len(result.files) >= 1

    def test_invalid_repo_raises(self, tmp_path: Path) -> None:
        """Non-git directory raises InvalidGitRepositoryError."""
        with pytest.raises(git.InvalidGitRepositoryError):
            read_staged_diff(str(tmp_path))
