# Spec: Database Schema for Chores System

## Overview

This spec defines the SQLite database schema for the chores management system, including all tables, columns, constraints, and indexes.

## ADDED

### Table: people

Stores the list of household members who can perform chores.

```sql
CREATE TABLE people (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    ordinal INTEGER NOT NULL,
    avatar TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
```

**Columns:**
- `id`: Unique identifier for the person
- `name`: Full name (must be unique)
- `ordinal`: Sort order for round-robin scheduling (1-N)
- `avatar`: Filename of avatar image in assets/avatars/
- `created_at`: UTC timestamp when record was created (ISO 8601 format)
- `updated_at`: UTC timestamp when record was last modified (ISO 8601 format)

**Indexes:**
- UNIQUE constraint on `name`
- Index on `ordinal` for sorting

**Initial Data:**
Seeds from hardcoded values in current chores.py:
- Ariel (ordinal 1, avatar: ariel.png)
- Asaf (ordinal 2, avatar: asaf.png)
- Amalya (ordinal 3, avatar: amalya.png)
- Alon (ordinal 4, avatar: alon.png)
- Aviv (ordinal 5, avatar: aviv.png)

### Table: chores

Stores chore definitions with their frequency.

```sql
CREATE TABLE chores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    frequency_in_weeks INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
```

**Columns:**
- `id`: Unique identifier for the chore
- `name`: Chore name (must be unique)
- `frequency_in_weeks`: How often this chore should be performed (in weeks)
- `created_at`: UTC timestamp when record was created (ISO 8601 format)
- `updated_at`: UTC timestamp when record was last modified (ISO 8601 format)

**Constraints:**
- frequency_in_weeks must be >= 1

**Indexes:**
- UNIQUE constraint on `name`

### Table: chore_state

Tracks the current state of each chore (last and next execution details).

```sql
CREATE TABLE chore_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chore_id INTEGER NOT NULL UNIQUE,
    last_executor_id INTEGER,
    last_execution_date TEXT,
    next_executor_id INTEGER,
    next_execution_date TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (chore_id) REFERENCES chores(id) ON DELETE CASCADE,
    FOREIGN KEY (last_executor_id) REFERENCES people(id),
    FOREIGN KEY (next_executor_id) REFERENCES people(id)
)
```

**Columns:**
- `id`: Unique identifier for the state record
- `chore_id`: Reference to chore (one-to-one, UNIQUE)
- `last_executor_id`: Reference to person who last executed this chore (nullable until first execution)
- `last_execution_date`: Date when chore was last executed (nullable, ISO 8601 format)
- `next_executor_id`: Reference to person scheduled to execute next (nullable)
- `next_execution_date`: Date when chore is scheduled to be executed next (nullable, ISO 8601 format)
- `created_at`: UTC timestamp when record was created (ISO 8601 format)
- `updated_at`: UTC timestamp when record was last modified (ISO 8601 format)

**Constraints:**
- One state record per chore (UNIQUE on chore_id)
- FOREIGN KEY: chore_id must exist in chores table (CASCADE on delete)
- FOREIGN KEY: last_executor_id and next_executor_id must exist in people table (if not null)

**Indexes:**
- Primary key index on chore_id for lookups

### Table: executions

Historical log of every time a chore was executed.

```sql
CREATE TABLE executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chore_id INTEGER NOT NULL,
    executor_id INTEGER NOT NULL,
    execution_date TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (chore_id) REFERENCES chores(id) ON DELETE CASCADE,
    FOREIGN KEY (executor_id) REFERENCES people(id)
)
```

**Columns:**
- `id`: Unique identifier for the execution record
- `chore_id`: Reference to chore that was executed
- `executor_id`: Reference to person who executed it
- `execution_date`: Date of execution (ISO 8601 format)
- `created_at`: UTC timestamp when record was created (ISO 8601 format)

**Constraints:**
- FOREIGN KEY: chore_id must exist in chores table (CASCADE on delete)
- FOREIGN KEY: executor_id must exist in people table

**Indexes:**
- Composite index on (chore_id, execution_date) for retrieving execution history
- Index on executor_id for finding person's recent executions

### Table: rankings

Stores each person's preference rating (1-10) for each chore.

```sql
CREATE TABLE rankings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id INTEGER NOT NULL,
    chore_id INTEGER NOT NULL,
    rating INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(person_id, chore_id),
    FOREIGN KEY (person_id) REFERENCES people(id) ON DELETE CASCADE,
    FOREIGN KEY (chore_id) REFERENCES chores(id) ON DELETE CASCADE
)
```

**Columns:**
- `id`: Unique identifier for the ranking record
- `person_id`: Reference to person
- `chore_id`: Reference to chore
- `rating`: Preference rating from 1-10 (1 = dislike, 10 = like)
- `created_at`: UTC timestamp when record was created (ISO 8601 format)
- `updated_at`: UTC timestamp when record was last modified (ISO 8601 format)

**Constraints:**
- rating must be between 1 and 10
- UNIQUE (person_id, chore_id) - one ranking per person per chore
- FOREIGN KEY: person_id and chore_id must exist (CASCADE on delete)

**Indexes:**
- Composite unique index on (person_id, chore_id)
- Index on chore_id for fetching all rankings for a chore

### Table: audit_log

Immutable log of all changes to chores-related tables.

```sql
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

**Columns:**
- `id`: Unique identifier for the audit entry
- `table_name`: Name of table that was modified (chores, people, chore_state, executions, rankings)
- `operation`: Type of change (INSERT, UPDATE, DELETE)
- `record_id`: ID of the record that was modified in the source table
- `before_values`: JSON string of all column values before the change (null for INSERT)
- `after_values`: JSON string of all column values after the change (null for DELETE)
- `changed_at`: UTC timestamp when change occurred (ISO 8601 format)
- `changed_by`: User or system that made the change (e.g., "api", "migration", "user@example.com")

**Constraints:**
- Append-only (no UPDATE or DELETE allowed on audit_log itself)
- before_values null if operation = INSERT
- after_values null if operation = DELETE

**Indexes:**
- Index on (table_name, record_id) for auditing specific records
- Index on changed_at for time-range queries

## MODIFIED

None

## Removed

None - this is a new schema

## Renamed

None
