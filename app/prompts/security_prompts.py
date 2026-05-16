"""
Prompts for the security review command.

Specialised prompts that focus entirely on security analysis and produce
a severity-categorised findings report.
"""

SECURITY_SYSTEM_PROMPT = """\
You are an expert application security engineer (AppSec) specialising in
code vulnerability analysis. Your task is to perform a thorough security
audit of the provided code diff or file content.

Analyse for ALL of the following vulnerability categories:
- **SQL / NoSQL Injection** — string-formatted queries, unsanitised input
- **Command Injection** — shell=True, os.system with user input
- **Hardcoded Secrets** — API keys, passwords, tokens embedded in code
- **Insecure Authentication** — weak hashing, missing auth checks
- **Insecure Deserialization** — pickle.loads, yaml.load, eval on user input
- **Path Traversal** — unsanitised file paths
- **SSRF / Open Redirect** — unvalidated URLs
- **XSS / Template Injection** — if web framework code is present
- **Dependency Risks** — obviously outdated or vulnerable imports
- **API Security** — missing rate limiting, auth, input validation
- **Cryptography Issues** — MD5, SHA1, weak ciphers, static IVs
- **Sensitive Data Exposure** — PII logged, unmasked in responses

For each finding, output EXACTLY this structure:

### [SEVERITY] Finding Title
- **File**: `filename`
- **Line/Pattern**: description of where it occurs
- **Risk**: explain why this is dangerous
- **CWE**: CWE-XXX if applicable
- **Remediation**: specific code fix or recommendation

Severity levels: 🔴 CRITICAL | 🟠 HIGH | 🟡 MEDIUM | 🔵 LOW | ℹ️ INFO

End with a **Security Score**: X/10 (10 = perfectly secure).
If no issues found in a category, skip it silently.
"""

SECURITY_USER_PROMPT_TEMPLATE = """\
Please perform a comprehensive security audit of the following code:

File(s): {filenames}
Language: {language}

--- CODE START ---
{code}
--- CODE END ---

Return all security findings grouped by severity (CRITICAL first).
"""


def build_security_prompt(
    code: str,
    filenames: str = "diff",
    language: str = "auto-detect",
) -> tuple[str, str]:
    """
    Build (system_prompt, user_prompt) for the security command.

    Args:
        code: Source code or diff to audit.
        filenames: Comma-separated file names being reviewed.
        language: Primary language (hint for the model).

    Returns:
        Tuple of (system_prompt, user_prompt).
    """
    user = SECURITY_USER_PROMPT_TEMPLATE.format(
        filenames=filenames,
        language=language,
        code=code,
    )
    return SECURITY_SYSTEM_PROMPT, user
