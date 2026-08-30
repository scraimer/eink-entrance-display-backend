# Design: SQLite Database Schema and APIs for Chores System

## Context

The eink_backend currently reads chore data from Google Sheets, which creates external dependencies and prevents comprehensive auditing. This design describes how to migrate to a local SQLite database with APIs for managing chores, tracking executions, and maintaining rankings.

The system must integrate with the existing FastAPI application in `src/eink_backend/main.py` and the data_cache infrastructure in `src/eink_backend/data_cache.py`.

## Goals

- Enable programmatic CRUD operations on chores, executions, people, and rankings
- Maintain complete audit trail of all database changes
- Support automated next-executor calculation based on frequency and rankings
- Provide JSON APIs that integrate seamlessly with the existing FastAPI application
- Store all timestamps in UTC

## Non-Goals

- Real-time synchronization with Google Sheets (one-time migration only)
- Complex scheduling algorithms (use frequency_in_weeks + rankings for calculation)
- ~~Web UI for chore management (API-first design; UI can be added later)~~ — **UI is now in scope, see Decision 7**

## Decisions

### 1. Database Schema

All tables use UTC timestamps and include auto-increment integer primary keys:

```sql
-- People table: Base list of household members
CREATE TABLE people (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    ordinal INTEGER NOT NULL,
    avatar TEXT NOT NULL,
    updated_at TEXT NOT NULL
)

-- Chores table: Chore definitions
CREATE TABLE chores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    frequency_in_weeks INTEGER NOT NULL,
    updated_at TEXT NOT NULL
)

-- Chore state: Current state of each chore
CREATE TABLE chore_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chore_id INTEGER NOT NULL UNIQUE,
    last_executor_id INTEGER,
    last_execution_date TEXT,
    next_executor_id INTEGER,
    next_execution_date TEXT,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (chore_id) REFERENCES chores(id),
    FOREIGN KEY (last_executor_id) REFERENCES people(id),
    FOREIGN KEY (next_executor_id) REFERENCES people(id)
)

-- Executions: Historical log of chore executions
CREATE TABLE executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chore_id INTEGER NOT NULL,
    executor_id INTEGER NOT NULL,
    execution_date TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (chore_id) REFERENCES chores(id),
    FOREIGN KEY (executor_id) REFERENCES people(id)
)

-- Rankings: People's preferences/ratings for chores (1-10)
CREATE TABLE rankings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id INTEGER NOT NULL,
    chore_id INTEGER NOT NULL,
    rating INTEGER NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(person_id, chore_id),
    FOREIGN KEY (person_id) REFERENCES people(id),
    FOREIGN KEY (chore_id) REFERENCES chores(id)
)

-- Audit log: Complete history of all changes
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,
    operation TEXT NOT NULL,
    record_id INTEGER NOT NULL,
    before_values TEXT,
    after_values TEXT,
    changed_at TEXT NOT NULL,
    changed_by TEXT
)
```

### 2. API Endpoints

All endpoints return JSON and are routed under `/api/v1/chores/`:

#### Chores CRUD
- `POST /api/v1/chores/chores` - Create chore
- `GET /api/v1/chores/chores/{id}` - Get chore
- `PUT /api/v1/chores/chores/{id}` - Update chore
- `DELETE /api/v1/chores/chores/{id}` - Delete chore
- `GET /api/v1/chores/chores` - List all chores

#### Executions
- `POST /api/v1/chores/executions` - Perform execution (creates execution record, updates chore state, calculates next executor/date)
- `PUT /api/v1/chores/executions/{execution_id}/next-executor` - Modify next executor and date for a specific execution's chore
- `GET /api/v1/chores/executions` - List executions (with optional filters)

#### People
- `POST /api/v1/chores/people` - Create person
- `GET /api/v1/chores/people/{id}` - Get person
- `PUT /api/v1/chores/people/{id}` - Update person
- `DELETE /api/v1/chores/people/{id}` - Delete person
- `GET /api/v1/chores/people` - List all people

#### Rankings
- `POST /api/v1/chores/rankings` - Create/update ranking
- `GET /api/v1/chores/rankings` - List rankings (with optional person_id and chore_id filters)
- `DELETE /api/v1/chores/rankings/{person_id}/{chore_id}` - Delete ranking

#### Composite Endpoints
- `GET /api/v1/chores/summary` - Get all chores with current state and all person rankings (used by rendering pipeline)

#### Audit
- `GET /api/v1/chores/audit` - Query audit log (with optional table_name and record_id filters)

### 3. Next Executor Calculation

When executing a chore:
1. Get all people in order by their `ordinal`
2. Get the current last executor
3. Find the next person in the list after the last executor
4. If at the end of list, wrap to the first person
5. Apply weighting: if person has a ranking for this chore, weight selection by preference (1-10 scale, where 10 means they like it more)
6. Set next_execution_date = today + (chore.frequency_in_weeks * 7 days)

For the initial MVP, use simple round-robin. Rankings can weight selection in future versions.

### 4. Audit Log Implementation

Every INSERT, UPDATE, DELETE operation on chores, people, chore_state, executions, and rankings triggers:
1. Serialize before-state to JSON string (only for UPDATE/DELETE)
2. Serialize after-state to JSON string (only for INSERT/UPDATE)
3. Insert row into audit_log with operation, record_id, before_values, after_values, and UTC timestamp
4. Set changed_by to one of: "migration" (during initial data load), "api" (from API endpoints), or "auto" (from automatic operations)

Use database triggers (SQLite supports them) or application-level hooks.

**Audit Log Retention:** Audit log entries are append-only. Automatic cleanup removes records older than 365 days. The cleanup process runs daily and is non-blocking.

### 5. Result Set Limits

All list/query endpoints have a fixed maximum result set limit of 1000 records. If a query would return more than 1000 records, the API returns HTTP 400 with an error message indicating the limit was exceeded and suggesting more specific filters.

This prevents accidental bulk transfers of large datasets and ensures predictable API response times.

### 6. Integration with Existing System

- Database file: Use existing `data_cache.sqlite` or separate file as configured
- Migration: Load existing chores from Google Sheets, populate initial database
- Rendering: Update `chores.py` to read from database instead of Sheets API
- Background tasks: No changes needed to collection schedule; data now comes from database

## Risks and Trade-offs

### Risks
1. **Data migration**: Must validate all existing chores migrate correctly
2. **Compatibility**: Existing code reading from Sheets must be updated simultaneously
3. **Audit log growth**: Very high-frequency changes could make audit table large (mitigation: archive old entries)

### Trade-offs
1. **Round-robin vs weighted scheduling**: Starting with simple round-robin for MVP; rankings can improve selection later
2. **Database file location**: Collocating with data_cache.sqlite simplifies deployment but couples concerns
3. **API versioning**: Starting with v1; plan for v2 if schema changes significantly

## Migration Plan

1. **Phase 1**: Create database schema and Python models
2. **Phase 2**: Implement CRUD APIs for people, chores, rankings
3. **Phase 3**: Implement execution API with state tracking
4. **Phase 4**: Implement audit logging
5. **Phase 5**: Migrate data from Google Sheets
6. **Phase 6**: Update rendering pipeline to use database
7. **Phase 7**: Testing and validation

## Resolved Decisions

### Audit Log Immutability
**Decision**: Append-only with automatic cleanup. Audit log entries cannot be modified or manually deleted. A background process automatically deletes entries older than 365 days to manage storage.

### Migration User in Audit Log
**Decision**: Yes. The audit log includes a "migration" user for all entries created during the initial data load from Google Sheets. This clearly distinguishes system-seeded data from later user-driven changes.

### Execution Error Handling
**Decision**: No error recovery needed. Chores are either executed successfully (creates execution record and updates state) or not executed at all. There are no partial failures or rollbacks to handle. If an execution request fails, the entire operation is rolled back and the API returns an error without modifying state.

---

### 7. Web Application (`/chores`)

A single-page application (SPA) served at `GET /chores` from the FastAPI backend. Built entirely with **plain HTML, inline CSS, and vanilla JavaScript** — no build step, no npm, no external JS frameworks. This keeps the deployment simple: one Python file, zero new dependencies.

#### Serving

- `GET /chores` returns the full HTML document (including `<style>` and `<script>` inline).
- All data is fetched from the existing `/api/v1/chores/*` endpoints via `fetch()`.
- The HTML is generated by a new module `src/eink_backend/chores_ui.py` and returned as `HTMLResponse`.

#### Navigation

Three tabs rendered client-side by toggling CSS `display`:

| Tab | Path fragment | Description |
|-----|---------------|-------------|
| Chores | `#chores` | Default view — chore list with "Mark as Done" |
| Management | `#management` | CRUD for Chores and People |
| Audit Log | `#audit` | Last 100 audit entries, read-only |

#### Tab 1: Chores List

- Fetches `GET /api/v1/chores/summary` on load.
- Also fetches `GET /api/v1/chores/people` to build an `id → name` lookup map.
- Displays a table with columns: **Chore**, **Due Date**, **Next Executor**.
- Sorted client-side:
  1. Primary: `next_execution_date` descending (most overdue first; `null` dates sort last)
  2. Secondary: next executor's `ordinal` descending
- Clicking a row opens a detail panel (or inline expansion) showing:
  - Last executor name and date
  - Next executor name and date
  - Frequency
  - "Mark as Done" button
- **Mark as Done**: `POST /api/v1/chores/executions` with `{ chore_id, executor_id: next_executor_id }`. Refreshes the list on success.
- If a chore has no next executor set, "Mark as Done" is disabled.

#### Tab 2: Management

Two sub-sections, toggled by buttons:

**People section**
- Lists all people (from `GET /api/v1/chores/people`) sorted by ordinal.
- Each person row has **Edit** and **Delete** buttons.
- Edit opens an inline form: name, ordinal, avatar.
- Clicking a person's name expands their ranking panel:
  - Shows every chore with a rating input (1–10, or blank).
  - Save sends `POST /api/v1/chores/rankings` (upsert) per changed rating.
- "Add Person" button at the bottom opens a new-person form.

**Chores section**
- Lists all chores (from `GET /api/v1/chores/chores`) sorted by name.
- Each row: chore name, frequency, **Edit** and **Delete** buttons.
- Edit inline: name, frequency_in_weeks.
- "Add Chore" button at the bottom.
- Deletion requires a confirmation prompt before calling `DELETE /api/v1/chores/chores/{id}`.

#### Tab 3: Audit Log

- Fetches `GET /api/v1/chores/audit` and limits display to the last 100 entries (API already caps at 1000; client slices the result to 100).
- Displays a read-only table: **When**, **Table**, **Operation**, **Record ID**, **Changed By**.
- Clicking a row toggles a detail expansion showing `before_values` and `after_values` as formatted JSON.
- No create/edit/delete actions on this tab.

#### Error Handling

- All API errors show an inline error message near the relevant section (not `alert()`).
- 404 and 400 responses show the `detail` field from the JSON response body.

#### Styling

- Minimal CSS, self-contained in the `<style>` block.
- Uses a tab-bar at the top, a content area below.
- Works without any external fonts or icon libraries.

### API Result Set Limits
**Decision**: No pagination API. All list endpoints return a maximum of 1000 records. If a query would exceed this limit, the API returns HTTP 400 with an error message. Clients must use filtering options (date ranges, person_id, chore_id, etc.) to narrow results.
