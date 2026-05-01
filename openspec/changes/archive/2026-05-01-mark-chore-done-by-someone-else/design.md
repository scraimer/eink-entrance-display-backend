## Context

The Chores UI currently shows a "Mark as Done" button in the chore detail panel that always records the execution against the scheduled `next_executor_id`. Household members sometimes complete chores that were assigned to someone else, so the recorded executor is frequently wrong.

The existing `POST /executions` endpoint already accepts any `executor_id`, so no API change is needed. The entire implementation is confined to `src/eink_backend/chores_ui.py`, which is a single-file SPA rendered as an inline HTML/JS string.

## Goals / Non-Goals

**Goals:**
- Let the user select a different person before confirming "Mark as Done".
- Keep the existing quick-confirm path (the main "Mark as Done" button) unchanged.
- Work entirely within the existing single-file SPA structure; no build step, no external libraries.

**Non-Goals:**
- API changes — the existing `POST /executions` endpoint is sufficient.
- Changing how the next executor is computed after an execution.
- Persisting the "done-by" selection across page reloads.

## Decisions

### Decision: Inline sub-panel, not a modal

**Choice:** An inline expandable sub-panel rendered inside the existing `choreDetailHTML()` detail row.

**Rationale:** The SPA has no modal infrastructure. Adding a modal would require significant new CSS/JS. An inline panel is consistent with the existing expand/collapse pattern used for chore rows and person edit forms, requires minimal new markup, and keeps all state local to the row.

**Alternative considered:** Global modal overlay. Rejected — heavier, harder to wire without a component framework.

### Decision: Sub-panel triggered by a text link, not a second button

**Choice:** A small `<a href="#">` text link ("Done by someone else?") placed next to the "Mark as Done" button opens the sub-panel.

**Rationale:** The button is the primary action; the alternative-executor path is a secondary/corrective action. A text link communicates lower visual weight and is common for secondary flows in the same area (pattern seen in e-commerce "Use a different card?" links).

### Decision: Person list sourced from the already-loaded `people` array

**Choice:** The sub-panel's `<select>` is populated from the `people` global (already fetched when the Chores tab loads).

**Rationale:** No extra round-trip. The people list is always available by the time any chore row is expanded.

## Risks / Trade-offs

- **Risk:** Sub-panel state leaks between expansions — if a row is collapsed and re-expanded, the sub-panel may be visible.  
  **Mitigation:** Always render the sub-panel hidden by default; `toggleChoreDetail()` already replaces innerHTML on expand, so state is reset naturally.

- **Risk:** `people` array not yet populated when the sub-panel is opened.  
  **Mitigation:** The "Done by someone else?" link is only rendered when `canMarkDone` is true (i.e., `next_executor_id` exists), and `loadChores()` already calls `loadPeople()` indirectly. If `people` is empty, the select will be empty and the user cannot submit — acceptable degraded state.
