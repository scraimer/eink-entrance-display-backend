## ADDED Requirements

### Requirement: Chore plans are persisted by plan date
The system SHALL store a separate chore plan for each target plan date so that plans for today and tomorrow can exist at the same time.

#### Scenario: Today and tomorrow plans coexist
- **WHEN** the system generates a plan for today and then generates a plan for tomorrow
- **THEN** both plans SHALL remain available independently

#### Scenario: Recomputing tomorrow does not overwrite today
- **WHEN** the system refreshes the plan for tomorrow
- **THEN** the stored plan for today SHALL remain unchanged

### Requirement: Plan calculation can target any ISO date
The system SHALL be able to generate a chore plan for any requested ISO date on demand, with today and tomorrow as common shortcuts.

#### Scenario: Manual trigger requests tomorrow
- **WHEN** an operator requests a plan calculation for tomorrow
- **THEN** the system SHALL generate and store the plan for tomorrow

#### Scenario: Manual trigger requests an arbitrary ISO date
- **WHEN** an operator requests a plan calculation for `2026-07-20`
- **THEN** the system SHALL generate and store the plan for `2026-07-20`

#### Scenario: Midnight job prepares tomorrow
- **WHEN** the scheduled midnight refresh runs
- **THEN** the system SHALL generate and store the plan for tomorrow

### Requirement: Plan generation is idempotent per date
Recalculating a plan for the same target date SHALL replace only that date's stored plan.

#### Scenario: Refreshing today keeps tomorrow intact
- **WHEN** the system recalculates the plan for today
- **THEN** the stored plan for tomorrow SHALL remain unchanged

### Requirement: Marking a chore done does not recalculate plans
Recording a chore execution SHALL not rebalance or regenerate any stored plan records.

#### Scenario: Execution leaves stored plans untouched
- **WHEN** a chore is marked done
- **THEN** the system SHALL save the execution without changing the stored plan for today or tomorrow

#### Scenario: Plan changes only after an explicit refresh
- **WHEN** a plan is viewed after a chore execution and before a plan refresh
- **THEN** the stored plan SHALL remain the same as before the execution
