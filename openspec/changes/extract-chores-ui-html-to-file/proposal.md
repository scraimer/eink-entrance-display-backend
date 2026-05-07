## Why

The HTML for the chores SPA is currently embedded as a Python string inside `generate_chores_ui_html()` in `chores_ui.py`. This makes it difficult to read, edit, and syntax-highlight the HTML, and conflates presentation with Python logic. Extracting it to a standalone `.html` file improves maintainability and enables proper editor tooling.

## What Changes

- A new `assets/chores_ui.html` file is created containing the full SPA HTML (currently inlined in Python).
- `generate_chores_ui_html()` in `src/eink_backend/chores_ui.py` is updated to read and return the HTML from that file at call time.
- No changes to the HTML content, API, or routes — purely a structural refactor.

## Capabilities

### New Capabilities

<!-- None — this is a pure structural refactor with no new user-facing capabilities. -->

### Modified Capabilities

- `chores-ui`: The chores UI is now loaded from a file rather than being inlined in Python. No requirement changes — implementation detail only.

## Impact

- `src/eink_backend/chores_ui.py`: refactored to read from file.
- `assets/chores_ui.html`: new file created.
- Deployment: the `assets/` directory must be included in the deployment image (it already is for other assets).
- No API or schema changes.
