"""
Prompts for the full code review command.

These prompts instruct the LLM to act as a senior code reviewer and
return structured Markdown output covering bugs, security, performance,
readability, best practices, and architecture.
"""

REVIEW_SYSTEM_PROMPT = """\
You are an elite senior software engineer conducting a thorough code review.
Your job is to analyse the provided git diff and produce a detailed, actionable,
and structured review in Markdown.

Review dimensions you MUST cover (use these exact headings):
1. **🐛 Bugs & Logic Errors** — incorrect logic, off-by-one, null-reference risks
2. **🔒 Security Vulnerabilities** — injection, secrets, insecure patterns
3. **⚡ Performance Issues** — inefficiency, N+1 queries, blocking calls
4. **📖 Readability & Style** — naming, comments, complexity
5. **🏗️ Architecture & Design** — SOLID violations, coupling, design smells
6. **✅ Best Practices** — missing tests, error handling, logging
7. **💡 Overall Verdict** — HIGH / MEDIUM / LOW risk rating + one-line summary

Rules:
- Be direct and specific. Reference exact file names and line ranges when possible.
- If a section has no issues, write "No issues found." — do NOT skip the heading.
- Use inline code (`backticks`) for all code references.
- Keep each finding concise: problem → why it matters → suggested fix.
- Do NOT praise generic things. Focus entirely on improvements.
"""

REVIEW_USER_PROMPT_TEMPLATE = """\
Repository: {repo_name}
Branch: {branch}
Commit: {commit_hash}
Changed files: {file_count} ({total_additions}+ / {total_deletions}-)

--- DIFF START ---
{diff}
--- DIFF END ---

Please review the above diff thoroughly and return your structured review.
"""


def build_review_prompt(
    diff: str,
    repo_name: str = "unknown",
    branch: str = "main",
    commit_hash: str = "HEAD",
    file_count: int = 0,
    total_additions: int = 0,
    total_deletions: int = 0,
) -> tuple[str, str]:
    """
    Build (system_prompt, user_prompt) for the review command.

    Args:
        diff: Raw unified diff text.
        repo_name: Repository name shown to the LLM.
        branch: Current git branch.
        commit_hash: Short commit hash.
        file_count: Number of files changed.
        total_additions: Total lines added.
        total_deletions: Total lines deleted.

    Returns:
        Tuple of (system_prompt, user_prompt).
    """
    user = REVIEW_USER_PROMPT_TEMPLATE.format(
        repo_name=repo_name,
        branch=branch,
        commit_hash=commit_hash,
        file_count=file_count,
        total_additions=total_additions,
        total_deletions=total_deletions,
        diff=diff,
    )
    return REVIEW_SYSTEM_PROMPT, user
