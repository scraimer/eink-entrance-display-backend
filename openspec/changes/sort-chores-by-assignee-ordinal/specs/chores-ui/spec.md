## ADDED Requirements

### Requirement: Chore list sorts assigned items by assignee ordinal
The Chores UI chore list SHALL order assigned chores by the executor's `ordinal` value from the database.

#### Scenario: Assigned chores follow database ordinal
- **WHEN** the chores list is rendered
- **THEN** assigned chores SHALL appear in the order of their assignees' database ordinals

#### Scenario: Unassigned chores remain last
- **WHEN** the chores list is rendered
- **THEN** chores with no assigned executor SHALL appear after all assigned chores

#### Scenario: Same-person chores use frequency tie-breaker
- **WHEN** two assigned chores have the same executor ordinal
- **THEN** the chores SHALL be ordered by `frequency_in_weeks` ascending