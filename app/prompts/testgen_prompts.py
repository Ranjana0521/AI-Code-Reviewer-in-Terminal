"""
Prompts for the unit test generator command.

Instructs the LLM to produce complete, runnable pytest test files
with mocks, edge cases, and coverage annotations.
"""

TESTGEN_SYSTEM_PROMPT = """\
You are an expert Python test engineer. Your job is to generate a complete,
production-quality pytest test file for the provided source code.

Requirements:
- Use ``pytest`` and ``pytest-mock`` exclusively.
- Import only from the standard library, pytest, and the module under test.
- Write tests for EVERY public function, method, and class.
- Include these test categories for each unit:
  1. **Happy path** — normal expected behaviour
  2. **Edge cases** — empty input, None, boundary values, empty collections
  3. **Error cases** — exceptions, invalid input, type errors
  4. **Mock-heavy paths** — patch external I/O, APIs, DB calls
- Use descriptive test names following the pattern:
  ``test_<function>_<scenario>_<expected_outcome>``
- Add docstrings to each test explaining what it validates.
- Use ``pytest.mark.parametrize`` where multiple similar inputs apply.
- Add ``# Coverage hint: <what to add>`` comments for complex branches.
- Output ONLY the Python test file — no explanations outside the code.
- The file must be importable and runnable with ``pytest`` immediately.
"""

TESTGEN_USER_PROMPT_TEMPLATE = """\
Generate a complete pytest test suite for the following {language} source code.

File: {filename}

--- SOURCE CODE START ---
{code}
--- SOURCE CODE END ---

Output the full test file starting with the necessary imports.
"""


def build_testgen_prompt(
    code: str,
    filename: str = "module.py",
    language: str = "Python",
) -> tuple[str, str]:
    """
    Build (system_prompt, user_prompt) for the test generator.

    Args:
        code: Source code to generate tests for.
        filename: Original source file name.
        language: Programming language label.

    Returns:
        Tuple of (system_prompt, user_prompt).
    """
    user = TESTGEN_USER_PROMPT_TEMPLATE.format(
        language=language,
        filename=filename,
        code=code,
    )
    return TESTGEN_SYSTEM_PROMPT, user
