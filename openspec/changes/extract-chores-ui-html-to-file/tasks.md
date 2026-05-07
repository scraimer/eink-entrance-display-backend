## 1. Extract HTML to file

- [x] 1.1 Create `assets/chores_ui.html` with the full HTML content currently inside the `generate_chores_ui_html()` return string (remove the surrounding Python string delimiters)

## 2. Update Python module

- [x] 2.1 Update `generate_chores_ui_html()` in `src/eink_backend/chores_ui.py` to resolve `assets/chores_ui.html` relative to the module file and return its contents
- [x] 2.2 Remove the inline HTML string from `chores_ui.py`

## 3. Verify

- [x] 3.1 Start the server and open `/chores` in a browser; confirm the page loads and all tabs (Chores, Management, Audit Log) work correctly
