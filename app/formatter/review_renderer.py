"""
Structured review renderer.

Takes raw LLM Markdown output and renders it beautifully in the terminal
using Rich, with coloured panels per section and severity-aware formatting.
"""

from __future__ import annotations

import re

from rich.markdown import Markdown
from rich.panel import Panel
from rich import box

from app.formatter.rich_output import (
    console,
    print_section,
    severity_badge,
)

# Maps section heading keywords → border colour
_SECTION_COLOURS: dict[str, str] = {
    "bugs":         "red",
    "security":     "red",
    "performance":  "yellow",
    "readability":  "cyan",
    "style":        "cyan",
    "architecture": "magenta",
    "design":       "magenta",
    "best":         "green",
    "verdict":      "bright_white",
    "overall":      "bright_white",
}

_SEVERITY_RE = re.compile(
    r"\b(critical|high|medium|low|info)\b", re.IGNORECASE
)


def render_review(markdown_text: str, title: str = "Code Review") -> None:
    """
    Render a full multi-section Markdown review in the terminal.

    Splits on ``##`` headings and renders each section in its own
    colour-coded panel.

    Args:
        markdown_text: Raw Markdown string from the LLM.
        title: Title shown in the top panel.
    """
    print_section(title)

    # Split by ## headings
    sections = re.split(r"(?m)^(#{1,3} .+)$", markdown_text.strip())

    if len(sections) <= 1:
        # No headings found — render as single panel
        console.print(
            Panel(
                Markdown(markdown_text),
                border_style="bright_blue",
                padding=(1, 2),
            )
        )
        return

    # First element may be preamble text
    preamble = sections[0].strip()
    if preamble:
        console.print(Markdown(preamble))

    # Iterate heading + body pairs
    i = 1
    while i < len(sections) - 1:
        heading = sections[i].strip()
        body = sections[i + 1].strip() if i + 1 < len(sections) else ""
        i += 2

        # Pick border colour from heading keywords
        border = "bright_blue"
        heading_lower = heading.lower()
        for keyword, colour in _SECTION_COLOURS.items():
            if keyword in heading_lower:
                border = colour
                break

        # Replace severity keywords with styled versions inline
        body_md = Markdown(body) if body else Markdown("_No issues found._")

        console.print(
            Panel(
                body_md,
                title=f"[bold]{heading}[/bold]",
                border_style=border,
                padding=(1, 2),
                box=box.ROUNDED,
            )
        )


def render_verdict(text: str) -> None:
    """
    Render the overall verdict panel with a risk level badge.

    Args:
        text: The verdict section text.
    """
    risk_level = "medium"
    for level in ("critical", "high", "medium", "low"):
        if level in text.lower():
            risk_level = level
            break

    badge = severity_badge(risk_level)
    console.print(
        Panel(
            Markdown(text),
            title=badge,
            border_style="bright_white",
            padding=(1, 2),
            box=box.DOUBLE,
        )
    )
