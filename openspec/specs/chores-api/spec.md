## ADDED Requirements

### Requirement: Chore endpoints include same_person_next_time field
All API endpoints that read or write a `Chore` resource SHALL include the `same_person_next_time` boolean field.

#### Scenario: GET chore returns flag
- **WHEN** a client calls `GET /api/v1/chores/{chore_id}`
- **THEN** the response body SHALL include `"same_person_next_time": true` or `"same_person_next_time": false`

#### Scenario: GET chores list returns flag
- **WHEN** a client calls `GET /api/v1/chores`
- **THEN** every chore object in the response SHALL include the `same_person_next_time` field

#### Scenario: POST chore accepts flag
- **WHEN** a client calls `POST /api/v1/chores` with `"same_person_next_time": true`
- **THEN** the created chore SHALL have `same_person_next_time` set to `true`

#### Scenario: POST chore defaults flag to false
- **WHEN** a client calls `POST /api/v1/chores` without the `same_person_next_time` field
- **THEN** the created chore SHALL have `same_person_next_time` set to `false`

#### Scenario: PUT chore updates flag
- **WHEN** a client calls `PUT /api/v1/chores/{chore_id}` with a new value for `same_person_next_time`
- **THEN** the chore SHALL be updated to reflect the new value

### Requirement: Rankings endpoint excludes flagged chores
The `GET /api/v1/chores/rankings` endpoint (or any endpoint returning ranking data) SHALL NOT return ranking entries for chores with `same_person_next_time: true`.

#### Scenario: Flagged chore missing from rankings response
- **WHEN** a client calls `GET /api/v1/chores/rankings`
- **THEN** the response SHALL NOT contain ranking entries for chores where `same_person_next_time` is `true`

### Requirement: Chores API supports bulk next due date updates
The chores API SHALL expose an endpoint that accepts multiple chore IDs and one target next due date to update in a single request.

#### Scenario: Request contains multiple chore IDs
- **WHEN** a client sends a bulk due date update request with two or more chore IDs
- **THEN** the API SHALL attempt to update each listed chore to the provided due date

#### Scenario: Request validation for required fields
- **WHEN** a client omits chore IDs or the due date from the bulk request
- **THEN** the API SHALL return a validation error response

#### Scenario: Request enforces maximum selection size
- **WHEN** a client sends more than 10 chore IDs in one bulk request
- **THEN** the API SHALL return a validation error response

#### Scenario: Request uses date-only due date
- **WHEN** a client sends the due date as a date-only value
- **THEN** the API SHALL accept the request without requiring a timestamp field

### Requirement: Chores API bulk updates are transactional
The chores API SHALL process bulk due date updates as all-or-nothing operations.

#### Scenario: All chores updated
- **WHEN** every requested chore is updated successfully
- **THEN** the API SHALL commit and return success for the bulk operation

#### Scenario: Any failure rolls back all updates
- **WHEN** one or more requested chore IDs cannot be updated
- **THEN** the API SHALL return a failure response and SHALL NOT persist updates for any requested chore
