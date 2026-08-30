## Why

When a chore is marked done, the next executor is left unchanged — someone must manually update it each time. This creates unnecessary friction and makes it easy to forget, leaving the next_executor stale or blank. Who participates in the rotation should be manageable from the UI without touching code or redeploying.

## What Changes

- Each person record gains a boolean `in_rotation` flag (default `true`).
- When an execution is recorded, the system automatically advances `next_executor_id` to the next person whose `in_rotation` flag is `true`, ordered by `ordinal`.
- The rotation wraps around: after the last eligible person it cycles back to the first.
- If `same_person_next_time` is `true` for the chore, the auto-advance is skipped.
- The Chores UI People management section gains a toggle to set `in_rotation` per person, so adding or removing someone from the rotation requires no code change.

## Capabilities

### New Capabilities

- `executor-rotation`: Automatically advance `next_executor_id` on chore state when an execution is recorded. The eligible pool is all people with `in_rotation = true`, ordered by `ordinal`.

### Modified Capabilities

- `chores-api`: The `Person` resource gains an `in_rotation` boolean field; people endpoints (GET, POST, PUT) must include it. The `POST /api/v1/executions` endpoint advances `next_executor_id` using the `in_rotation`-filtered pool.
- `chores-ui`: The People section of the Management tab gains an `in_rotation` toggle column per person.

## Impact

- `src/eink_backend/chores_db.py`: `Person` model gains `in_rotation` column
- `src/eink_backend/chores_api.py`: all person endpoints expose `in_rotation`; `perform_execution()` filters pool by `in_rotation = true`
- `assets/chores_ui.html`: People table and edit form gain `in_rotation` toggle
- Database migration: new column `in_rotation INTEGER NOT NULL DEFAULT 1` on `people` table
- No breaking API changes for existing chore/execution endpoints
