## MODIFIED Requirements

### Requirement: Chore state response includes a persisted plan for the requested date
The chore state object returned by `GET /api/v1/chores/summary` SHALL include the stored plan for the requested plan date, including `plan_date`, `next_executor_id`, and `person_scores` for variable-executor chores. The returned values SHALL come from persisted plan records for that date rather than from client-side recalculation. The requested plan date MAY be today, tomorrow, or any valid ISO date. For fixed-executor chores, `person_scores` SHALL be an empty array.

#### Scenario: Summary returns the active plan date
- **WHEN** a client calls `GET /api/v1/chores/summary` for a specific plan date
- **THEN** the response SHALL include that `plan_date` in each chore entry

#### Scenario: Summary returns an arbitrary ISO date
- **WHEN** a client calls `GET /api/v1/chores/summary` for `plan_date=2026-07-20`
- **THEN** the response SHALL include plan data for `2026-07-20`

#### Scenario: Summary returns stored scores for variable-executor chore
- **WHEN** a client calls `GET /api/v1/chores/summary` for a variable-executor chore
- **THEN** the response SHALL include the stored `person_scores` for that plan date, sorted by score ascending

#### Scenario: Summary returns no scores for fixed-executor chore
- **WHEN** a client calls `GET /api/v1/chores/summary` for a chore with `same_person_next_time: true`
- **THEN** `person_scores` SHALL be an empty array

## ADDED Requirements

### Requirement: Chores API supports generating a plan for a chosen date
The chores API SHALL expose an operation that generates or refreshes a stored plan for a requested target date, including any valid ISO date.

#### Scenario: Generate plan for today
- **WHEN** a client requests plan generation for today
- **THEN** the API SHALL calculate and store the plan for today

#### Scenario: Generate plan for tomorrow
- **WHEN** a client requests plan generation for tomorrow
- **THEN** the API SHALL calculate and store the plan for tomorrow

#### Scenario: Generate plan for an arbitrary ISO date
- **WHEN** a client requests plan generation for `2026-07-20`
- **THEN** the API SHALL calculate and store the plan for `2026-07-20`

### Requirement: Chore execution recording does not rebalance stored plans
The `POST /api/v1/executions` endpoint SHALL record the execution and update execution-related chore state without recalculating any stored plan.

#### Scenario: Marking done does not refresh the plan
- **WHEN** a client posts a chore execution
- **THEN** the stored plan for today and tomorrow SHALL remain unchanged until an explicit plan refresh occurs
