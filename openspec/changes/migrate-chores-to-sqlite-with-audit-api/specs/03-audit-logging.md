# Spec: Audit Logging Implementation

## Overview

This spec defines how audit logging is implemented to track all changes to chores-related tables, enabling both compliance auditing and recovery from accidental changes.

## ADDED

### Audit Log Entry Structure

Each entry in the `audit_log` table records:

- **table_name**: Name of the affected table (chores, people, chore_state, executions, rankings)
- **operation**: Type of change (INSERT, UPDATE, DELETE)
- **record_id**: Primary key of the affected record in the source table
- **before_values**: JSON string containing all column values before the change (null for INSERT)
- **after_values**: JSON string containing all column values after the change (null for DELETE)
- **changed_at**: UTC timestamp when the change was recorded (ISO 8601 format)
- **changed_by**: Identifier of the user or system that made the change

### Tracked Tables

Audit logging applies to:
1. `people` - All changes to person records
2. `chores` - All changes to chore definitions
3. `chore_state` - All changes to chore state (including automatic updates from executions)
4. `executions` - All changes to execution records
5. `rankings` - All changes to ranking records

The `audit_log` table itself is append-only and never modified.

### Before/After Values Format

The `before_values` and `after_values` columns store JSON strings representing all columns of the record at that point in time.

**Example for UPDATE:**
```json
// before_values
{
  "id": 1,
  "name": "Clean Kitchen",
  "frequency_in_weeks": 1,
  "created_at": "2026-04-22T10:00:00Z",
  "updated_at": "2026-04-22T10:00:00Z"
}

// after_values
{
  "id": 1,
  "name": "Clean Kitchen",
  "frequency_in_weeks": 2,
  "created_at": "2026-04-22T10:00:00Z",
  "updated_at": "2026-04-22T11:00:00Z"
}
```

**Example for INSERT:**
```json
// before_values
null

// after_values
{
  "id": 1,
  "name": "Clean Kitchen",
  "frequency_in_weeks": 1,
  "created_at": "2026-04-22T10:00:00Z",
  "updated_at": "2026-04-22T10:00:00Z"
}
```

**Example for DELETE:**
```json
// before_values
{
  "id": 1,
  "name": "Clean Kitchen",
  "frequency_in_weeks": 1,
  "created_at": "2026-04-22T10:00:00Z",
  "updated_at": "2026-04-22T10:00:00Z"
}

// after_values
null
```

### Changed By Field

The `changed_by` field identifies who made the change. For this implementation:

- `"api"` - Change made through the public API
- `"migration"` - Change made during initial data migration from Google Sheets
- `"auto"` - Change made automatically (e.g., auto-calculated next executor from execution API)

Future versions may support user identifiers or system names.

### Implementation Strategy

#### Option 1: SQLite Triggers (Preferred)

Use SQLite triggers to automatically log changes. Create triggers for each table:

```sql
CREATE TRIGGER people_audit_insert
AFTER INSERT ON people
FOR EACH ROW
BEGIN
  INSERT INTO audit_log (table_name, operation, record_id, before_values, after_values, changed_at, changed_by)
  VALUES ('people', 'INSERT', NEW.id, NULL, json_object(...NEW columns...), datetime('now'), 'api');
END;

CREATE TRIGGER people_audit_update
AFTER UPDATE ON people
FOR EACH ROW
BEGIN
  INSERT INTO audit_log (table_name, operation, record_id, before_values, after_values, changed_at, changed_by)
  VALUES ('people', 'UPDATE', NEW.id, json_object(...OLD columns...), json_object(...NEW columns...), datetime('now'), 'api');
END;

CREATE TRIGGER people_audit_delete
AFTER DELETE ON people
FOR EACH ROW
BEGIN
  INSERT INTO audit_log (table_name, operation, record_id, before_values, after_values, changed_at, changed_by)
  VALUES ('people', 'DELETE', OLD.id, json_object(...OLD columns...), NULL, datetime('now'), 'api');
END;
```

**Limitation**: SQLite triggers cannot pass context (e.g., changed_by value) dynamically. Workaround: Use application-level hooks for API calls, triggers only for direct database access.

#### Option 2: Application-Level Hooks (Recommended)

Implement audit logging in the Python application layer:

1. All database operations go through a wrapper function
2. Before INSERT: Serialize all column values, create audit entry
3. Before UPDATE: Capture old values, perform update, create audit entry
4. Before DELETE: Capture old values, perform delete, create audit entry

**Pseudocode:**
```python
def audit_update(table_name, record_id, old_values, new_values, changed_by='api'):
    audit_entry = {
        'table_name': table_name,
        'operation': 'UPDATE',
        'record_id': record_id,
        'before_values': json.dumps(old_values),
        'after_values': json.dumps(new_values),
        'changed_at': datetime.utcnow().isoformat() + 'Z',
        'changed_by': changed_by
    }
    db.execute('INSERT INTO audit_log (...) VALUES (...)', audit_entry)
```

**Benefits**: Full control over `changed_by` context, can include request headers or user info

### Automatic Changes from Executions

When executing a chore (POST /api/v1/chores/executions):
1. Create execution record (logged as INSERT)
2. Update chore_state with calculated values (logged as UPDATE with changed_by='auto')
3. All changes are logged atomically in a single transaction

### Data Retention

- Audit log entries are append-only. Manual deletion of audit entries is not permitted.
- A background cleanup process runs daily and automatically deletes all audit entries older than 365 days.
- Regular backups should be taken before the cleanup window to prevent accidental data loss.
- The cleanup process is non-blocking and does not interfere with API operations.

### Compliance and Recovery

**Audit queries:**
- Find all changes to a specific chore: `SELECT * FROM audit_log WHERE table_name='chores' AND record_id=?`
- Find all changes in a date range: `SELECT * FROM audit_log WHERE changed_at >= ? AND changed_at <= ?`
- Identify who made changes: `SELECT changed_by, COUNT(*) FROM audit_log GROUP BY changed_by`

**Recovery scenarios:**
- Accidental DELETE of chore: `SELECT * FROM audit_log WHERE table_name='chores' AND record_id=? AND operation='DELETE' ORDER BY changed_at DESC LIMIT 1` to get values before deletion
- Track changes to assignments: Join audit_log with chore_state table via before/after values
- Replay operations: Re-execute recorded changes in order for forensic analysis

## MODIFIED

None

## Removed

None - this is a new implementation

## Renamed

None
