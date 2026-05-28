## ADDED Requirements

### Requirement: Chore table shows same-person-next-time badge
The Chores UI chore list SHALL display a visible indicator on rows where `same_person_next_time` is `true`.

#### Scenario: Badge visible for flagged chore
- **WHEN** a chore with `same_person_next_time: true` is rendered in the chores table
- **THEN** the row SHALL show a badge or icon indicating it is a "same person" chore

#### Scenario: No badge for normal chore
- **WHEN** a chore with `same_person_next_time: false` is rendered in the chores table
- **THEN** no "same person" badge or icon SHALL be shown

### Requirement: Chore create form includes same-person-next-time toggle
The inline chore create form in the Chores UI SHALL include a checkbox to set `same_person_next_time`.

#### Scenario: Checkbox present in create form
- **WHEN** the user opens the chore create form
- **THEN** a "Same person next time" checkbox SHALL be visible and unchecked by default

#### Scenario: Creating chore with checkbox checked
- **WHEN** the user checks "Same person next time" and submits the create form
- **THEN** the API request SHALL include `"same_person_next_time": true`

### Requirement: Chore edit form includes same-person-next-time toggle
The inline chore edit form SHALL display and allow editing of the `same_person_next_time` flag.

#### Scenario: Edit form reflects current flag value
- **WHEN** the user expands a chore row to edit a chore with `same_person_next_time: true`
- **THEN** the "Same person next time" checkbox SHALL be checked

#### Scenario: Saving edited flag value
- **WHEN** the user changes the "Same person next time" checkbox and saves
- **THEN** the API update request SHALL include the new value for `same_person_next_time`

### Requirement: Rankings tab excludes flagged chores
The rankings tab in the Chores UI SHALL NOT display chores with `same_person_next_time: true`.

#### Scenario: Flagged chore not visible in rankings tab
- **WHEN** the user opens the rankings tab
- **THEN** chores with `same_person_next_time: true` SHALL NOT appear in any rankings table or list

#### Scenario: Non-flagged chores visible in rankings tab
- **WHEN** the user opens the rankings tab
- **THEN** chores with `same_person_next_time: false` SHALL appear in the rankings tables

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
