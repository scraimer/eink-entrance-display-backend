## MODIFIED Requirements

### Requirement: Sub-panel trigger link visible when chore is scheduled and not completed
When a chore detail panel is shown, a next executor is assigned, and the chore is not already completed, the UI SHALL display a secondary text link that opens an alternative-executor sub-panel.

#### Scenario: Link visible when executor is scheduled for an incomplete chore
- **WHEN** the chore detail panel is expanded, `next_executor_id` is set, and the chore is not completed
- **THEN** a "Done by someone else?" text link SHALL be visible adjacent to the "Mark as Done" button

#### Scenario: Link not visible when chore is already completed
- **WHEN** the chore detail panel is expanded and the chore is already completed
- **THEN** the "Done by someone else?" link SHALL NOT be rendered

#### Scenario: Link not visible when no executor is scheduled
- **WHEN** the chore detail panel is expanded and `next_executor_id` is null
- **THEN** the "Done by someone else?" link SHALL NOT be rendered

### Requirement: Sub-panel contains a person selector and confirm/cancel controls
Clicking the "Done by someone else?" link SHALL reveal an inline sub-panel with a person dropdown, a confirm button, and a cancel link.

#### Scenario: Sub-panel opens on link click
- **WHEN** the user clicks the "Done by someone else?" link
- **THEN** an inline sub-panel SHALL appear containing a `<select>` populated with all known people and a "Confirm" button

#### Scenario: Sub-panel closed on cancel
- **WHEN** the user clicks the cancel control inside the sub-panel
- **THEN** the sub-panel SHALL be hidden without recording any execution

#### Scenario: Selecting a person and confirming records execution
- **WHEN** the user selects a person from the dropdown and clicks "Confirm"
- **THEN** `POST /executions` SHALL be called with the selected `executor_id` and the page SHALL refresh the chore list

#### Scenario: Confirm button disabled with no selection
- **WHEN** the sub-panel is open and no person is selected in the dropdown
- **THEN** the "Confirm" button SHALL be disabled
