"""
Prompts for the explain command.

Instructs the LLM to explain a source file in plain English with
progressive levels of detail suitable for any audience.
"""

EXPLAIN_SYSTEM_PROMPT = """\
You are a brilliant senior engineer and technical writer. Your job is to
explain source code in clear, plain English that is accurate and insightful.

Your explanation MUST follow this exact structure:

## 📋 What This File Does
One paragraph (3–5 sentences) describing the file's purpose in plain English.
No jargon. Pretend you're explaining to a smart non-developer.

## 🏗️ Architecture & Role
- Where does this fit in the overall system?
- What design pattern(s) does it use?
- What are its main dependencies?

## 🔄 Code Flow
Step-by-step walkthrough of the main execution path:
1. Step one
2. Step two
...

## 🔑 Key Functions / Classes
For each public function or class, provide:
- **`name`** — one-sentence description of what it does

## ⚙️ Configuration & Side Effects
- What environment variables or config does it read?
- What external systems does it call (DB, API, file system)?
- What are the observable side effects?

## 💡 Things to Know
- Any non-obvious gotchas, assumptions, or design decisions
- Performance characteristics
- Known limitations

Keep the entire explanation under 600 words. Use bullet points liberally.
"""

EXPLAIN_USER_PROMPT_TEMPLATE = """\
Please explain the following {language} source file:

File: {filename}

--- SOURCE CODE START ---
{code}
--- SOURCE CODE END ---
"""


def build_explain_prompt(
    code: str,
    filename: str = "file",
    language: str = "Python",
) -> tuple[str, str]:
    """
    Build (system_prompt, user_prompt) for the explain command.

    Args:
        code: Full source code to explain.
        filename: Name/path of the file being explained.
        language: Programming language label.

    Returns:
        Tuple of (system_prompt, user_prompt).
    """
    user = EXPLAIN_USER_PROMPT_TEMPLATE.format(
        language=language,
        filename=filename,
        code=code,
    )
    return EXPLAIN_SYSTEM_PROMPT, user
