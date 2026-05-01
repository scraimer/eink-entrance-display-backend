## Why

When a chore gets done, it is always recorded against the assigned executor. In practice, a different household member often completes a chore (e.g., someone covers for the assigned person), and the system currently has no way to credit the right person without first reassigning the chore. This leads to inaccurate execution history.

## What Changes

- The chore detail panel in the Chores UI gains a "Done by someone else?" text link below the "Mark as Done" button.
- Clicking that link opens an inline sub-panel with a person selector and a confirm button.
- Confirming records the execution against the chosen person instead of the scheduled executor.
- The sub-panel can be dismissed without taking any action.
- No API changes are required; the existing `POST /executions` endpoint already accepts any `executor_id`.

## Capabilities

### New Capabilities

- `mark-done-by-other`: Inline sub-panel in the chore detail view that lets the user select an alternative executor when marking a chore as done.

### Modified Capabilities

- `chores-ui`: The chore detail panel gains new interactive UI elements (sub-panel trigger link, person dropdown, confirm/cancel controls).

## Impact

- `src/eink_backend/chores_ui.py` — inline HTML/JS changes to `choreDetailHTML()` and `markDone()`.
- No database schema or API changes required.
- No new dependencies.
