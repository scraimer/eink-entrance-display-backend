## Why

The current chore balancing happens in the browser and is implicitly retriggered when a chore is marked done. That makes the plan visible only in the management UI, and it means the backend does not own the same plan that the display or other clients should see.

We need the backend to persist a dated plan so the household can generate a plan for today or tomorrow ahead of time, including a separate tomorrow plan that can be prepared at midnight or on demand.

## What Changes

- **BREAKING**: Move chore balancing from client-side state into backend-owned, date-keyed plan records.
- Add support for calculating and storing a plan for a specific target date, including both today, tomorrow, and arbitrary ISO dates.
- Add a scheduled midnight refresh that prepares tomorrow's plan automatically.
- Add a manual trigger from the Management UI to calculate or refresh the plan for the selected date, with shortcuts for today and tomorrow.
- Change the mark-done flow so it records the execution without rebalancing the plan.
- Update rendering and API responses to read the persisted plan for the requested date.

## Capabilities

### New Capabilities
- `dated-chore-plans`: Persisted chore plans keyed by date, with backend-triggered calculation for today, tomorrow, or any ISO date and separate stored plans for each date.

### Modified Capabilities
- `chores-api`: Summary and execution flows change to read/write persisted plans instead of recalculating in the client; add a way to trigger plan generation for a chosen date.
- `chores-ui`: The Management tab gains controls to calculate the selected plan date, shows the active plan date explicitly, and the chores list stops relying on local rebalance logic.

## Impact

- Backend scheduling and chore plan persistence
- Chores API behavior for plan generation and execution updates
- Chores Management UI controls and plan display
- Rendering paths that consume the current plan
- Database schema for storing date-keyed plan state
- Tests covering today/tomorrow plan generation and mark-done behavior
