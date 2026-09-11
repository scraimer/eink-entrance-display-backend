# chores-ui Specification

## Purpose

Define the browser-facing behavior of the chore management interface, including chore display, completion controls, plan management, and score presentation.
## Requirements
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

### Requirement: Chore management page declares a favicon
The HTML document returned by `GET /chores` SHALL include a favicon link in its `<head>` that references `/favicon.ico` and identifies the asset as an ICO image.

#### Scenario: Chore page includes favicon metadata
- **WHEN** a client requests `GET /chores`
- **THEN** the HTML response SHALL contain a `<link rel="icon">` declaration whose href is `/favicon.ico` and whose type is `image/x-icon`

### Requirement: Chore management page declares installable PWA metadata
The HTML document returned by `GET /chores` SHALL reference `/manifest.webmanifest` with `rel="manifest"`, declare a theme color, and declare `/icons/icon-192.png` as an Apple touch icon.

#### Scenario: Chore page includes PWA metadata
- **WHEN** a client requests `GET /chores`
- **THEN** the HTML response SHALL contain manifest, theme-color, and Apple touch icon metadata with the specified resource paths

### Requirement: Chore management manifest describes the broom app
The application SHALL serve `GET /manifest.webmanifest` as valid web app manifest JSON with an app name and short name for chore management, `start_url: "/chores"`, `display: "standalone"`, a theme color, and icon entries for `/icons/icon-192.png` and `/icons/icon-512.png`.

#### Scenario: Browser requests the web app manifest
- **WHEN** a client requests `GET /manifest.webmanifest`
- **THEN** the application SHALL return HTTP 200 with an application manifest media type and valid JSON containing the required install metadata and both icon entries

### Requirement: Chore management provides high-resolution broom icons
The application SHALL serve valid PNG icons at `/icons/icon-192.png` and `/icons/icon-512.png`, and SHALL serve a compatible ICO fallback at `/favicon.ico`. All icon variants SHALL depict the broom emoji `🧹` and the PNG icons SHALL have dimensions matching their filenames.

#### Scenario: High-resolution PNG icons are available
- **WHEN** a browser requests either supported PNG icon path
- **THEN** the application SHALL return HTTP 200 with `image/png` and an image whose dimensions are respectively 192x192 or 512x512

#### Scenario: ICO fallback remains available
- **WHEN** a browser requests `GET /favicon.ico`
- **THEN** the application SHALL return HTTP 200 with `image/x-icon` and a non-empty valid ICO containing the broom artwork

