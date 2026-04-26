## Why

Some chores are permanently tied to one person — regardless of the normal rotation logic. These chores should never cycle to a new executor when marked done, and they are irrelevant to difficulty rankings because there is no choice about who performs them. Currently the system has no way to express this, so manual workarounds are needed after every execution.

## What Changes

- Add a `same_person_next_time` boolean flag to the `chores` table (default `false`).
- When a chore with this flag is marked as done, the `next_executor_id` in `chore_state` must remain the same person who just executed it — the normal rotation is skipped.
- Chores flagged `same_person_next_time` are excluded from the rankings display in the Chores UI and from any ranking-related API responses.
- The Chores UI must expose a way to set/clear this flag when creating or editing a chore.
- The Chores REST API must expose the flag in all chore read/write endpoints.

## Capabilities

### New Capabilities

- `same-person-next-time`: A chore-level flag that pins the executor across executions and hides the chore from difficulty rankings.

### Modified Capabilities

- `chores-api`: Chore read/write endpoints must include the new `same_person_next_time` field.
- `chores-ui`: The chore management UI must render and allow editing the flag; rankings views must exclude flagged chores.

## Impact

- **Database**: `chores` table gains one column; existing rows default to `false`. A migration is required.
- **`chores_db.py`**: `Chore` ORM model gains the new column.
- **`chores_api.py`**: All Pydantic schemas and endpoint handlers that touch `Chore` need updating.
- **`chores_ui.py`**: Rankings rendering must filter out flagged chores; chore create/edit forms must include the toggle.
- **No breaking API changes** — the new field is optional with a safe default.
