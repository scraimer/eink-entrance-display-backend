## ADDED Requirements

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
