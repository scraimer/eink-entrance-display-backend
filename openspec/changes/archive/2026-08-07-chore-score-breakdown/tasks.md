## 1. Backend — extend score query with component fields

- [x] 1.1 Update the `SELECT` clause in `compute_chore_scores()` in `chores_db.py` to also select `COUNT(e.id) AS execution_count` and `COALESCE(CAST(MIN(julianday(:as_of_date) - julianday(e.execution_date)) AS INTEGER), NULL)` AS `days_since_last` (before applying the recency cap, so callers can display the real value; apply the cap only for the score arithmetic already present).
- [x] 1.2 Define a `ChoreScore` dataclass in `chores_db.py` with fields `person_id: int`, `chore_id: int`, `score: int`, `execution_count: int`, `days_since_last: int | None`. Change the return type of `compute_chore_scores()` from `list[tuple[int, int, int]]` to `list[ChoreScore]` and update the function to construct and return `ChoreScore` instances.
- [x] 1.3 Update all call sites of `compute_chore_scores()` in `chores_api.py` and `chores_db.py` to use named attribute access (`.person_id`, `.chore_id`, `.score`, etc.) instead of tuple unpacking.

## 2. API — propagate components into person_scores

- [x] 2.1 In `_build_plan_snapshot()` in `chores_api.py`, update the `scores_by_chore` dict assembly to store `{person_id, score, execution_count, days_since_last}` instead of `{person_id, score}`.
- [x] 2.2 Ensure the stored `person_scores` list in each chore dict passes through all four fields so the JSON response includes them.

## 3. Tests — update and add coverage

- [x] 3.1 Update any existing tests that assert on the shape of `compute_chore_scores()` tuples to unpack the new five-element form.
- [x] 3.2 Add a test case asserting that the `person_scores` entries in the summary response include `execution_count` and `days_since_last`.
- [x] 3.3 Add a test case for a person who has never done the chore (expects `days_since_last: null` and `execution_count: 0`).

## 4. UI — expandable score breakdown

- [x] 4.1 In `assets/chores_ui.html`, update the `scoreRows` mapping in `choreDetailHTML()` to store `execution_count` and `days_since_last` from the score object as `data-` attributes on the score badge element.
- [x] 4.2 Add a `▸` indicator to each score badge to signal it is interactive; change to `▾` when expanded.
- [x] 4.3 Add an `onclick` handler (or delegated listener) to each score badge that toggles an adjacent inline `<span>` showing the formula breakdown: `{execution_count} × 1000 − {days} = {score}` (use `365` in place of `days` when `days_since_last` is null).
- [x] 4.4 Add minimal CSS for the breakdown text (e.g. `font-size: 0.75rem; color: #718096; margin-left: 0.4rem`).
