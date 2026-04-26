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
