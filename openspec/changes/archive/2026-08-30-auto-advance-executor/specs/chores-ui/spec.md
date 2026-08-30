## ADDED Requirements

### Requirement: People table shows in_rotation status
The People section of the Management tab SHALL display the `in_rotation` flag for each person as a non-editable checkbox in the table row.

#### Scenario: in_rotation shown in table
- **WHEN** the People table is rendered
- **THEN** each row SHALL include a checkbox or indicator reflecting the person's `in_rotation` value

### Requirement: Add-person form includes in_rotation toggle
The inline add-person form SHALL include a checkbox for `in_rotation`, checked by default.

#### Scenario: Checkbox defaults to checked
- **WHEN** the user opens the add-person form
- **THEN** the `in_rotation` checkbox SHALL be visible and checked by default

#### Scenario: Creating person with in_rotation unchecked
- **WHEN** the user unchecks `in_rotation` and submits the add form
- **THEN** the API request SHALL include `"in_rotation": false`

### Requirement: Edit-person form includes in_rotation toggle
The inline edit-person form SHALL display and allow editing of the `in_rotation` flag.

#### Scenario: Edit form reflects current in_rotation value
- **WHEN** the user opens the edit form for a person with `in_rotation: false`
- **THEN** the `in_rotation` checkbox SHALL be unchecked

#### Scenario: Saving updated in_rotation value
- **WHEN** the user changes the `in_rotation` checkbox and saves
- **THEN** the PUT request SHALL include the new value for `in_rotation`
