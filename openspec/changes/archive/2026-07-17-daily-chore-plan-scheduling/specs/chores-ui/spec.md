## MODIFIED Requirements

### Requirement: Chore table shows per-person weighted scores for the selected plan date
The Chores UI chore list SHALL display, for each variable-executor chore row, the stored score of every in-rotation person for the selected plan date. Scores SHALL be sorted ascending (lowest first). Fixed-executor chores SHALL show the fixed executor's avatar with a lock or "fixed" label instead of scores.

#### Scenario: Variable-executor chore shows all stored scores
- **WHEN** a chore with `same_person_next_time: false` is rendered in the chores table
- **THEN** the row SHALL display one score entry per in-rotation person showing the stored score for the selected plan date, sorted by score ascending

#### Scenario: Fixed-executor chore shows fixed executor label
- **WHEN** a chore with `same_person_next_time: true` is rendered in the chores table
- **THEN** the row SHALL show only the fixed executor's avatar/name and a "fixed" or lock indicator, with no score table

#### Scenario: Person with lowest score highlighted
- **WHEN** person scores are displayed for a chore
- **THEN** the entry for the person with the lowest score (the next executor) SHALL be visually distinguished

### Requirement: Chore detail panel includes mark-as-done action
The chore detail panel SHALL include a primary "Mark as Done" button and a secondary "Done by someone else?" link. Both controls are only available when a next executor is scheduled.

#### Scenario: Primary button marks chore done with scheduled executor
- **WHEN** the user clicks "Mark as Done"
- **THEN** `POST /executions` SHALL be called with the `next_executor_id` as the executor

#### Scenario: Primary button disabled when no executor scheduled
- **WHEN** `next_executor_id` is null
- **THEN** the "Mark as Done" button SHALL be disabled

#### Scenario: Secondary link opens alternative-executor sub-panel
- **WHEN** the user clicks "Done by someone else?"
- **THEN** an inline sub-panel SHALL appear (see `mark-done-by-other` spec for sub-panel requirements)

#### Scenario: Secondary link not shown when no executor scheduled
- **WHEN** `next_executor_id` is null
- **THEN** the "Done by someone else?" link SHALL NOT be rendered

## ADDED Requirements

### Requirement: Management UI can trigger plan calculation for the selected plan date
The Chores UI Management tab SHALL show the currently selected plan date explicitly and provide refresh controls for that date, with shortcuts for today and tomorrow.

#### Scenario: Today plan trigger is visible
- **WHEN** the user opens the Management tab
- **THEN** a control to calculate the plan for today SHALL be visible

#### Scenario: Tomorrow plan trigger is visible
- **WHEN** the user opens the Management tab
- **THEN** a control to calculate the plan for tomorrow SHALL be visible

#### Scenario: Selected plan date is visible
- **WHEN** the user opens the Management tab
- **THEN** the currently selected plan date SHALL be shown explicitly

#### Scenario: Triggering the selected plan calls the API
- **WHEN** the user requests a plan calculation for the selected date
- **THEN** the UI SHALL call the API to generate the stored plan for that date
