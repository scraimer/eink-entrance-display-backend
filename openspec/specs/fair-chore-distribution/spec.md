## ADDED Requirements

### Requirement: Next executor is computed from weighted execution history
For chores without a fixed executor, the system SHALL dynamically select the next executor using a score formula applied to execution history. The formula is: `score = (1000 × execution_count) + (−1 × min(days_since_last_execution_by_that_person, 365))`. The person with the lowest score SHALL be the next executor. Only people with `in_rotation = true` are eligible. A person who has never performed the chore SHALL receive an effective `days_since_last_execution` of 365 for scoring purposes.

Only executions within the last **two years (730 days)** SHALL be counted when computing `execution_count`. Executions older than this window SHALL be ignored. This window is controlled by the `SCORE_EXECUTION_WINDOW_DAYS` constant in the code.

#### Scenario: Person with fewest executions is chosen
- **WHEN** the next executor is computed for a chore
- **THEN** the person with the lowest execution count (among in-rotation people) SHALL have the lowest score and be selected

#### Scenario: Tie-break by recency
- **WHEN** two or more in-rotation people have the same execution count for a chore
- **THEN** the person whose last execution date is furthest in the past SHALL have the lower score and be selected

#### Scenario: Person never performed chore is highest priority
- **WHEN** an in-rotation person has no execution records for a chore
- **THEN** their score for that chore SHALL be lower than any person who has performed it at least once

#### Scenario: Recency advantage is capped at 365 days
- **WHEN** a person's last execution for a chore was more than 365 days ago
- **THEN** the score calculation SHALL use 365 days for the recency term, not the full elapsed number of days

#### Scenario: Executions older than two years do not count
- **WHEN** computing the execution count for a person and a chore
- **THEN** only executions with `execution_date` within the last 730 days SHALL be included in the count

#### Scenario: Out-of-rotation people excluded
- **WHEN** a person has `in_rotation = false`
- **THEN** they SHALL NOT appear in the next executor computation for any chore

### Requirement: Scores are computed in a single SQL query
The system SHALL compute all person × chore scores using a single SQL query (with subqueries as needed) against the `executions` table. The query SHALL produce one row per (person, chore) combination for all in-rotation people and all chores.

#### Scenario: Query covers all in-rotation people and all chores
- **WHEN** the scoring query executes
- **THEN** it SHALL return a row for every combination of in-rotation person and chore, including pairs with no execution history

#### Scenario: Scores returned for specific chore
- **WHEN** the scores for a specific chore are requested
- **THEN** the result SHALL contain one row per in-rotation person with their computed score

### Requirement: Next executor for a chore is derivable at any time
The system SHALL be able to determine the current next executor for any chore at any time by running the scoring query, without relying on a stored `next_executor_id` value.

#### Scenario: Next executor returned in summary response
- **WHEN** `GET /api/v1/chores/summary` is called
- **THEN** each chore entry SHALL include a `next_executor_id` field derived from the scoring query

#### Scenario: Next executor changes after a new execution is recorded
- **WHEN** an execution is recorded for a chore
- **THEN** a subsequent call to retrieve the chore summary SHALL reflect the updated scores and potentially a different next executor