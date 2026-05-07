## ADDED Requirements

### Requirement: Person endpoints include in_rotation field
All API endpoints that read or write a `Person` resource SHALL include the `in_rotation` boolean field.

#### Scenario: GET person returns in_rotation
- **WHEN** a client calls `GET /api/v1/chores/people/{id}`
- **THEN** the response body SHALL include `"in_rotation": true` or `"in_rotation": false`

#### Scenario: GET people list returns in_rotation
- **WHEN** a client calls `GET /api/v1/chores/people`
- **THEN** every person object in the response SHALL include the `in_rotation` field

#### Scenario: POST person accepts in_rotation
- **WHEN** a client calls `POST /api/v1/chores/people` with `"in_rotation": false`
- **THEN** the created person SHALL have `in_rotation` set to `false`

#### Scenario: POST person defaults in_rotation to true
- **WHEN** a client calls `POST /api/v1/chores/people` without the `in_rotation` field
- **THEN** the created person SHALL have `in_rotation` set to `true`

#### Scenario: PUT person updates in_rotation
- **WHEN** a client calls `PUT /api/v1/chores/people/{id}` with `"in_rotation": false`
- **THEN** the person SHALL be updated to have `in_rotation = false`

## MODIFIED Requirements

### Requirement: POST executions advances next_executor using rotation pool
The `POST /api/v1/executions` endpoint SHALL use the `in_rotation = true`-filtered pool (ordered by `ordinal`) when computing `next_executor_id`, instead of rotating through all people in the database.

#### Scenario: Next executor is the next in_rotation person by ordinal
- **WHEN** a client calls `POST /api/v1/executions` with a valid `chore_id` and `executor_id`
- **AND** the chore has `same_person_next_time = false`
- **THEN** the response `updated_state.next_executor_id` SHALL be the ID of the person immediately after the current executor in the ordinal-ordered `in_rotation = true` pool

#### Scenario: Executor not in pool still advances to pool's first member
- **WHEN** the `executor_id` in the request corresponds to a person with `in_rotation = false`
- **THEN** `next_executor_id` SHALL be set to the first person in the `in_rotation = true` pool
