## Context

`generate_chores_ui_html()` in `src/eink_backend/chores_ui.py` returns a multi-hundred-line HTML string for the chores SPA. This string is embedded directly in Python, preventing syntax highlighting, proper HTML formatting, and IDE tooling from working on it. The rest of the project already keeps HTML templates under `assets/` (e.g., `assets/layout-choreday.html`), so extracting to that directory follows the established pattern.

## Goals / Non-Goals

**Goals:**
- Move the HTML string from `chores_ui.py` into `assets/chores_ui.html`.
- Update `generate_chores_ui_html()` to read and return the file contents.
- No changes to the rendered HTML output.

**Non-Goals:**
- Modifying the HTML content, CSS, or JavaScript.
- Changing any API routes or behaviour.
- Adding caching or preprocessing of the HTML file.
- Templating or parameterisation of the HTML file.

## Decisions

### Read file at call time (not at import time)

**Decision:** `generate_chores_ui_html()` reads the file each time it is called rather than caching it at module load.

**Rationale:** Consistent with how the rest of the codebase works (e.g., the Jinja-style template rendering in `main.py` reads assets on each request). The call frequency is low (each page load), so the I/O cost is negligible. Reading at call time also makes development easier — editing the HTML file is reflected immediately without restarting the server.

**Alternative considered:** Cache the content in a module-level variable at import. Rejected because it requires a server restart to pick up edits and adds complexity for no meaningful performance benefit.

### File location: `assets/chores_ui.html`

**Decision:** Place the file in `assets/`, alongside existing layout HTML files.

**Rationale:** `assets/` is already the home for static layout HTML files (`layout-choreday.html`, `layout-shabbat.html`, etc.). The deployment Dockerfile already copies `assets/` into the image.

### Path resolution: relative to `chores_ui.py`

**Decision:** Resolve the path using `Path(__file__).parent.parent.parent / "assets" / "chores_ui.html"` (i.e., navigate from the Python module up to the repo root, then into `assets/`).

**Alternative:** Accept a path from config. Rejected — the file is always in the same repo-relative location and adding config would be over-engineering.

## Risks / Trade-offs

- [Risk] File not found at runtime → Mitigation: the path is deterministic and `assets/` is always deployed alongside the package; a missing file would raise an obvious `FileNotFoundError`.
- [Trade-off] Slightly more I/O per page load → Acceptable; the page is served rarely and the OS caches small files aggressively.

## Migration Plan

1. Create `assets/chores_ui.html` with the extracted HTML content.
2. Update `generate_chores_ui_html()` to read from that file.
3. Delete the inline HTML string from `chores_ui.py`.
4. Verify: run the server, open `/chores`, confirm the page loads identically.
5. No rollback complexity — the change is self-contained and reversible.
