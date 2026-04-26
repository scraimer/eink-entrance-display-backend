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
