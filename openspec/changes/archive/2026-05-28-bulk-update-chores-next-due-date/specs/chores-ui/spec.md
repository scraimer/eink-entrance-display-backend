## ADDED Requirements

### Requirement: Chores table supports multi-select for bulk actions
The Chores UI SHALL let users select multiple chores for bulk operations.

#### Scenario: Select multiple chores
- **WHEN** the user checks selection controls for more than one chore row
- **THEN** all selected chores SHALL be tracked in UI selection state

#### Scenario: Clear selection
- **WHEN** the user clears selection (manually or via a clear-selection control)
- **THEN** no chores SHALL remain selected

### Requirement: Chores UI applies one due date to selected chores
The Chores UI SHALL provide one date input and one action that applies that date to all currently selected chores.

#### Scenario: Submit bulk due date update
- **WHEN** at least one chore is selected and the user chooses a valid due date then submits the bulk action
- **THEN** the UI SHALL call the bulk next-due-date API with selected chore IDs and the chosen due date

#### Scenario: Date picker submits date-only value
- **WHEN** the user selects a due date for bulk update
- **THEN** the UI SHALL submit a date-only value to the bulk API

#### Scenario: Prevent submit without selection
- **WHEN** no chores are selected
- **THEN** the bulk update action control SHALL be disabled or blocked

#### Scenario: Refresh rows after bulk update
- **WHEN** the bulk update request completes successfully
- **THEN** the chores table SHALL show the updated next due date for all updated chores

#### Scenario: Show transactional failure feedback
- **WHEN** the bulk update request fails
- **THEN** the UI SHALL show that no selected chores were updated

#### Scenario: Prevent selecting more than maximum
- **WHEN** the user attempts to select more than 10 chores for bulk update
- **THEN** the UI SHALL block submit and provide a validation message about the 10-item limit
