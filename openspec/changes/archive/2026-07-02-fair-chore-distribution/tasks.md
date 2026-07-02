## 1. Database Migration

- [x] 1.1 Add `fixed_executor_id` column (nullable FK → people, ON DELETE SET NULL) to `chore_state` in `migrate_db()` in `chores_db.py`
- [x] 1.2 Update the SQLAlchemy `ChoreState` model to add `fixed_executor_id` column and relationship
- [x] 1.3 Remove `next_executor_id` column from the SQLAlchemy `ChoreState` model and related `Person.next_executor_chores` relationship
- [x] 1.4 Write migration logic (in `migrate_db()`) to: (a) copy `next_executor_id` → `fixed_executor_id` for chores with `same_person_next_time = true`, then (b) rebuild `chore_state` without `next_executor_id` using SQLite table-rename approach
- [x] 1.5 Update `ChoreStateData` dataclass in `chores_db.py` to replace `next_executor_id` with `fixed_executor_id`
- [x] 1.6 Update `chores-database-schema.md` to reflect the schema change (remove `next_executor_id`, add `fixed_executor_id`)

## 2. Scoring Query

- [x] 2.1 Write a `compute_chore_scores(session)` function in `chores_db.py` (or `chores_api.py`) that executes the scoring SQL and returns a list of `(person_id, chore_id, score)` tuples using a 365-day cap on the recency term
- [x] 2.2 Write a `get_next_executor_id(chore_id, session)` helper that returns the person_id with the lowest score for a given chore (or `fixed_executor_id` if `same_person_next_time` is true)
- [ ] 2.3 Add unit tests for the scoring formula: fewest executions wins, tie-break by oldest last execution, recency capped at 365 days, never-performed person scores lowest, out-of-rotation excluded

## 3. API Layer

- [x] 3.1 Update `ChoreStateResponse` Pydantic model: remove `next_executor_id`, add `fixed_executor_id`; add `person_scores: List[{person_id, score}]` field
- [x] 3.2 Update `get_chores_summary()` in `chores_api.py` to: (a) run the scoring query, (b) populate `next_executor_id` (computed) and `person_scores` per chore, (c) use `fixed_executor_id` for fixed-executor chores
- [x] 3.3 Remove or update the `POST /executions/next-executor` endpoint (the old `ExecutionNextExecutorRequest` that set `next_executor_id`) — replace with an endpoint that sets `fixed_executor_id`
- [ ] 3.4 Add `PATCH /chores/{chore_id}/state` (or equivalent) endpoint to set/clear `fixed_executor_id`
- [x] 3.5 Update all other route handlers that reference `state.next_executor_id` (e.g. person cascade delete path) to use `fixed_executor_id` or remove the reference
- [ ] 3.6 Update `chores-api-reference.md` to document the new response shape and the fixed-executor endpoint

## 4. UI Updates

- [ ] 4.1 Update the `GET /api/v1/chores/summary` response handling in `assets/chores_ui.html` JavaScript to read `person_scores` and `fixed_executor_id` instead of `next_executor_id` from the state object
- [ ] 4.2 Add score display to each variable-executor chore row: render a compact list of `(avatar/name, score)` per in-rotation person, sorted by score ascending, with the lowest-score person highlighted
- [ ] 4.3 Add a "fixed" / lock label for fixed-executor chore rows instead of the score table
- [ ] 4.4 Add a person selector control to the chore edit form for setting `fixed_executor_id` when `same_person_next_time` is true; wire it to the new API endpoint
- [ ] 4.5 Update the "Mark as Done" and "Done by someone else?" logic to use the computed `next_executor_id` from the summary response (no behavioral change needed if the API provides the computed value)

## 5. Execution Recording

- [x] 5.1 Verify that the `POST /executions` handler no longer writes to `next_executor_id` after recording an execution (since next executor is now computed)
- [x] 5.2 Ensure `same_person_next_time` chores still keep the correct fixed executor after an execution is recorded (no mutation of `fixed_executor_id` should occur)

## 6. Tests

- [x] 6.1 Update existing tests that assert on `next_executor_id` in chore state to instead check the computed `next_executor_id` in the summary response
- [ ] 6.2 Add integration test: multiple executions recorded → verify the person with fewest executions becomes next executor
- [ ] 6.3 Add integration test: tie-break by recency — two people with equal count, the one with the older last execution is selected
- [x] 6.4 Add integration test: `same_person_next_time = true` chore always returns `fixed_executor_id` as next executor regardless of execution history
- [ ] 6.5 Add integration test: person with `in_rotation = false` is never selected as next executor
- [ ] 6.6 Run full test suite and fix any regressions
