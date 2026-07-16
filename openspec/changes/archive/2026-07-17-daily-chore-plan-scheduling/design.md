## Context

Today the chores UI computes a “balanced” view in the browser by mutating the `/summary` payload after it loads. That rebalance is only visible in the Management tab, and `POST /executions` can retrigger it indirectly when the page reloads. The backend does not own the same plan that clients render.

The requested change makes plan calculation a backend concern with a date key, so the household can store one plan for today and a separate plan for tomorrow. The existing FastAPI app already has APScheduler and a chores database layer, so the change can fit into the current orchestration pattern without introducing a new service.

## Goals / Non-Goals

**Goals:**
- Persist chore plans by target date so today and tomorrow can coexist.
- Support explicit plan generation for today, tomorrow, or an arbitrary ISO date from the UI/API.
- Generate tomorrow’s plan automatically at midnight and seed both today and tomorrow on startup.
- Stop plan regeneration from happening as a side effect of marking a chore done.
- Keep the current weighted executor logic as the basis for plan generation.

**Non-Goals:**
- Reworking the weighted scoring algorithm itself.
- Adding arbitrary multi-day planning beyond today/tomorrow in this change.
- Changing the existing people/rotation model.
- Introducing a new external queue or worker system.

## Decisions

### 1. Store plan snapshots in a dedicated table keyed by date

**Decision:** Introduce a persisted plan table with one row per `plan_date`, and store the full computed plan snapshot for that date.

**Rationale:** A date-keyed snapshot naturally supports both today and tomorrow at the same time, and it avoids overwriting one plan when the other is refreshed. It also preserves the exact plan that the UI and e-ink renderers should use.

**Alternatives considered:**
- **Reuse `chore_state`** — rejected because that table represents per-chore execution state, not dated plan snapshots.
- **Keep plan data in memory** — rejected because the plan must survive process restarts and be shared across clients.
- **Normalize into many rows** — possible, but unnecessary for the current scale and harder to evolve.

### 2. Store the plan as a JSON snapshot

**Decision:** Store the rendered plan payload as JSON per plan date instead of fully normalizing every score row.

**Rationale:** The dataset is small, the consumer shape already exists in the API/UI, and a snapshot makes the plan easy to read back without joining several new tables. It also lets the plan schema evolve without a database migration every time the display shape changes.

**Alternatives considered:**
- **Normalized plan items table** — better for SQL queries, but higher schema and query complexity for little benefit here.
- **Derive everything on read** — rejected because the plan needs to be stable and shared across clients.

### 3. Make plan generation an explicit backend operation

**Decision:** Add an explicit plan-generation operation that accepts a target date (`today`, `tomorrow`, or any ISO date) and writes the resulting snapshot.

**Rationale:** The user wants manual generation from the Management UI and a midnight refresh for tomorrow. Explicit generation keeps that behavior predictable and prevents accidental recalculation during unrelated actions like marking chores done.

**Alternatives considered:**
- **Generate on every execution** — rejected because the user explicitly does not want rebalance side effects on `mark done`.
- **Generate lazily on read** — rejected because the plan should be a stored daily artifact, not a transient view.

### 4. Use the scheduler only for tomorrow’s daily refresh

**Decision:** Add a midnight cron job that refreshes tomorrow’s plan automatically, and seed both today and tomorrow on startup so the UI has an immediate persisted snapshot.

**Rationale:** Tomorrow’s plan is the one that benefits most from being prepared before the day starts. Keeping today manual gives operators control if the household’s chores change during the day.

**Alternatives considered:**
- **Refresh both today and tomorrow at midnight** — viable, but today’s plan can become stale if operators intentionally adjust it later in the day.
- **Refresh only on demand** — rejected because the user wants a daily automatic preparation path.

### 5. Read plan data from the persisted snapshot in API/UI paths

**Decision:** Update summary and display paths to read the stored plan for the requested date rather than recomputing locally.

**Rationale:** The same persisted snapshot must power the API, Management UI, and rendering path so they all show the same answer. This also removes the current browser-only rebalance behavior.

**Alternatives considered:**
- **Keep client-side rebalance as a fallback** — rejected because it would reintroduce divergent behavior between clients.
- **Recompute on every request** — rejected because the plan should be a durable daily artifact.

## Risks / Trade-offs

- [Stale plan after mid-day changes] → Operators may need to manually refresh today’s plan after chore or people changes.
- [JSON snapshot is less queryable] → Acceptable for the current small dataset and display-driven use case.
- [Timezone boundary mistakes] → Use the app’s local timezone consistently for `plan_date` and the midnight scheduler.
- [Cold-start missing plan] → Seed today and tomorrow on startup so the UI has a usable default immediately.

## Migration Plan

1. Add the new plan storage table and generation service.
2. Backfill first snapshots for today and tomorrow so the UI and renderers can read persisted data immediately after deploy.
3. Schedule the midnight job to generate tomorrow’s plan going forward.
4. Update API and UI consumers to read the stored snapshot by date.
5. Remove the client-side rebalance path once the backend path is authoritative.

Rollback would restore the previous client-side flow and drop the new plan table after any required data export.

## Open Questions

None.
