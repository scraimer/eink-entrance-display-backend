"""
Single-page web application for managing chores.

Served at GET /chores. All HTML, CSS, and JS are inlined — no external
dependencies, no build step.
"""

from pathlib import Path

_HTML_FILE = Path(__file__).parent.parent.parent / "assets" / "chores_ui.html"


def generate_chores_ui_html() -> str:
    """Return the full HTML string for the /chores SPA."""
    return _HTML_FILE.read_text(encoding="utf-8")
