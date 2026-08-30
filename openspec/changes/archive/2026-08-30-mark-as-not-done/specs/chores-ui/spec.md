## MODIFIED Requirements

### Requirement: Chore detail panel includes completion controls
The chore detail panel SHALL display a primary "Mark as Done" button when the chore is not yet completed. When the chore is already completed, the primary control SHALL be replaced by a visible "Mark as not Done" button in the same location. The "Done by someone else?" link SHALL only be visible when the chore is not yet completed and a next executor is scheduled. The primary completion button for an incomplete chore SHALL be disabled when no next executor is scheduled.

#### Scenario: Incomplete chore with next executor shows completion action
- **WHEN** a chore detail panel is shown for a chore that is not yet completed and `next_executor_id` is set
- **THEN** the panel SHALL show a "Mark as Done" button that calls `POST /executions` with the `next_executor_id` as the executor
- **AND THEN** the "Done by someone else?" link SHALL be visible

#### Scenario: Incomplete chore without next executor disables completion action
- **WHEN** a chore detail panel is shown for a chore that is not yet completed and `next_executor_id` is null
- **THEN** the panel SHALL show a disabled "Mark as Done" button
- **AND THEN** the "Done by someone else?" link SHALL NOT be rendered

#### Scenario: Completed chore shows undo action instead of completion action
- **WHEN** a chore detail panel is shown for a chore that is already completed
- **THEN** the panel SHALL show a "Mark as not Done" button in place of the "Mark as Done" button
- **AND THEN** the "Done by someone else?" link SHALL NOT be rendered

#### Scenario: Undo action reverses the completion and refreshes the list
- **WHEN** the user clicks "Mark as not Done" for a completed chore
- **THEN** the UI SHALL call the reversal operation for that chore
- **AND THEN** the chore list SHALL refresh so the chore appears not done again
