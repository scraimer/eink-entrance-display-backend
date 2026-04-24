# Proposal: Migrate Chores System from Google Sheets to SQLite with Audit APIs

## Why

The current chores system relies on Google Sheets as a data source, creating dependencies on external cloud services and making it difficult to maintain an audit trail of changes. By migrating to a local SQLite database, we can:

1. **Eliminate cloud dependency**: Remove reliance on Google Sheets API for chore data
2. **Enable comprehensive auditing**: Track every change with before/after values for compliance and debugging
3. **Improve performance**: Local database access is faster and more predictable than cloud API calls
4. **Enable new workflows**: Support APIs for managing chores, executions, and rankings programmatically
5. **Support scheduling enhancements**: Calculate and track next executor and execution dates systematically

## What Changes

### Data Model
- **Chores**: Replace spreadsheet-based chore definitions with a database table (name, frequency_in_weeks)
- **Executions**: Introduce new table to track historical record of who performed each chore and when
- **Chore State**: New table to maintain current state of each chore (last executor, last execution date, next executor, scheduled next date)
- **People**: Formalize the person list from hardcoded values in chores.py into a database table (id, name, ordinal, avatar)
- **Rankings**: New table for people's satisfaction/preference ratings for each chore (person, chore, rating 1-10)
- **Audit Log**: Comprehensive audit trail for all table changes (table name, operation, before values, after values, timestamp, user)

### APIs
- **Chores**: Create, Read, Update, Delete operations
- **Executions**: Perform execution (creates record and updates chore state with auto-calculated next executor/date), Modify next executor and date
- **Chores + State**: Fetch current chores with their state and all person rankings
- **Audit**: (Optional) Query audit log for compliance/debugging

### Web Application (`/chores`)
A single-page web application served directly from the FastAPI backend at `/chores`. Built with plain HTML, CSS, and vanilla JavaScript (no build step), consuming the existing Chores API.

Three views:
1. **Chores list** (default): All chores sorted by due date (descending), then by next executor ordinal (descending). Each row shows the chore name, due date, and the executor's name (not ID). Clicking a chore opens a detail panel with a "Mark as Done" button that records an execution and advances the schedule.
2. **Management tab**: Add, edit, and delete Chores and People. Each person's page shows their rankings for every chore.
3. **Audit log tab**: Read-only, shows the last 100 audit log entries (table, operation, record, timestamp, changed_by).

## Capabilities

### New Capabilities
- Programmatic management of chores via RESTful JSON APIs
- Complete audit trail for regulatory compliance and debugging
- Intelligent next-executor calculation based on frequency and person rankings
- Historical execution tracking for analytics
- **Browser-based chore management UI** at `/chores` — no separate frontend deployment required

### Modified Capabilities
- Chores data now sourced from local database instead of Google Sheets
- Chore scheduling integrated into database with systematic state tracking
- All operations return structured JSON responses

## Impact

### Data Sources
- Current: Google Sheets (external)
- Future: SQLite database (local) + spreadsheet fallback removed

### Components Affected
- `src/eink_backend/chores.py`: Rewrite to use database instead of Google Sheets API
- `src/eink_backend/main.py`: Add new API endpoints for chores management, and the `/chores` SPA route
- `src/eink_backend/chores_ui.py`: New module that generates the SPA HTML (inline JS + CSS)
- Background collection task: Update to read from database

### Breaking Changes
- Existing chore data in Google Sheets will need to be migrated to SQLite
- Any external integrations reading from the spreadsheet will need to use the new APIs

### Dependencies
- No new Python dependencies (SQLite is built-in)
- New database schema and migrations required
