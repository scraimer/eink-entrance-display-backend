## MODIFIED Requirements

### Requirement: Chore table shows per-person weighted scores for the selected plan date
The Chores UI chore list SHALL display, for each variable-executor chore row, the stored score of every in-rotation person for the selected plan date. Scores SHALL be sorted ascending (lowest first). Fixed-executor chores SHALL show the fixed executor's avatar with a lock or "fixed" label instead of scores.

Each score badge SHALL be interactive: clicking it SHALL toggle an inline breakdown revealing the formula components in the format `{execution_count} × 1000 − {days_since_last} = {score}`. When `days_since_last` is null the breakdown SHALL render the cap value (365) in place of `days_since_last`.

#### Scenario: Variable-executor chore shows all stored scores
- **WHEN** a chore with `same_person_next_time: false` is rendered in the chores table
- **THEN** the row SHALL display one score entry per in-rotation person showing the stored score for the selected plan date, sorted by score ascending

#### Scenario: Fixed-executor chore shows fixed executor label
- **WHEN** a chore with `same_person_next_time: true` is rendered in the chores table
- **THEN** the row SHALL show only the fixed executor's avatar/name and a "fixed" or lock indicator, with no score table

#### Scenario: Person with lowest score highlighted
- **WHEN** person scores are displayed for a chore
- **THEN** the entry for the person with the lowest score (the next executor) SHALL be visually distinguished

#### Scenario: Score badge expands to show breakdown
- **WHEN** the user clicks a score badge for person A on chore X where `execution_count` is 2 and `days_since_last` is 14
- **THEN** an inline breakdown SHALL appear showing `2 × 1000 − 14 = 1986`

#### Scenario: Score badge collapses breakdown on second click
- **WHEN** the breakdown is visible and the user clicks the score badge again
- **THEN** the breakdown SHALL be hidden

#### Scenario: Score breakdown renders cap for person who never did chore
- **WHEN** the user clicks a score badge for a person with `execution_count: 0` and `days_since_last: null`
- **THEN** the breakdown SHALL show `0 × 1000 − 365 = -365`
