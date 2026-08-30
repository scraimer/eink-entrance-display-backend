## Why

The chores UI currently leaves completed chores in a dead-end state: once a chore is marked done, the primary action is disabled instead of offering a direct way to undo the completion. That makes routine correction flows slower and pushes users toward manual database or API cleanup when they need to reverse a mistaken completion.

## What Changes

- Replace the disabled completed-state primary action with a visible "Mark as not Done" action for chores that are already completed.
- Keep the existing "Mark as Done" action for chores that are not yet completed.
- When the new undo action is clicked, revert the completion state so the chore appears not done again and can be completed normally later.
- Preserve the current alternative-executor flow for chores that are not yet completed.

## Capabilities

### New Capabilities
- <!-- None -->

### Modified Capabilities
- `chores-ui`: The chore detail panel and completion controls are changing to support an undo state instead of disabling the action after completion.
- `mark-done-by-other`: The trigger link must stay hidden when the primary control is replaced by "Mark as not Done".
- `chores-api`: The execution API must support reversing a completion so the UI can restore a chore to the not-done state.

## Impact

- `assets/chores_ui.html` — completion button rendering and client-side behavior
- `src/eink_backend/chores_api.py` — execution reversal endpoint or equivalent mutation path
- `src/eink_backend/chores_db.py` — execution/state consistency and any data repair needed when a completion is reverted
- `src/eink_backend/chores_audit.py` — audit logging for the undo flow
