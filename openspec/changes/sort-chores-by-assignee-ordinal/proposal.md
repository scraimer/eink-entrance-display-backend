## Why

The current chores renderer sorts by assignee name and still normalizes assignee labels with a hard-coded lookup. This is fragile and inconsistent with database-driven assignee ordering.

## What Changes

- Change `render_chores()` to sort chores by the assignee ordinal stored in the database instead of alphabetic assignee name.
- Remove the render-time dependency on `normalize_assigneed()` for sorting decisions and instead derive ordering from database person/assignee data.
- Ensure all assignee-related display information is read from the database, replacing the `#sym:normalize_assigneed` normalization path.

## Capabilities

### New Capabilities

### Modified Capabilities
- `chores-ui`: chore list sorting behavior changes to respect assignee ordinal information from the database rather than assignee name normalization

## Impact

- `src/eink_backend/chores.py` rendering and sorting logic
- Database query/path used to resolve assignee information for chores
- Chores UI output ordering and displayed assignee metadata
