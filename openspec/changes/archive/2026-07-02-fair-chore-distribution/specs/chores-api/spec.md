## MODIFIED Requirements

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

### Requirement: Chore state response includes computed next executor and person scores
The chore state object returned by `GET /api/v1/chores/summary` SHALL include a `next_executor_id` field (derived from the scoring query, or from `fixed_executor_id` for fixed-executor chores) and a `person_scores` array containing one entry per in-rotation person with their computed score. For fixed-executor chores, `person_scores` SHALL be an empty array.

#### Scenario: Summary returns next_executor_id for variable-executor chore
- **WHEN** a client calls `GET /api/v1/chores/summary`
- **THEN** each chore with `same_person_next_time: false` SHALL include a `next_executor_id` equal to the person with the lowest computed score

#### Scenario: Summary returns person_scores for variable-executor chore
- **WHEN** a client calls `GET /api/v1/chores/summary`
- **THEN** each chore with `same_person_next_time: false` SHALL include a `person_scores` array with one `{person_id, score}` entry per in-rotation person, sorted by score ascending

#### Scenario: Summary returns fixed_executor_id for fixed-executor chore
- **WHEN** a client calls `GET /api/v1/chores/summary` for a chore with `same_person_next_time: true`
- **THEN** `next_executor_id` SHALL equal the `fixed_executor_id` stored in `chore_state`

#### Scenario: person_scores empty for fixed-executor chore
- **WHEN** a client calls `GET /api/v1/chores/summary` for a chore with `same_person_next_time: true`
- **THEN** `person_scores` SHALL be an empty array

## REMOVED Requirements

### Requirement: Chore state stores next_executor_id
**Reason**: `next_executor_id` is now computed dynamically from execution history. Storing it would create stale data and conflict with the fair distribution algorithm.
**Migration**: Use `GET /api/v1/chores/summary` which returns a computed `next_executor_id`. For fixed-executor chores, use the `fixed_executor_id` field via the fixed-executor API.

## ADDED Requirements

### Requirement: Chores API supports setting fixed executor
The chores API SHALL expose an endpoint or field to set and clear `fixed_executor_id` on a chore state.

#### Scenario: Set fixed executor
- **WHEN** a client sends a PATCH or PUT request specifying `fixed_executor_id` for a chore
- **THEN** `chore_state.fixed_executor_id` SHALL be persisted with that person's ID

#### Scenario: Clear fixed executor
- **WHEN** a client sends a request with `fixed_executor_id: null` for a chore
- **THEN** `chore_state.fixed_executor_id` SHALL be set to null

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
