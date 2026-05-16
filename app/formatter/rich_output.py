"""
Rich terminal UI components.

Central module for all terminal output using the ``rich`` library.
Import and use ``console`` directly, or call the helper functions for
consistent styling across the entire application.
"""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.theme import Theme
from rich import box

# ── Custom colour theme ───────────────────────────────────────────────────────
_THEME = Theme(
    {
        "info":     "bold cyan",
        "success":  "bold green",
        "warning":  "bold yellow",
        "error":    "bold red",
        "critical": "bold white on red",
        "high":     "bold red",
        "medium":   "bold yellow",
        "low":      "bold cyan",
        "dim_text": "dim white",
        "heading":  "bold bright_white",
        "brand":    "bold magenta",
    }
)

# Shared console — import this everywhere
console = Console(theme=_THEME, highlight=True)


# ── Banner ────────────────────────────────────────────────────────────────────

def print_banner() -> None:
    """Print the application startup banner."""
    banner = Text()
    banner.append("  ██████╗ ██╗    ", style="bold magenta")
    banner.append("\n")
    banner.append("  ██╔══██╗██║    ", style="bold magenta")
    banner.append("AI Code Reviewer", style="bold bright_white")
    banner.append("\n")
    banner.append("  ██║  ██║██║    ", style="bold magenta")
    banner.append("v1.0.0  •  OpenAI + Ollama + LangGraph", style="dim white")
    banner.append("\n")
    banner.append("  ██████╔╝██║    ", style="bold magenta")
    banner.append("\n")
    banner.append("  ╚═════╝ ╚═╝    ", style="bold magenta")

    console.print(
        Panel(
            banner,
            border_style="magenta",
            padding=(1, 4),
            subtitle="[dim]github.com/aicodereviewer[/dim]",
        )
    )


# ── Section headers ───────────────────────────────────────────────────────────

def print_section(title: str, subtitle: str = "") -> None:
    """Print a bold section panel."""
    content = Text(subtitle, style="dim white") if subtitle else Text("")
    console.print(
        Panel(
            content,
            title=f"[heading]{title}[/heading]",
            border_style="bright_blue",
            padding=(0, 2),
        )
    )


# ── Severity label ────────────────────────────────────────────────────────────

_SEVERITY_STYLES: dict[str, tuple[str, str]] = {
    "critical": ("🔴", "critical"),
    "high":     ("🟠", "high"),
    "medium":   ("🟡", "medium"),
    "low":      ("🔵", "low"),
    "info":     ("ℹ️ ", "info"),
    "pass":     ("✅", "success"),
}


def severity_badge(level: str) -> Text:
    """Return a coloured severity badge ``Text`` object."""
    level_lower = level.lower()
    icon, style = _SEVERITY_STYLES.get(level_lower, ("❓", "dim_text"))
    t = Text()
    t.append(f" {icon} {level.upper()} ", style=style)
    return t


# ── Code syntax panel ─────────────────────────────────────────────────────────

def print_code(code: str, language: str = "python", title: str = "") -> None:
    """Render a syntax-highlighted code block in a panel."""
    syntax = Syntax(
        code,
        language,
        theme="monokai",
        line_numbers=True,
        word_wrap=True,
    )
    console.print(
        Panel(
            syntax,
            title=f"[dim]{title}[/dim]" if title else None,
            border_style="dim blue",
            padding=(0, 1),
        )
    )


# ── Diff stats table ──────────────────────────────────────────────────────────

def print_diff_stats(files: list[dict]) -> None:
    """
    Render a table of changed files with addition/deletion counts.

    Args:
        files: List of dicts with keys: ``filename``, ``change_type``,
               ``additions``, ``deletions``.
    """
    table = Table(
        box=box.ROUNDED,
        border_style="dim blue",
        header_style="bold bright_white",
        show_lines=False,
    )
    table.add_column("Status", style="bold", width=4, justify="center")
    table.add_column("File", style="cyan")
    table.add_column("  +", style="green", justify="right", width=6)
    table.add_column("  -", style="red", justify="right", width=6)

    _change_icons = {"A": "✚", "D": "✖", "M": "●", "R": "↪"}
    for f in files:
        icon = _change_icons.get(f.get("change_type", "M"), "●")
        table.add_row(
            icon,
            f["filename"],
            f"+{f['additions']}",
            f"-{f['deletions']}",
        )
    console.print(table)


# ── Spinner / progress context ────────────────────────────────────────────────

def make_spinner(description: str = "Thinking…") -> Progress:
    """Create a progress spinner for long-running operations."""
    return Progress(
        SpinnerColumn(spinner_name="dots", style="magenta"),
        TextColumn("[bold cyan]{task.description}"),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    )


# ── Generic Markdown panel ────────────────────────────────────────────────────

def print_markdown_panel(markdown_text: str, title: str = "Result") -> None:
    """Render Markdown text inside a styled panel."""
    from rich.markdown import Markdown

    md = Markdown(markdown_text)
    console.print(
        Panel(
            md,
            title=f"[heading]{title}[/heading]",
            border_style="bright_blue",
            padding=(1, 2),
        )
    )


# ── Simple status messages ────────────────────────────────────────────────────

def print_success(msg: str) -> None:
    """Print a green success line."""
    console.print(f"[success]✔  {msg}[/success]")


def print_error(msg: str) -> None:
    """Print a red error line."""
    console.print(f"[error]✖  {msg}[/error]")


def print_warning(msg: str) -> None:
    """Print a yellow warning line."""
    console.print(f"[warning]⚠  {msg}[/warning]")


def print_info(msg: str) -> None:
    """Print a cyan info line."""
    console.print(f"[info]ℹ  {msg}[/info]")
