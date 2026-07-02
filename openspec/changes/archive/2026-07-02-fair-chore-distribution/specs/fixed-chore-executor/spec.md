## ADDED Requirements

### Requirement: Chore state stores a fixed executor
A `chore_state` row SHALL have a `fixed_executor_id` column (nullable FK → people) that designates the one person who always performs this chore. When `fixed_executor_id` is set, the weighted scoring algorithm SHALL be bypassed for that chore.

#### Scenario: Fixed executor always selected as next executor
- **WHEN** a chore has `fixed_executor_id` set to a person's ID
- **THEN** the next executor for that chore SHALL always be that person, regardless of execution history

#### Scenario: Fixed executor can be cleared
- **WHEN** `fixed_executor_id` is set to null on a chore state
- **THEN** the chore SHALL revert to the weighted scoring algorithm for next executor selection

#### Scenario: Fixed executor column allows null
- **WHEN** a chore state has no fixed executor
- **THEN** `fixed_executor_id` SHALL be null

### Requirement: Fixed executor is set and cleared via the API
The API SHALL provide a way to set or clear the `fixed_executor_id` on a chore state. This is the replacement for the old `next_executor_id` setter for fixed-executor chores.

#### Scenario: Set fixed executor via API
- **WHEN** a client sends a request to set the fixed executor for a chore
- **THEN** `chore_state.fixed_executor_id` SHALL be updated to the provided person ID

#### Scenario: Clear fixed executor via API
- **WHEN** a client sends a request to clear the fixed executor (null value)
- **THEN** `chore_state.fixed_executor_id` SHALL be set to null

### Requirement: Migration populates fixed_executor_id from old data
The database migration SHALL copy the old `next_executor_id` value into `fixed_executor_id` for every chore whose `same_person_next_time` flag is true before removing `next_executor_id`.

#### Scenario: Fixed executor populated from old next_executor_id
- **WHEN** the migration runs on a database containing chores with `same_person_next_time = true` and a stored `next_executor_id`
- **THEN** `chore_state.fixed_executor_id` SHALL equal the old `next_executor_id` for those chores

#### Scenario: Variable-executor chores unaffected
- **WHEN** the migration runs on a chore with `same_person_next_time = false`
- **THEN** `fixed_executor_id` SHALL be null regardless of the old `next_executor_id` value
