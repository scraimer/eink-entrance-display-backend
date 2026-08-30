## Context

The chores UI is a single-page HTML/JS surface served from `assets/chores_ui.html` via `src/eink_backend/chores_ui.py`. Today, the primary completion control disappears or disables in states where the chore is already done, and the user has no direct way to reverse a mistaken completion from the same detail panel.

The backend already treats executions as the source of truth for completion history through `src/eink_backend/chores_api.py`, `src/eink_backend/chores_db.py`, and the audit layer. The new behavior should preserve that model rather than introducing a separate client-side completion flag.

## Goals / Non-Goals

**Goals:**
- Replace the completed-state disabled action with a visible "Mark as not Done" control.
- Make undo return the chore to the not-done state using server-side state.
- Keep the current "Mark as Done" and "Done by someone else?" flows for incomplete chores.
- Keep the UI consistent after either completion or undo by refreshing from the server.

**Non-Goals:**
- No scoring or rotation changes.
- No new plan-calculation behavior.
- No bulk undo, history browser, or edit-in-place execution management.
- No redesign of the chore detail panel beyond the state-dependent primary action.

## Decisions

1. **Model undo as a server-side reversal of the latest completion for the chore.**
   This keeps the completion history authoritative and avoids client-side toggles that can drift from persisted state. The UI only initiates the action; it does not try to reconstruct prior state locally.

2. **Recompute chore state from remaining execution history after undo.**
   That keeps the post-undo result aligned with how the system already derives future state from executions. An alternative would be to store a pre-completion snapshot and restore it directly, but that adds extra state and makes repeated changes harder to reason about.

3. **Render the primary action from server-provided completion state.**
   The detail panel should show either "Mark as Done" or "Mark as not Done" for a chore, never both. This keeps the controls mutually exclusive and avoids stale local assumptions after refresh.

4. **Hide the "Done by someone else?" link when the chore is already completed.**
   That link is only relevant when the user is creating a new execution. Once the chore is done, the panel should present a single undo action instead of two completion paths.

5. **Refresh the list after mutation instead of patching the DOM incrementally.**
   The existing completion flow already expects a server round-trip, and a refresh guarantees that the detail panel, summary data, and any dependent controls stay in sync.

## Risks / Trade-offs

- Recomputing state during undo is slightly more expensive than restoring a cached snapshot, but undo is a rare operation and correctness is more important than micro-optimizing it.
- If undo is allowed after other data changes, the backend must derive the restored state from persisted execution history instead of any UI state. That increases implementation discipline but reduces inconsistency risk.
- The UI state switch depends on a fresh summary response; the required refresh adds a small amount of latency but avoids stale rendering.

## Migration Plan

- No schema migration is expected if undo is implemented using existing execution and chore-state records.
- Add the reversal operation on the backend, then update the chores UI to show the alternate button state and call that operation.
- Validate the normal completion path, the new undo path, and the secondary-link visibility rules together.

## Open Questions

- Resolved: undo SHALL always target the most recent execution for the chore and SHALL never revert an earlier execution out of order.
