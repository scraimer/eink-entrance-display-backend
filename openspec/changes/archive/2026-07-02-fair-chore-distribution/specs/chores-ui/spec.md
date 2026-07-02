## MODIFIED Requirements

### Requirement: Chore table shows same-person-next-time badge
The Chores UI chore list SHALL display a visible indicator on rows where `same_person_next_time` is `true`.

#### Scenario: Badge visible for flagged chore
- **WHEN** a chore with `same_person_next_time: true` is rendered in the chores table
- **THEN** the row SHALL show a badge or icon indicating it is a "same person" chore

#### Scenario: No badge for normal chore
- **WHEN** a chore with `same_person_next_time: false` is rendered in the chores table
- **THEN** no "same person" badge or icon SHALL be shown

### Requirement: Chore detail panel includes mark-as-done action
The chore detail panel SHALL include a primary "Mark as Done" button and a secondary "Done by someone else?" link. Both controls are only available when the computed next executor is non-null.

#### Scenario: Primary button marks chore done with computed next executor
- **WHEN** the user clicks "Mark as Done"
- **THEN** `POST /executions` SHALL be called with the computed `next_executor_id` as the executor

#### Scenario: Primary button disabled when no executor can be computed
- **WHEN** the computed `next_executor_id` is null (no in-rotation people available)
- **THEN** the "Mark as Done" button SHALL be disabled

#### Scenario: Secondary link opens alternative-executor sub-panel
- **WHEN** the user clicks "Done by someone else?"
- **THEN** an inline sub-panel SHALL appear (see `mark-done-by-other` spec for sub-panel requirements)

#### Scenario: Secondary link not shown when no executor can be computed
- **WHEN** the computed `next_executor_id` is null
- **THEN** the "Done by someone else?" link SHALL NOT be rendered

## ADDED Requirements

### Requirement: Chore table shows per-person weighted scores
The Chores UI chore list SHALL display, for each variable-executor chore row, the computed score of every in-rotation person. Scores SHALL be sorted ascending (lowest first). Fixed-executor chores SHALL show the fixed executor's avatar with a lock or "fixed" label instead of scores.

#### Scenario: Variable-executor chore shows all person scores
- **WHEN** a chore with `same_person_next_time: false` is rendered in the chores table
- **THEN** the row SHALL display one score entry per in-rotation person showing their computed score, sorted by score ascending

#### Scenario: Fixed-executor chore shows fixed executor label
- **WHEN** a chore with `same_person_next_time: true` is rendered in the chores table
- **THEN** the row SHALL show only the fixed executor's avatar/name and a "fixed" or lock indicator, with no score table

#### Scenario: Person with lowest score highlighted
- **WHEN** person scores are displayed for a chore
- **THEN** the entry for the person with the lowest score (the next executor) SHALL be visually distinguished

### Requirement: Chore create form includes same-person-next-time toggle
The inline chore create form in the Chores UI SHALL include a checkbox to set `same_person_next_time`.

#### Scenario: Checkbox present in create form
- **WHEN** the user opens the chore create form
- **THEN** a "Same person next time" checkbox SHALL be visible and unchecked by default

#### Scenario: Creating chore with checkbox checked
- **WHEN** the user checks "Same person next time" and submits the create form
- **THEN** the API request SHALL include `"same_person_next_time": true`

### Requirement: Fixed-executor chore shows selector for fixed person
When a chore has `same_person_next_time: true`, the Chores UI SHALL provide a way to select or change the fixed executor person (stored as `fixed_executor_id`).

#### Scenario: Fixed executor selector shown for flagged chore
- **WHEN** a chore with `same_person_next_time: true` is edited or viewed in the UI
- **THEN** a person selector control SHALL be visible allowing the user to set `fixed_executor_id`

#### Scenario: Saving fixed executor updates chore state
- **WHEN** the user selects a person and saves the fixed executor
- **THEN** the API SHALL be called to update `fixed_executor_id` on the chore state

### Requirement: Rankings tab excludes flagged chores
The rankings tab in the Chores UI SHALL NOT display chores with `same_person_next_time: true`.

#### Scenario: Flagged chore not visible in rankings tab
- **WHEN** the user opens the rankings tab
- **THEN** chores with `same_person_next_time: true` SHALL NOT appear in any rankings table or list

#### Scenario: Non-flagged chores visible in rankings tab
- **WHEN** the user opens the rankings tab
- **THEN** chores with `same_person_next_time: false` SHALL appear in the rankings tables

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
- **WHEN** the user selects chores and submits a bulk due date update
- **THEN** the API SHALL be called with the selected chore IDs and the chosen date

### Requirement: Chore edit form includes same-person-next-time toggle
The inline chore edit form SHALL display and allow editing of the `same_person_next_time` flag.

#### Scenario: Edit form reflects current flag value
- **WHEN** the user expands a chore row to edit a chore with `same_person_next_time: true`
- **THEN** the "Same person next time" checkbox SHALL be checked

#### Scenario: Saving edited flag value
- **WHEN** the user changes the "Same person next time" checkbox and saves
- **THEN** the API update request SHALL include the new value for `same_person_next_time`
