## Why

The current chore scheduling system assigns the next executor to a chore manually or via a round-robin based on ordinal order, without considering historical execution frequency or recency. This leads to unequal distribution over time. A weighted scoring system will automatically and fairly assign chores to the person who has done it least (and longest ago), without manual intervention.

## What Changes

- **BREAKING**: Remove `next_executor_id` column from `chore_state` table — the next executor is now computed dynamically from execution history using a weighted score.
- Add a `fixed_executor_id` column (FK → people) to `chore_state` (or a separate table) to handle chores where the executor never changes (replaces the `same_person_next_time` flag + stored next_executor logic for that case).
- Implement a weighted scoring SQL query: score = (1000 × execution_count) + (capped_days_since_last_execution × -1), where `capped_days_since_last_execution = min(days_since_last_execution, 365)`, selecting the person with the lowest score as next executor. Only people with `in_rotation = true` are eligible.
- The Chores UI tab now shows, for each chore in its details (after clicking on it), the weighted score of every eligible person who could be assigned — so staff can see the current state of fairness.
- Remove the API endpoint (or field) that sets `next_executor_id` on `chore_state`, since it is no longer stored.
- Update the "mark chore done" flow to recalculate next executor dynamically after recording the execution, rather than looking up a stored value.

## Capabilities

### New Capabilities

- `fair-chore-distribution`: Dynamic next-executor selection using weighted scores derived from execution history. Computes, for every in-rotation person × chore pair, a score = 1000 × execution_count + (−1) × min(days_since_last_execution, 365) (lower score = higher priority). The person with the lowest score is the next executor. Scores for all eligible people are exposed in the API and displayed in the UI.
- `fixed-chore-executor`: A way to designate a single permanent executor for a chore (replaces the old `same_person_next_time` + `next_executor_id` mechanism). When set, the scoring algorithm is bypassed entirely.

### Modified Capabilities

- `chores-api`: The chore state resource no longer contains `next_executor_id`; it is replaced by a computed `next_executor` with score breakdowns. The API to set next executor manually is removed or replaced.
- `chores-ui`: The chores list view gains a per-person score column/display for each chore row.
- `same-person-next-time`: The existing same-person-next-time behavior (chore stays with same person) is now implemented via `fixed_executor_id` rather than a stored `next_executor_id`. The `same_person_next_time` flag on `chores` may be retained as a semantic marker but the executor storage moves to the new column.

## Impact

- **Database**: `chore_state` loses `next_executor_id`; gains `fixed_executor_id`.
- **API**: `chores_api.py` — chore state responses change shape; endpoint for setting next executor changes.
- **Business logic**: `chores_db.py` / `chores_api.py` — new scoring SQL query, new function to compute next executor.
- **UI**: `chores_ui.py` / `assets/chores_ui.html` — score display per person per chore.
- **Migrations**: `migrate_chores_data.py` — schema migration to add/remove columns.
- **Tests**: All test files referencing `next_executor_id` or the old scheduling logic need updating.
