## ADDED Requirements

### Requirement: Chore has same-person-next-time flag
A `Chore` SHALL have a boolean attribute `same_person_next_time` (default `false`) that pins the executor across executions.

#### Scenario: Flag defaults to false on creation
- **WHEN** a chore is created without specifying `same_person_next_time`
- **THEN** the chore's `same_person_next_time` value SHALL be `false`

#### Scenario: Flag can be set to true
- **WHEN** a chore is created or updated with `same_person_next_time: true`
- **THEN** the stored value SHALL be `true`

#### Scenario: Flag can be cleared
- **WHEN** a chore with `same_person_next_time: true` is updated with `same_person_next_time: false`
- **THEN** the stored value SHALL be `false`

### Requirement: Executor is not rotated for flagged chores
When an execution is recorded for a chore with `same_person_next_time: true`, the system SHALL keep `next_executor_id` equal to the executor who just completed the chore.

#### Scenario: Next executor unchanged after execution
- **WHEN** an execution is recorded for a chore with `same_person_next_time: true`
- **THEN** `chore_state.next_executor_id` SHALL equal the `executor_id` of that execution

#### Scenario: Next executor advances normally for non-flagged chores
- **WHEN** an execution is recorded for a chore with `same_person_next_time: false`
- **THEN** `chore_state.next_executor_id` SHALL be advanced to the next person in the rotation

### Requirement: Flagged chores excluded from rankings
Chores with `same_person_next_time: true` SHALL NOT appear in any rankings display or ranking-related response.

#### Scenario: Flagged chore absent from rankings list
- **WHEN** the rankings data is requested
- **THEN** chores with `same_person_next_time: true` SHALL NOT be included in the response

#### Scenario: Non-flagged chores remain in rankings
- **WHEN** the rankings data is requested
- **THEN** all chores with `same_person_next_time: false` SHALL still appear in the response
