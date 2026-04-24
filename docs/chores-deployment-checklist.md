# Deployment Checklist: Chores SQLite Migration

This checklist covers deploying the chores SQLite backend to production.

## Pre-Deployment

- [ ] **Backup Google Sheets data**
  - Export the "Friday Chores" worksheet to CSV or make a copy of the spreadsheet
  - Note the current frequency values for all chores

- [ ] **Verify `google-sheets-bot-auth.json` is present** in the project root (needed for initial sync)

- [ ] **Build and test locally**
  ```bash
  cd /workspaces/dev
  source .venv/bin/activate
  pytest test_chores_integration.py test_person_cascade_delete.py test_chores_migration.py -v
  ```

## Database Setup

- [ ] **Initialize the database schema**
  ```bash
  python -m src.eink_backend.chores_db_tools init-db
  ```

- [ ] **Seed initial people data**
  ```bash
  python -m src.eink_backend.chores_db_tools people-init
  ```
  Verify: `sqlite3 chores.sqlite "SELECT id, name, ordinal FROM people ORDER BY ordinal;"`

- [ ] **Sync chores from Google Sheets**
  ```bash
  python -m src.eink_backend.chores_db_tools sync-sheets
  ```
  Verify: `sqlite3 chores.sqlite "SELECT name, frequency_in_weeks FROM chores ORDER BY name;"`

- [ ] **Verify chore_state records were created** (one per chore)
  ```bash
  sqlite3 chores.sqlite "SELECT COUNT(*) FROM chore_state;"
  # Should match: SELECT COUNT(*) FROM chores;
  ```

- [ ] **Verify audit log entries** from migration
  ```bash
  sqlite3 chores.sqlite "SELECT table_name, operation, COUNT(*) FROM audit_log GROUP BY table_name, operation;"
  ```

## Deployment

- [ ] **Copy `chores.sqlite` to production host** (or mount the volume)

- [ ] **Start the application with the new image**
  - Do NOT set `SYNC_CHORES_FROM_SHEETS=true` on first run — the database is already seeded
  - Verify: `GET /api/v1/chores/summary` returns expected chores

- [ ] **Check `/docs`** — the chores API routes should be visible under the "chores" tag

- [ ] **Smoke test the API**
  ```bash
  curl http://localhost:8000/api/v1/chores/people
  curl http://localhost:8000/api/v1/chores/chores
  curl http://localhost:8000/api/v1/chores/summary
  ```

- [ ] **Test rendering pipeline**
  ```bash
  curl "http://localhost:8000/html-dev/black"
  ```
  Confirm chores appear in the HTML output.

## Post-Deployment Monitoring

- [ ] **Watch application logs** for the first 24 hours for errors in:
  - Chores API route handlers
  - Daily audit log cleanup task (runs at 2 AM)
  - Background data collection task

- [ ] **Verify audit log is growing** after real API usage
  ```bash
  sqlite3 chores.sqlite "SELECT COUNT(*) FROM audit_log;"
  ```

- [ ] **Check audit log cleanup** after the first 2 AM run
  (Only meaningful after 365 days of data, but verify the task ran without errors)

## Optional: Remove Google Sheets Dependency (Post-Migration)

Once the system is running stably from SQLite and you no longer need to sync from Sheets:

- [ ] Remove or archive `src/eink_backend/sync_chores_from_sheets.py`
- [ ] Remove or archive `src/eink_backend/migrate_chores_data.py`
- [ ] Remove `SYNC_CHORES_FROM_SHEETS` env var handling from `main.py`
- [ ] Remove the `google-api-python-client` and `gspread` packages from `pyproject.toml` if no other modules use them
- [ ] Update this checklist and `README.md`

## Rollback Plan

If the deployment fails and you need to revert to the Google Sheets-based chores:

1. Restore the previous Docker image
2. Verify the Google Sheets spreadsheet is still intact
3. The old rendering pipeline in `chores.py` used Google Sheets directly — restore that code from git history if needed
