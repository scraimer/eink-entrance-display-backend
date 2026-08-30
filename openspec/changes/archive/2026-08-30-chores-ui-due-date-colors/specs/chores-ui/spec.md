## ADDED Requirements

### Requirement: Due-date badge uses grey for chores due in more than 7 days
The Chores UI due-date badge SHALL display a grey badge for chores whose next due date is more than 7 days away.

#### Scenario: Chore due in 8 days shows grey badge
- **WHEN** a chore's next due date is 8 or more days from today
- **THEN** the badge SHALL use the grey style and display "In Nd"

### Requirement: Due-date badge uses green for chores due within the next 2–7 days
The Chores UI due-date badge SHALL display a green badge for chores whose next due date is 2 to 7 days away (inclusive).

#### Scenario: Chore due in 7 days shows green badge
- **WHEN** a chore's next due date is exactly 7 days from today
- **THEN** the badge SHALL use the green style and display "In 7d"

#### Scenario: Chore due in 2 days shows green badge
- **WHEN** a chore's next due date is exactly 2 days from today
- **THEN** the badge SHALL use the green style and display "In 2d"

### Requirement: Due-date badge uses yellow for chores due today or tomorrow
The Chores UI due-date badge SHALL display a yellow badge for chores whose next due date is today or tomorrow (0–1 days away).

#### Scenario: Chore due today shows yellow badge
- **WHEN** a chore's next due date is today (0 days)
- **THEN** the badge SHALL use the yellow style and display "Due today"

#### Scenario: Chore due tomorrow shows yellow badge
- **WHEN** a chore's next due date is tomorrow (1 day from today)
- **THEN** the badge SHALL use the yellow style and display "In 1d"

### Requirement: Due-date badge uses red for overdue chores
The Chores UI due-date badge SHALL display a red badge for chores whose next due date is in the past.

#### Scenario: Overdue chore shows red badge
- **WHEN** a chore's next due date is before today
- **THEN** the badge SHALL use the red style and display "Overdue Nd"
