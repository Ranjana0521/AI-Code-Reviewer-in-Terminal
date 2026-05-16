"""
Prompts for the commit message generator command.

Produces Conventional Commits-compliant messages from a git diff.
"""

COMMIT_SYSTEM_PROMPT = """\
You are an expert developer who writes perfect git commit messages.

Follow the Conventional Commits specification (https://www.conventionalcommits.org):
  <type>(<scope>): <short description>

  [optional body]

  [optional footer(s)]

Allowed types: feat, fix, refactor, perf, test, docs, style, chore, ci, build

Rules:
- First line ≤ 72 characters, imperative mood ("add" not "added")
- Body explains WHAT changed and WHY (not HOW) — wrap at 100 chars
- Footer includes breaking changes as ``BREAKING CHANGE: <description>``
- Reference issues as ``Closes #123`` when inferrable from context
- Output EXACTLY three versions:
  1. **Minimal** — single-line conventional commit
  2. **Standard** — commit + concise body (3–5 lines)
  3. **Detailed** — commit + full body + changelog bullet points

Separate each version with ``---``.
Do NOT include any text before "1. **Minimal**".
"""

COMMIT_USER_PROMPT_TEMPLATE = """\
Generate commit messages for the following git diff:

Repository: {repo_name}
Branch: {branch}
Changed files: {file_count}

--- DIFF START ---
{diff}
--- DIFF END ---
"""


def build_commit_prompt(
    diff: str,
    repo_name: str = "unknown",
    branch: str = "main",
    file_count: int = 0,
) -> tuple[str, str]:
    """
    Build (system_prompt, user_prompt) for the commit message generator.

    Args:
        diff: Raw unified diff text.
        repo_name: Repository name.
        branch: Current branch.
        file_count: Number of changed files.

    Returns:
        Tuple of (system_prompt, user_prompt).
    """
    user = COMMIT_USER_PROMPT_TEMPLATE.format(
        repo_name=repo_name,
        branch=branch,
        file_count=file_count,
        diff=diff,
    )
    return COMMIT_SYSTEM_PROMPT, user
