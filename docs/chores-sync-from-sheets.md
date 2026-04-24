# Chores Data Sync from Google Sheets

## Overview

The chores sync system provides a complete solution for synchronizing chore data from Google Sheets to the SQLite database. Unlike a one-time migration, this system allows for ongoing updates where the database can be completely refreshed from Sheets at any time while maintaining a complete audit trail of all changes.

## Architecture

### Three Tiers of Functionality

1. **sync_chores_from_sheets.py** - Core sync functions
   - `get_chores_from_spreadsheet()` - Read from Google Sheets
   - `clear_all_chores()` - Delete all existing chores with audit logging
   - `insert_chores()` - Insert fresh chores from Sheets data
   - `sync_chores_from_sheets()` - Orchestrates the complete refresh

2. **chores_db_tools.py** - CLI database tools
   - Standalone script for manual operations
   - Can be run without starting the FastAPI server
   - Multiple commands for different tasks

3. **main.py integration** - Optional automatic startup sync
   - Triggered by `SYNC_CHORES_FROM_SHEETS=true` environment variable
   - Runs during application startup
   - Non-blocking (errors don't prevent startup)

## Quick Start

### Option 1: Manual Sync via CLI

```bash
# Sync all chores from Google Sheets (clear and repopulate)
python -m src.eink_backend.chores_db_tools sync-sheets

# Initialize database and people only
python -m src.eink_backend.chores_db_tools init-db

# Initialize people only
python -m src.eink_backend.chores_db_tools people-init

# Clear all chores (destructive)
python -m src.eink_backend.chores_db_tools clear-chores
```

### Option 2: Automatic Sync on Startup

Set the environment variable before starting the application:

```bash
export SYNC_CHORES_FROM_SHEETS=true
python -m src.eink_backend.main
```

Or in Docker:

```bash
docker run -e SYNC_CHORES_FROM_SHEETS=true ...
```

### Option 3: Programmatic Sync

```python
from src.eink_backend.chores_db import ChoresDatabase
from src.eink_backend.sync_chores_from_sheets import sync_chores_from_sheets

db = ChoresDatabase("sqlite:///path/to/chores.sqlite")
sync_chores_from_sheets(db)
```

## Google Sheets Format

The sync expects a worksheet named "Friday Chores" (configurable in config.py) with the following columns:

| Column | Type | Required | Example |
|--------|------|----------|---------|
| Chore Name | String | Yes | "Clean Kitchen" |
| Frequency (weeks) | Integer | Yes | "1" |
| {PersonName} Difficulty Rating | Integer | No | "8" |

**Column Notes:**
- `Chore Name` and `Frequency (weeks)` are required
- Difficulty Rating columns are optional and use the format `{PersonName} Difficulty Rating`
- Difficulty ratings must be integers from 1-10
- For each person in the database, the sync looks for a column matching their exact name
- Example: If you have people named "Ariel", "Asaf", "Amalya", create columns:
  - "Ariel Difficulty Rating"
  - "Asaf Difficulty Rating"
  - "Amalya Difficulty Rating"
- Invalid or missing difficulty ratings are skipped (no error)
- Empty difficulty rating cells are ignored

Example worksheet with difficulty ratings:

```
Chore Name           Frequency (weeks)  Ariel Difficulty Rating  Asaf Difficulty Rating  Amalya Difficulty Rating
Clean Kitchen        1                  8                        6                       7
Mop Floors           2                  7                        9                       5
Bathroom             1                  9                        8                       6
Take Out Trash       1                                            5                       4
Vacuum Living Room   2                  6                        7                       8
```

## Sync Process

When `sync_chores_from_sheets()` is called:

### Step 1: Fetch from Google Sheets
- Reads from configured worksheet
- Parses chore names and frequencies
- Captures all columns for difficulty rating parsing
- Validates data (skips invalid rows)
- Returns list of chore dictionaries and raw records

### Step 2: Clear Existing Chores
- Queries all existing chores from database
- For each chore, creates an audit entry with operation=DELETE
- Deletes the chore (CASCADE deletes all related data)
- Returns count of deleted chores

**Cascading Deletes:**
- `Chore` → `ChoreState` (one-to-one)
- `Chore` → `Execution` (one-to-many)
- `Chore` → `Ranking` (one-to-many) - **clears old difficulty ratings**

### Step 3: Insert Fresh Chores
- For each chore from Sheets:
  - Creates `Chore` record
  - Creates empty `ChoreState` record
  - Creates audit entries for both INSERT operations
  - Logs with `changed_by='migration'`
- Returns count of inserted chores and name-to-ID mapping

### Step 4: Parse Difficulty Ratings
- Fetches all people from database
- For each row in Sheets:
  - Looks for columns matching `{PersonName} Difficulty Rating`
  - Validates rating is 1-10
  - Creates ranking entry if valid
- Returns list of (person_id, chore_id, rating) tuples

**Difficulty Rating Logic:**
- Column name must match person name exactly (case-sensitive)
- Ratings outside 1-10 range are skipped with warning
- Missing or empty ratings are silently ignored
- Multiple people can rate the same chore

### Step 5: Insert Fresh Rankings
- For each difficulty rating from Sheets:
  - Checks if ranking already exists
  - Creates new Ranking entry if needed
  - Updates rating if ranking already exists
  - Creates audit entries with `changed_by='migration'`
- Returns count of inserted/updated rankings

**Result:** All previous rankings deleted via CASCADE, fresh rankings created from Sheets

## Audit Trail

All operations create audit log entries with the following structure:

### DELETE Operation (when clearing)
```json
{
  "table_name": "chores",
  "operation": "DELETE",
  "record_id": 123,
  "before_values": {
    "id": 123,
    "name": "Clean Kitchen",
    "frequency_in_weeks": 1,
    "created_at": "2026-04-24T10:30:00Z",
    "updated_at": "2026-04-24T10:30:00Z"
  },
  "after_values": null,
  "changed_at": "2026-04-24T10:35:00Z",
  "changed_by": "migration"
}
```

### INSERT Operation (when repopulating)
```json
{
  "table_name": "chores",
  "operation": "INSERT",
  "record_id": 456,
  "before_values": null,
  "after_values": {
    "id": 456,
    "name": "Clean Kitchen",
    "frequency_in_weeks": 1,
    "created_at": "2026-04-24T10:35:00Z",
    "updated_at": "2026-04-24T10:35:00Z"
  },
  "changed_at": "2026-04-24T10:35:00Z",
  "changed_by": "migration"
}
```

### INSERT Operation (ranking from difficulty rating)
```json
{
  "table_name": "rankings",
  "operation": "INSERT",
  "record_id": 789,
  "before_values": null,
  "after_values": {
    "id": 789,
    "person_id": 1,
    "chore_id": 456,
    "rating": 8,
    "created_at": "2026-04-24T10:35:00Z",
    "updated_at": "2026-04-24T10:35:00Z"
  },
  "changed_at": "2026-04-24T10:35:00Z",
  "changed_by": "migration"
}
```

## Recovery from Sync

If you need to recover previous chore data after a sync:

1. **Query Audit Log** - View deleted chores:
   ```bash
   # Use the audit log query endpoint
   GET /api/v1/chores/audit?table_name=chores&operation=DELETE
   ```

2. **Extract Before Values** - Access `before_values` from the audit entry to see what was deleted

3. **Manual Recovery** - If needed, use the audit data to manually restore via API

## Error Handling

### Google Sheets Connection Errors
- If Sheets is unavailable, sync fails with descriptive error
- When running during startup (`SYNC_CHORES_FROM_SHEETS=true`), errors are logged but don't prevent app startup
- When running via CLI, errors cause the command to exit with code 1

### Data Validation Errors
- Invalid frequencies are logged with warning and default to 1
- Empty chore names are skipped with log message
- Duplicate chore names are ignored (last one from Sheets wins)

### Database Errors
- All changes are transactional (all-or-nothing)
- On error, session is rolled back, previous state preserved
- Error details are logged for debugging

## Performance Considerations

- **Large Worksheets**: Sync reads all rows in memory
- **Cascading Deletes**: Can take time with many related records (executions, rankings)
- **Audit Logging**: Each delete/insert operation creates audit entries
- **No Background Task**: Sync is synchronous and blocks during execution

For deployments:
- Run sync during maintenance windows if concerned about downtime
- Consider batch processing if worksheet has 1000+ chores

## Testing

Run the test suite to verify sync functionality:

```bash
python test_sync_chores_from_sheets.py
```

Tests include:
- Mock Google Sheets parsing
- Clearing existing chores with audit logging
- Inserting new chores with validation
- Complete end-to-end sync workflow

## Integration with Other Components

### Rendering Pipeline
- Fetches chores via REST API from database
- Can be called before/after sync without issues
- Returns HTTP 503 if database is unavailable

### API Endpoints
- Summary endpoint (`GET /api/v1/chores/summary`) includes all current chores
- Audit endpoint (`GET /api/v1/chores/audit`) can filter sync operations

### Scheduling
- Sync is independent of the 15-minute data collection cycle
- Can run multiple times without conflicts (all-or-nothing model)

## Configuration

Edit `config.py` to customize:

```python
google_sheets=GoogleSheet(
    sheet_id="1TJoMDv5UUEzY1IYEn3Ce-MmhlnP8ytGQLnx9dg8LFm8",
    chores_worksheet_name="Friday Chores",  # Change this
    seating_worksheet_name="Shabbat Seating",
    json_file=google_sheets_auth_json,
),
```

## Troubleshooting

### "Could not find google-sheets-bot-auth.json"
- Ensure the auth file exists at `google-sheets-bot-auth.json`
- Check that pygsheets is installed: `pip install pygsheets`

### "No chores found in Google Sheets"
- Verify the worksheet name matches config (case-sensitive)
- Check that worksheet has data with headers: "Chore Name", "Frequency (weeks)"

### Sync completes but no chores appear
- Check that `SYNC_CHORES_FROM_SHEETS=true` was set on startup
- Or verify manual CLI command completed without errors
- Query the audit log to see what was inserted

### Cascading deletes fail
- Check foreign key constraints in database
- Verify `ondelete="CASCADE"` is set on Chore relationships
- Look for orphaned records in related tables

## Future Enhancements

Possible improvements:
- Schedule periodic syncs (e.g., daily at midnight)
- Support selective column mapping (e.g., different Sheets format)
- Incremental sync (only update changed rows)
- Rollback functionality (restore to previous state)
- Conflict resolution (merge local changes with Sheets data)
