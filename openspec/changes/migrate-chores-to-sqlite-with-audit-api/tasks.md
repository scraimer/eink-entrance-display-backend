# Tasks: Migrate Chores to SQLite with Audit API

## Phase 1: Database Schema and Python Models

- [x] Create database migration script to set up all tables
  - [x] Create table: people
  - [x] Create table: chores
  - [x] Create table: chore_state
  - [x] Create table: executions
  - [x] Create table: rankings
  - [x] Create table: audit_log
  - [x] Create all necessary indexes
  - [x] Add ON DELETE CASCADE foreign key constraints

- [x] Create SQLAlchemy ORM models or dataclasses for database operations
  - [x] Model: Person
  - [x] Model: Chore
  - [x] Model: ChoreState
  - [x] Model: Execution
  - [x] Model: Ranking
  - [x] Model: AuditLogEntry

- [x] Implement database connection and session management
  - [x] Add database initialization to main.py startup
  - [x] Use existing data_cache.sqlite or configure separate database file
  - [x] Implement connection pooling

## Phase 2: Seed Initial Data

- [x] Create migration script to populate initial people data
  - [x] Load hardcoded people list from current chores.py (Ariel, Asaf, Amalya, Alon, Aviv)
  - [x] Set ordinal values and avatar filenames
  - [x] Log entries in audit_log with changed_by='migration'

- [x] Load existing chores from Google Sheets (one-time migration)
  - [x] Query Google Sheets API for current chores
  - [x] Parse chore names and frequencies
  - [x] Insert into chores table
  - [x] Create empty chore_state records for each chore
  - [x] Log entries in audit_log with changed_by='migration'

- [x] Create sync script for ongoing updates from Google Sheets
  - [x] Create sync_chores_from_sheets.py with full refresh functionality
  - [x] Implement clear_all_chores() to delete existing chores with audit logging
  - [x] Implement insert_chores() to populate from Sheets data
  - [x] Create chores_db_tools.py CLI tool for manual sync operations
  - [x] Add SYNC_CHORES_FROM_SHEETS environment variable for startup initialization
  - [x] Test complete sync workflow with mock data

## Phase 3: Audit Logging Infrastructure

- [x] Implement audit logging wrapper functions
  - [x] audit_insert(table_name, record, changed_by)
  - [x] audit_update(table_name, record_id, old_values, new_values, changed_by)
  - [x] audit_delete(table_name, record_id, old_values, changed_by)
  - [x] Serialize values to JSON with proper handling of dates/timestamps

- [x] Integrate audit logging into all database operations
  - [x] Create decorator or context manager for automatic audit logging
  - [x] Update all CRUD operations to call audit functions

- [x] Test audit logging with sample operations
  - [x] Verify INSERT creates correct audit entries
  - [x] Verify UPDATE logs before and after values
  - [x] Verify DELETE logs before values only
  - [x] Verify changed_by field is set correctly
  - [x] Test audit_log with changed_by='migration' for initial data load

- [x] Implement audit log cleanup
  - [x] Create background task that runs daily
  - [x] Delete all audit_log entries older than 365 days
  - [x] Ensure cleanup is non-blocking and doesn't interfere with API operations
  - [x] Log cleanup actions to application logs

## Phase 4: Core API Endpoints - People

- [x] POST /api/v1/chores/people - Create person
  - [x] Validate required fields (name, ordinal, avatar)
  - [x] Check name uniqueness
  - [x] Create record with timestamps
  - [x] Log to audit_log
  - [x] Return created person with ID

- [x] GET /api/v1/chores/people/{id} - Get person
  - [x] Fetch from database
  - [x] Return person record

- [x] PUT /api/v1/chores/people/{id} - Update person
  - [x] Allow optional field updates
  - [x] Log before/after values to audit_log
  - [x] Return updated person

- [x] DELETE /api/v1/chores/people/{id} - Delete person
  - [x] Check for dependent records (executions, rankings)
  - [x] Handle cascade deletion if applicable
  - [x] Log deletion to audit_log
  - [x] Return 204 No Content

- [x] GET /api/v1/chores/people - List people
  - [x] Return all people sorted by ordinal with 1000-record limit
  - [x] Return HTTP 400 if result set exceeds limit

## Phase 5: Core API Endpoints - Chores

- [x] POST /api/v1/chores/chores - Create chore
  - [x] Validate required fields (name, frequency_in_weeks)
  - [x] Validate frequency_in_weeks >= 1
  - [x] Check name uniqueness
  - [x] Create record with timestamps
  - [x] Create empty chore_state record
  - [x] Log to audit_log
  - [x] Return created chore with ID

- [x] GET /api/v1/chores/chores/{id} - Get chore
  - [x] Fetch from database
  - [x] Return chore record

- [x] PUT /api/v1/chores/chores/{id} - Update chore
  - [x] Allow optional field updates
  - [x] Validate frequency_in_weeks >= 1
  - [x] Log before/after values to audit_log
  - [x] Return updated chore

- [x] DELETE /api/v1/chores/chores/{id} - Delete chore
  - [x] Delete associated chore_state, executions, rankings (CASCADE)
  - [x] Log deletions to audit_log
  - [x] Return 204 No Content

- [x] GET /api/v1/chores/chores - List chores
  - [x] Return all chores with 1000-record limit
  - [x] Return HTTP 400 if result set exceeds limit

## Phase 6: Core API Endpoints - Rankings

- [x] POST /api/v1/chores/rankings - Create or update ranking
  - [x] Validate required fields (person_id, chore_id, rating)
  - [x] Validate rating is 1-10
  - [x] Check person and chore exist
  - [x] Check for existing ranking (upsert vs insert)
  - [x] Log to audit_log (INSERT or UPDATE)
  - [x] Return ranking record

- [x] GET /api/v1/chores/rankings - List rankings
  - [x] Support filtering by person_id and/or chore_id
  - [x] Return matching rankings with 1000-record limit
  - [x] Return HTTP 400 if result set exceeds limit

- [x] DELETE /api/v1/chores/rankings/{person_id}/{chore_id} - Delete ranking
  - [x] Log deletion to audit_log
  - [x] Return 204 No Content

## Phase 7: Execution API - Core Implementation

- [x] Implement next executor calculation algorithm
  - [x] Get all people sorted by ordinal
  - [x] Implement round-robin logic: next person after last executor
  - [x] Handle wrap-around (end of list → first person)
  - [x] Calculate next_execution_date = last_execution_date + (frequency_in_weeks * 7 days)

- [x] POST /api/v1/chores/executions - Perform execution
  - [x] Validate required fields (chore_id, executor_id)
  - [x] Check chore and executor exist
  - [x] Create execution record with today's date (UTC)
  - [x] Update chore_state: set last_executor_id, last_execution_date
  - [x] Calculate next_executor_id and next_execution_date
  - [x] Update chore_state: set calculated values
  - [x] Log execution INSERT to audit_log
  - [x] Log chore_state UPDATE to audit_log with changed_by='auto'
  - [x] Return execution and updated state

- [x] GET /api/v1/chores/executions - List executions
  - [x] Support filtering by chore_id, executor_id, date range
  - [x] Return execution records with 1000-record limit
  - [x] Return HTTP 400 if result set exceeds limit

- [x] PUT /api/v1/chores/executions/next-executor - Modify next executor
  - [x] Validate required fields (chore_id)
  - [x] Accept optional next_executor_id and next_execution_date
  - [x] Update chore_state with provided values
  - [x] Log UPDATE to audit_log with changed_by='api'
  - [x] Return updated chore_state

## Phase 8: Composite and Audit Endpoints

- [x] GET /api/v1/chores/summary - Get chores summary
  - [x] Fetch all chores with their state
  - [x] For each chore, fetch all rankings
  - [x] Return nested structure with chores, state, and rankings
  - [x] This endpoint is consumed by rendering pipeline

- [x] GET /api/v1/chores/audit - Query audit log
  - [x] Support filtering by table_name, record_id, operation, date range
  - [x] Return audit entries with before/after values with 1000-record limit
  - [x] Return HTTP 400 if result set exceeds limit

## Phase 9: Update Rendering Pipeline

- [x] Modify src/eink_backend/chores.py to use database instead of Google Sheets
  - [x] Replace get_chores_from_spreadsheet() with database query
  - [x] Update collect_data() to fetch from database
  - [x] Remove Google Sheets API calls
  - [x] Keep normalize_assigneed() function or integrate with people table

- [x] Update rendering functions to work with new data model
  - [x] Modify render_chores() to use ChoreData that includes state
  - [x] Update HTML template rendering with new data structure

- [x] Test rendering with database chores
  - [x] Verify chores display correctly
  - [x] Verify ordering and formatting

## Phase 10: Integration Testing

- [x] Test API contract with all endpoints
  - [x] Verify all endpoints return correct JSON structure
  - [x] Verify error handling (validation, not found, etc.)
  - [x] Test filtering and result set limits
  - [x] Verify HTTP 400 when result set exceeds 1000-record limit

- [x] Test audit logging end-to-end
  - [x] Create chore → verify audit entry
  - [x] Execute chore → verify execution and state audit entries
  - [x] Update rankings → verify audit entries
  - [x] Query audit log → verify filtering and retrieval

- [x] Test data integrity
  - [x] Verify foreign key constraints
  - [x] Verify uniqueness constraints
  - [x] Test ON DELETE CASCADE for chore deletion
    - [x] Create chore with chore_state, executions, and rankings
    - [x] Delete chore via API
    - [x] Verify chore_state is deleted
    - [x] Verify all executions for that chore are deleted
    - [x] Verify all rankings for that chore are deleted
    - [x] Verify audit log entries are created for all deletions
  - [x] Test ON DELETE CASCADE for person deletion
    - [x] Create person with executions, rankings, and chore assignments
    - [x] Delete person via API
    - [x] Verify all executions with that executor are deleted
    - [x] Verify all rankings for that person are deleted
    - [x] Verify chore states with last_executor_id are updated (set to NULL)
    - [x] Verify chore states with next_executor_id are updated (set to NULL)
    - [x] Verify audit log entries are created for all deletions and updates

- [x] Test next executor calculation
  - [x] Verify round-robin with different frequencies
  - [x] Verify wrap-around behavior
  - [x] Verify date calculation with various frequencies

- [x] Performance testing
  - [x] Measure /api/v1/chores/summary response time
  - [x] Profile database queries
  - [x] Optimize indexes if needed

## Phase 11: Documentation and API Summary

- [x] Create API summary document
  - [x] List all endpoints with descriptions
  - [x] Include request/response examples
  - [x] Document error codes
  - [x] Include query parameters and filtering options

- [x] Document database schema
  - [x] Include ER diagram
  - [x] Document table relationships
  - [x] Document constraints and indexes

- [x] Write developer guide
  - [x] How to run migrations
  - [x] How to seed initial data
  - [x] How to query the API
  - [x] How to audit changes

## Phase 12: Deployment and Cutover

- [x] Create deployment checklist
  - [x] Backup existing Google Sheets data
  - [x] Run database migrations
  - [x] Seed initial data from Sheets
  - [x] Update config to use new APIs
  - [x] Test rendering pipeline
  - [x] Monitor for errors

- [x] Remove Google Sheets dependencies
  - [x] Remove google-api-python-client imports
  - [x] Remove Sheets-related configuration
  - [x] Update README and documentation

- [x] Monitor and support
  - [x] Watch for audit log anomalies
  - [x] Track API performance
  - [x] Handle any edge cases discovered in production

## Phase 13: Chores Web Application (`/chores`)

- [x] Create `src/eink_backend/chores_ui.py` module
  - [x] Add `generate_chores_ui_html()` function that returns the full SPA HTML string
  - [x] Inline all CSS in a `<style>` block (no external stylesheets)
  - [x] Inline all JavaScript in a `<script>` block (no external files or frameworks)

- [x] Add `GET /chores` route to `main.py`
  - [x] Import `generate_chores_ui_html` from `chores_ui`
  - [x] Return `HTMLResponse` with the generated HTML

- [x] Implement Tab 1: Chores List
  - [x] Fetch `/api/v1/chores/summary` and `/api/v1/chores/people` on page load
  - [x] Build an `id → {name, ordinal}` lookup map for people
  - [x] Display table with columns: Chore, Due Date, Next Executor (name, not ID)
  - [x] Sort client-side: primary by `next_execution_date` descending (null dates last), secondary by next executor's `ordinal` descending
  - [x] Clicking a row expands a detail panel showing: last executor name + date, next executor name + date, frequency
  - [x] "Mark as Done" button in detail panel: `POST /api/v1/chores/executions` with `{chore_id, executor_id: next_executor_id}`
  - [x] Disable "Mark as Done" if chore has no `next_executor_id`
  - [x] Refresh the list after a successful execution

- [x] Implement Tab 2: Management — People section
  - [x] Fetch and list all people sorted by ordinal
  - [x] Edit button: show inline form for name, ordinal, avatar → `PUT /api/v1/chores/people/{id}`
  - [x] Delete button: confirm dialog → `DELETE /api/v1/chores/people/{id}`
  - [x] Clicking a person's name expands their rankings panel
    - [x] List every chore with a rating input (1–10, or blank for unrated)
    - [x] Save button: send `POST /api/v1/chores/rankings` for each changed rating
  - [x] "Add Person" button: inline form → `POST /api/v1/chores/people`

- [x] Implement Tab 2: Management — Chores section
  - [x] Fetch and list all chores sorted by name
  - [x] Edit button: inline form for name and frequency_in_weeks → `PUT /api/v1/chores/chores/{id}`
  - [x] Delete button: confirm dialog → `DELETE /api/v1/chores/chores/{id}`
  - [x] "Add Chore" button: inline form → `POST /api/v1/chores/chores`

- [x] Implement Tab 3: Audit Log
  - [x] Fetch `GET /api/v1/chores/audit` and display last 100 entries
  - [x] Read-only table: When, Table, Operation, Record ID, Changed By
  - [x] Clicking a row toggles `before_values` / `after_values` as formatted JSON
  - [x] No create/edit/delete actions on this tab

- [x] Error handling
  - [x] Show inline error messages (not `alert()`) near the relevant section on API errors
  - [x] Display `detail` field from JSON error responses for 400 and 404 responses

- [x] Tab navigation
  - [x] Tab bar with three tabs: Chores, Management, Audit Log
  - [x] Toggle tab content by showing/hiding sections (CSS `display`)
  - [x] Reflect active tab in URL hash (`#chores`, `#management`, `#audit`)
  - [x] Default to `#chores` if no hash is present
