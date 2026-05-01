## MODIFIED Requirements

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
