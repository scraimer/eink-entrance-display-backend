# Chores System Developer Guide

This guide covers how to set up, seed, query, and maintain the chores SQLite database.

## Overview

The chores system stores all chore data in a local SQLite database (`chores.sqlite` in the project root). It provides a REST API for CRUD operations and tracks every change in an audit log.

For the database schema, see [chores-database-schema.md](chores-database-schema.md).
For the full API reference, see [chores-api-reference.md](chores-api-reference.md).

## Running Migrations

The database is automatically initialized when the FastAPI application starts. Tables are created via SQLAlchemy's `Base.metadata.create_all()` in `ChoresDatabase.init_db()`.

You can also initialize it manually using the CLI tools:

```bash
cd /workspaces/dev
source .venv/bin/activate

# Initialize database schema and seed people
python -m src.eink_backend.chores_db_tools init-db
```

The database file is created at `./chores.sqlite` relative to the project root.

## Seeding Initial Data

### Seed People

The people list is hardcoded in `migrate_chores_data.py`. Run:

```bash
python -m src.eink_backend.chores_db_tools people-init
```

This inserts the initial household members (Ariel, Asaf, Amalya, Alon, Aviv) with their ordinals and avatar filenames. All insertions are logged to the audit log with `changed_by='migration'`.

### Seed Chores from Google Sheets

To populate the initial chores list from Google Sheets:

```bash
# Requires google-sheets-bot-auth.json to be present
python -m src.eink_backend.chores_db_tools sync-sheets
```

This:
1. Reads chore names and frequencies from the "Friday Chores" worksheet
2. Deletes all existing chores (with audit log entries)
3. Inserts fresh chores and creates empty `chore_state` records
4. Optionally imports difficulty ratings as `rankings`

See [chores-sync-from-sheets.md](chores-sync-from-sheets.md) for Google Sheets format details.

### Seed on Application Startup

Set `SYNC_CHORES_FROM_SHEETS=true` to trigger a sync automatically when the app starts:

```bash
SYNC_CHORES_FROM_SHEETS=true uvicorn src.eink_backend.main:app
```

Sync errors do **not** prevent startup — they are logged as warnings.

## Querying the API

With the application running on `http://localhost:8000`:

### List all chores with state

```bash
curl http://localhost:8000/api/v1/chores/summary | python -m json.tool
```

### List all people

```bash
curl http://localhost:8000/api/v1/chores/people
```

### Create a person

```bash
curl -X POST http://localhost:8000/api/v1/chores/people \
  -H "Content-Type: application/json" \
  -d '{"name": "John", "ordinal": 6, "avatar": "john.png"}'
```

### Record a chore execution

```bash
curl -X POST http://localhost:8000/api/v1/chores/executions \
  -H "Content-Type: application/json" \
  -d '{"chore_id": 1, "executor_id": 2}'
```

This sets `last_executor_id` and `last_execution_date` on `chore_state`, and automatically
calculates `next_executor_id` and `next_execution_date` using round-robin over `people.ordinal`.

### Override the next executor

```bash
curl -X PUT http://localhost:8000/api/v1/chores/executions/next-executor \
  -H "Content-Type: application/json" \
  -d '{"chore_id": 1, "next_executor_id": 3, "next_execution_date": "2026-05-01"}'
```

## Auditing Changes

Every INSERT, UPDATE, and DELETE is recorded in `audit_log`. Query it:

```bash
# All changes to the "chores" table
curl "http://localhost:8000/api/v1/chores/audit?table_name=chores"

# Audit trail for a specific record
curl "http://localhost:8000/api/v1/chores/audit?table_name=people&record_id=3"

# Changes since a date
curl "http://localhost:8000/api/v1/chores/audit?since=2026-04-01"

# DELETE operations only
curl "http://localhost:8000/api/v1/chores/audit?operation=DELETE"
```

The `before_values` field in DELETE entries contains the full row snapshot — useful for recovering accidentally deleted data.

The `changed_by` field indicates the source:
- `api` — triggered by an API call
- `migration` — triggered by the migration/seed script
- `auto` — triggered automatically (e.g. chore_state update after an execution)

Audit log entries older than 365 days are cleaned up daily by a background task.

## Next Executor Calculation

When a chore is executed (via `POST /executions`), the system automatically calculates the next executor:

1. All people are fetched sorted by `ordinal` (ascending).
2. The person with the next ordinal after `last_executor_id` is selected.
3. If the last executor was the last person in the list, it wraps back to the first person (round-robin).
4. `next_execution_date = last_execution_date + (frequency_in_weeks × 7 days)`.

Rankings (1–10 preference scores) are stored but currently do not influence the calculation — the round-robin is based purely on `ordinal` order. Rankings are available via the `/summary` endpoint for future use.

## Running Tests

```bash
cd /workspaces/dev
source .venv/bin/activate

# Integration tests for the full API
pytest test_chores_integration.py -v

# Cascade delete behaviour
pytest test_person_cascade_delete.py -v

# Migration script tests
pytest test_chores_migration.py -v

# Google Sheets sync tests
pytest test_sync_chores_from_sheets.py -v
```

## Direct SQLite Access

For debugging, you can query the database directly:

```bash
sqlite3 /workspaces/dev/chores.sqlite

# Show all tables
.tables

# Show the current state of all chores
SELECT c.name, cs.last_execution_date, cs.next_execution_date
FROM chores c
LEFT JOIN chore_state cs ON cs.chore_id = c.id;

# Show recent audit entries
SELECT table_name, operation, record_id, changed_at, changed_by
FROM audit_log
ORDER BY changed_at DESC
LIMIT 20;
```

## Architecture Notes

- The database is separate from `data_cache.sqlite` (used for the e-ink rendering cache).
- The `ChoresDatabase` class in `chores_db.py` manages the SQLAlchemy engine and session factory.
- All sessions are opened and closed within individual request handlers — no persistent session state.
- The `chores_api.py` router is registered in the FastAPI `lifespan` context (not a startup event) to ensure routes appear in `/docs`.
