## ADDED Requirements

### Requirement: Bulk next due date update operation
The system SHALL provide an operation that updates the next due date for multiple chores in one request.

#### Scenario: Successful bulk update
- **WHEN** a client submits a bulk update request with one valid due date and multiple valid chore IDs
- **THEN** the system SHALL update each listed chore to the provided next due date

#### Scenario: Reject empty chore selection
- **WHEN** a client submits a bulk update request without any chore IDs
- **THEN** the system SHALL reject the request with a validation error

#### Scenario: Reject invalid due date
- **WHEN** a client submits a bulk update request with an invalid due date value
- **THEN** the system SHALL reject the request with a validation error

#### Scenario: Reject request above maximum selection size
- **WHEN** a client submits a bulk update request with more than 10 chore IDs
- **THEN** the system SHALL reject the request with a validation error

### Requirement: Bulk update uses all-or-nothing semantics
The system SHALL apply bulk next due date updates transactionally so either all requested chores are updated or none are updated.

#### Scenario: One failing chore aborts entire update
- **WHEN** any requested chore cannot be updated in a bulk operation
- **THEN** no requested chore SHALL have its next due date changed

### Requirement: Bulk update request uses date-only due date format
The system SHALL accept the target due date as a date-only value and MUST NOT require a timestamp.

#### Scenario: Date-only input accepted
- **WHEN** a client sends a valid date-only due date value
- **THEN** the request SHALL be accepted without requiring time or timezone fields