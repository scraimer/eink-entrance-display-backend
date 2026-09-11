# chores-api Specification

## Purpose

Define the HTTP API behavior for chore state, plan generation, execution recording, scoring, and reversal.

## Requirements

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

### Requirement: Chore execution reversal restores the previous chore state
The chores API SHALL support reversing the latest recorded completion for a chore. The reversal operation SHALL remove the execution record associated with the completion, restore the `chore_state` fields updated by that completion, and restore the chore's visibility in any affected stored plan snapshot so the chore appears not done again.

#### Scenario: Reversing a completion restores the chore to not done
- **WHEN** a client requests a reversal for a chore that was previously marked done
- **THEN** the execution record for that completion SHALL be removed
- **AND THEN** the affected chore SHALL appear not done again in summary responses

#### Scenario: Reversal restores the prior executor and execution date fields
- **WHEN** a client reverses a completion for a chore that had updated `last_executor_id` and `last_execution_date`
- **THEN** the chore state SHALL return to the values that were in place before that completion

#### Scenario: Reversal fails when there is no completion to undo
- **WHEN** a client requests reversal for a chore that has no reversible completion
- **THEN** the API SHALL return an error and leave the chore state unchanged
