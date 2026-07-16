## 1. Persist dated chore plans

- [x] 1.1 Add a database table for date-keyed chore plan snapshots with storage for the computed plan payload and timestamps.
- [x] 1.2 Add migration/backfill logic so the current day and tomorrow can be seeded into persisted plan storage on deployment.
- [x] 1.3 Add database helpers for reading, writing, and replacing a plan for a specific target date.

## 2. Generate plans in the backend

- [x] 2.1 Extract the current balancing logic into a backend service that can generate a stored plan for an explicit target date.
- [x] 2.2 Make the generator support today, tomorrow, and arbitrary ISO dates as valid targets.
- [x] 2.3 Add a midnight scheduler job that automatically refreshes tomorrow’s plan.
- [x] 2.4 Ensure recording an execution updates execution state only and does not regenerate any stored plan.

## 3. Serve stored plans through the API

- [x] 3.1 Update summary responses to read the stored plan for the requested date instead of recomputing it in the client.
- [x] 3.2 Add an API operation for manually generating or refreshing the plan for the selected ISO date, with today/tomorrow shortcuts in the UI.
- [x] 3.3 Keep fixed-executor and ranking behavior consistent with the persisted plan snapshot.

## 4. Update the Management UI

- [x] 4.1 Remove the client-side rebalance path from the chores list rendering flow.
- [x] 4.2 Add controls in the Management tab to generate the plan for today or tomorrow.
- [x] 4.3 Show which plan date is currently being displayed so operators know exactly which snapshot they are editing.

## 5. Verify end-to-end behavior

- [x] 5.1 Add tests for generating and reading separate plans for today and tomorrow.
- [x] 5.2 Add tests that confirm marking a chore done does not trigger a plan rebuild.
- [x] 5.3 Add tests for the midnight job and manual trigger path producing the same stored format.
