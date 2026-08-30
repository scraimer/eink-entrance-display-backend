## ADDED Requirements

### Requirement: Person has an in_rotation flag
Each person record SHALL have a boolean `in_rotation` field that controls whether that person is included in the automatic executor rotation pool.

#### Scenario: Default value is true
- **WHEN** a new person is created without specifying `in_rotation`
- **THEN** `in_rotation` SHALL default to `true`

#### Scenario: Flag can be set to false at creation
- **WHEN** a client creates a person with `"in_rotation": false`
- **THEN** the created person SHALL have `in_rotation = false`

#### Scenario: Flag can be updated
- **WHEN** a client calls `PUT /api/v1/chores/people/{id}` with `"in_rotation": false`
- **THEN** the person record SHALL be updated and subsequent rotation pool queries SHALL exclude that person

### Requirement: Rotation pool is all in_rotation=true people ordered by ordinal
When determining the eligible pool for the next executor, the system SHALL query only the people with `in_rotation = true`, ordered by `ordinal` ascending.

#### Scenario: Only in_rotation members are candidates
- **WHEN** an execution is recorded and `same_person_next_time` is `false`
- **THEN** `next_executor_id` SHALL be set to a person with `in_rotation = true`

#### Scenario: Person with in_rotation=false is excluded
- **WHEN** a person has `in_rotation = false`
- **AND** an execution is recorded for any chore
- **THEN** that person SHALL NOT be selected as the next executor

#### Scenario: Empty pool is an error
- **WHEN** all people have `in_rotation = false`
- **AND** a client calls `POST /api/v1/executions`
- **THEN** the response SHALL be HTTP 400 with a message indicating no people are in the rotation pool

### Requirement: Rotation wraps around after the last pool member
After the last person in the pool completes an execution, the next executor SHALL be the first person in the pool.

#### Scenario: Wrap-around from last to first
- **WHEN** the current executor is the last person in the `in_rotation = true` pool (highest ordinal)
- **AND** `same_person_next_time` is `false`
- **THEN** `next_executor_id` SHALL be set to the first person in the pool (lowest ordinal)

### Requirement: same_person_next_time suppresses rotation
When a chore has `same_person_next_time` set to `true`, auto-advance SHALL NOT change the executor.

#### Scenario: Pinned chore keeps its executor
- **WHEN** an execution is recorded for a chore with `same_person_next_time = true`
- **THEN** `next_executor_id` SHALL remain set to the same person who just executed the chore
