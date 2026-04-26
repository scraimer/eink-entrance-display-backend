## Context

The chores system tracks household tasks in a SQLite database. Each `Chore` has a `ChoreState` that records who did it last and who should do it next. When an execution is recorded, the system advances `next_executor_id` to the following person in the rotation. A `rankings` table holds per-person difficulty ratings for each chore.

Some chores are permanently assigned to one person (e.g., a task only one household member is able or willing to do). For these chores, advancing the executor after each execution is wrong, and showing them in difficulty rankings is meaningless.

## Goals / Non-Goals

**Goals:**
- Add `same_person_next_time: bool` (default `false`) to the `chores` table and ORM model.
- When marking a flagged chore as done, keep `next_executor_id` equal to the current executor.
- Exclude flagged chores from the rankings tab in the Chores UI.
- Expose the flag in all Chore API read and write endpoints.
- Allow toggling the flag from the chore create/edit form in the UI.
- Provide a DB migration that adds the column to existing rows with value `0`.

**Non-Goals:**
- Changing how rankings are stored or computed for non-flagged chores.
- Retroactively correcting historical `next_executor_id` values.
- Any changes to the audit log schema.

## Decisions

### 1. Column type: integer (0/1) not a native boolean
SQLite has no native boolean type. The existing schema uses `INTEGER` columns for similar flags. Store `same_person_next_time` as `INTEGER NOT NULL DEFAULT 0` with a `CHECK (same_person_next_time IN (0, 1))` constraint. SQLAlchemy's `Boolean` type handles this transparently.

*Alternative considered*: Use a TEXT column (`'yes'`/`'no'`). Rejected — integers are consistent with the rest of the schema and cheaper to compare.

### 2. Execution logic: pin executor, not skip
When an execution is recorded for a flagged chore, set `next_executor_id = executor_id` (the person who just did it). This keeps the state table consistent and requires no special-casing elsewhere — callers that read `next_executor_id` will simply always get the same person.

*Alternative considered*: Null out `next_executor_id` for flagged chores. Rejected — null requires every consumer to handle a missing executor.

### 3. Rankings filter: server-side exclusion
Exclude flagged chores in the Python code that builds the rankings payload (`/api/v1/chores/summary` and the rankings tab fetch), not in SQL. The table is small; a simple Python filter is cleaner and easier to test than a dynamic SQL filter.

### 4. UI: checkbox in chore form, badge in chore table
- Add a "Same person next time" checkbox to the chore create/edit inline form.
- Show a small badge/icon in the chores table row for flagged chores so it is discoverable at a glance.
- The rankings tab already filters server-side; no extra UI change needed there beyond the absence of flagged rows.

## Risks / Trade-offs

- **Migration risk**: Adding a non-null column with a default is safe in SQLite and requires no data copy. Risk is low.
- **No ranking rows for flagged chores**: Rankings can still exist in the DB for a chore that later gets flagged. They will simply be hidden in the UI. This is intentional.

## Migration Plan

1. Run `ALTER TABLE chores ADD COLUMN same_person_next_time INTEGER NOT NULL DEFAULT 0 CHECK (same_person_next_time IN (0, 1))` against the live `chores.sqlite`.
2. No data backfill required — all existing chores default to `0`.
3. Rollback: `ALTER TABLE chores DROP COLUMN same_person_next_time` (SQLite 3.35+). If on an older SQLite, recreate the table without the column.
4. Deploy updated application code after migration.
