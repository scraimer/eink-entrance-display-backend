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

### Requirement: Score breakdown components are included in person_scores entries
Each entry in the `person_scores` array returned by `GET /api/v1/chores/summary` SHALL include two additional fields alongside the existing `score` value:
- `execution_count`: the number of times the person executed this chore within the scoring window (last `SCORE_EXECUTION_WINDOW_DAYS` days).
- `days_since_last`: the number of days since the person last executed this chore, capped at `SCORE_RECENCY_CAP_DAYS`. SHALL be `null` when the person has never executed this chore (in which case the cap value is used in the formula).

The computed `score` SHALL continue to equal `execution_count × 1000 − min(days_since_last, SCORE_RECENCY_CAP_DAYS)` (or `execution_count × 1000 − SCORE_RECENCY_CAP_DAYS` when `days_since_last` is null).

#### Scenario: Summary includes breakdown for person who has done the chore
- **WHEN** a client calls `GET /api/v1/chores/summary` and person A has executed chore X twice in the last two years, most recently 14 days ago
- **THEN** person A's entry in `person_scores` for chore X SHALL include `execution_count: 2`, `days_since_last: 14`, and `score: 1986`

#### Scenario: Summary includes breakdown for person who has never done the chore
- **WHEN** a client calls `GET /api/v1/chores/summary` and person B has never executed chore X
- **THEN** person B's entry in `person_scores` for chore X SHALL include `execution_count: 0`, `days_since_last: null`, and `score: -365` (i.e. 0 × 1000 − 365)

#### Scenario: Fixed-executor chore still returns empty person_scores
- **WHEN** a client calls `GET /api/v1/chores/summary` for a chore with `same_person_next_time: true`
- **THEN** `person_scores` SHALL be an empty array (no breakdown exposed)
