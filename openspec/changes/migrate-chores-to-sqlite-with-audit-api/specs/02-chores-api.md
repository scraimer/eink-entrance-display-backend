# Spec: Chores APIs

## Overview

This spec defines all RESTful JSON APIs for managing chores, executions, people, and rankings. All endpoints are routed under `/api/v1/chores/` and return JSON responses.

## Base Response Format

All successful responses use HTTP 200 (or 201 for POST creation) and JSON body:

```json
{
  "success": true,
  "data": { /* response-specific data */ }
}
```

Error responses use appropriate HTTP status and include:

```json
{
  "success": false,
  "error": "Human-readable error message"
}
```

All timestamps are in UTC, ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ).

## Result Set Limits

All endpoints that return lists have a fixed maximum of 1000 records. If a query would return more than 1000 records, the API returns HTTP 400 with the error:

```json
{
  "success": false,
  "error": "Result set exceeds maximum limit of 1000 records. Use filters to narrow your query."
}
```

Clients must use filtering options (date ranges, person_id, chore_id, since/until, etc.) to retrieve additional records.

## ADDED

### People APIs

#### Create Person
`POST /api/v1/chores/people`

Creates a new person.

**Request body:**
```json
{
  "name": "string (required, unique)",
  "ordinal": "integer (required)",
  "avatar": "string (required, filename)"
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Ariel",
    "ordinal": 1,
    "avatar": "ariel.png",
    "created_at": "2026-04-22T10:00:00Z",
    "updated_at": "2026-04-22T10:00:00Z"
  }
}
```

#### Get Person
`GET /api/v1/chores/people/{id}`

Retrieves a single person by ID.

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Ariel",
    "ordinal": 1,
    "avatar": "ariel.png",
    "created_at": "2026-04-22T10:00:00Z",
    "updated_at": "2026-04-22T10:00:00Z"
  }
}
```

#### Update Person
`PUT /api/v1/chores/people/{id}`

Updates a person's details.

**Request body:**
```json
{
  "name": "string (optional)",
  "ordinal": "integer (optional)",
  "avatar": "string (optional)"
}
```

**Response (200 OK):** Same as Get Person

#### Delete Person
`DELETE /api/v1/chores/people/{id}`

Deletes a person. Returns 204 No Content on success.

#### List People
`GET /api/v1/chores/people`

Lists all people, sorted by ordinal.

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "Ariel",
      "ordinal": 1,
      "avatar": "ariel.png",
      "created_at": "2026-04-22T10:00:00Z",
      "updated_at": "2026-04-22T10:00:00Z"
    }
  ]
}
```

### Chores APIs

#### Create Chore
`POST /api/v1/chores/chores`

Creates a new chore definition.

**Request body:**
```json
{
  "name": "string (required, unique)",
  "frequency_in_weeks": "integer (required, >= 1)"
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Clean Kitchen",
    "frequency_in_weeks": 1,
    "created_at": "2026-04-22T10:00:00Z",
    "updated_at": "2026-04-22T10:00:00Z"
  }
}
```

#### Get Chore
`GET /api/v1/chores/chores/{id}`

Retrieves a single chore by ID.

**Response (200 OK):** Same as Create Chore response

#### Update Chore
`PUT /api/v1/chores/chores/{id}`

Updates a chore definition.

**Request body:**
```json
{
  "name": "string (optional)",
  "frequency_in_weeks": "integer (optional)"
}
```

**Response (200 OK):** Same as Get Chore

#### Delete Chore
`DELETE /api/v1/chores/chores/{id}`

Deletes a chore. Returns 204 No Content on success.

#### List Chores
`GET /api/v1/chores/chores`

Lists all chores.

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "Clean Kitchen",
      "frequency_in_weeks": 1,
      "created_at": "2026-04-22T10:00:00Z",
      "updated_at": "2026-04-22T10:00:00Z"
    }
  ]
}
```

### Executions APIs

#### Perform Execution
`POST /api/v1/chores/executions`

Records that a chore was executed. This operation:
1. Creates an execution record with current UTC date
2. Updates chore_state with last_executor_id, last_execution_date
3. Calculates next_executor_id and next_execution_date based on frequency
4. Automatically logs the changes to audit_log

**Request body:**
```json
{
  "chore_id": "integer (required)",
  "executor_id": "integer (required)"
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "execution": {
      "id": 1,
      "chore_id": 1,
      "executor_id": 1,
      "execution_date": "2026-04-22",
      "created_at": "2026-04-22T10:00:00Z"
    },
    "updated_state": {
      "id": 1,
      "chore_id": 1,
      "last_executor_id": 1,
      "last_execution_date": "2026-04-22",
      "next_executor_id": 2,
      "next_execution_date": "2026-04-29",
      "updated_at": "2026-04-22T10:00:00Z"
    }
  }
}
```

**Next Executor Calculation:**
- Sort people by ordinal
- Find position of last_executor_id in sorted list
- next_executor_id = person at (current_position + 1) mod (number of people)
- If tie in rankings, use ordinal for tiebreaking
- next_execution_date = last_execution_date + (frequency_in_weeks * 7 days)

#### List Executions
`GET /api/v1/chores/executions`

Lists execution history with optional filtering.

**Query parameters:**
- `chore_id`: Filter by chore (optional)
- `executor_id`: Filter by executor (optional)
- `since`: Filter to executions on or after this date (YYYY-MM-DD format, optional)
- `until`: Filter to executions on or before this date (YYYY-MM-DD format, optional)

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "chore_id": 1,
      "executor_id": 1,
      "execution_date": "2026-04-22",
      "created_at": "2026-04-22T10:00:00Z"
    }
  ]
}
```

**Note**: Result set limited to maximum 1000 records. Returns HTTP 400 if limit exceeded.

#### Modify Next Executor
`PUT /api/v1/chores/executions/next-executor`

Manually override the next executor and/or next execution date for a specific chore.

**Request body:**
```json
{
  "chore_id": "integer (required)",
  "next_executor_id": "integer (optional)",
  "next_execution_date": "string date format YYYY-MM-DD (optional)"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "chore_id": 1,
    "last_executor_id": 1,
    "last_execution_date": "2026-04-22",
    "next_executor_id": 3,
    "next_execution_date": "2026-04-30",
    "updated_at": "2026-04-22T10:00:00Z"
  }
}
```

### Rankings APIs

#### Create or Update Ranking
`POST /api/v1/chores/rankings`

Creates or updates a person's rating for a chore.

**Request body:**
```json
{
  "person_id": "integer (required)",
  "chore_id": "integer (required)",
  "rating": "integer (required, 1-10)"
}
```

**Response (201 Created or 200 OK):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "person_id": 1,
    "chore_id": 1,
    "rating": 8,
    "created_at": "2026-04-22T10:00:00Z",
    "updated_at": "2026-04-22T10:00:00Z"
  }
}
```

#### List Rankings
`GET /api/v1/chores/rankings`

Lists all rankings with optional filtering.

**Query parameters:**
- `person_id`: Filter by person (optional)
- `chore_id`: Filter by chore (optional)

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "person_id": 1,
      "chore_id": 1,
      "rating": 8,
      "created_at": "2026-04-22T10:00:00Z",
      "updated_at": "2026-04-22T10:00:00Z"
    }
  ]
}
```

#### Delete Ranking
`DELETE /api/v1/chores/rankings/{person_id}/{chore_id}`

Deletes a person's ranking for a chore. Returns 204 No Content on success.

### Composite Endpoints

#### Get Chores Summary
`GET /api/v1/chores/summary`

Returns all chores with their current state and all people's rankings. This is the endpoint used by the rendering pipeline.

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "chores": [
      {
        "id": 1,
        "name": "Clean Kitchen",
        "frequency_in_weeks": 1,
        "state": {
          "last_executor_id": 1,
          "last_execution_date": "2026-04-22",
          "next_executor_id": 2,
          "next_execution_date": "2026-04-29"
        },
        "rankings": [
          {
            "person_id": 1,
            "rating": 8
          },
          {
            "person_id": 2,
            "rating": 5
          }
        ]
      }
    ]
  }
}
```

### Audit APIs

#### Query Audit Log
`GET /api/v1/chores/audit`

Lists audit log entries with optional filtering.

**Query parameters:**
- `table_name`: Filter by table (chores, people, chore_state, executions, rankings, optional)
- `record_id`: Filter by record ID (optional)
- `operation`: Filter by operation (INSERT, UPDATE, DELETE, optional)
- `since`: Filter to changes on or after this timestamp (ISO 8601, optional)
- `until`: Filter to changes on or before this timestamp (ISO 8601, optional)

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "table_name": "chores",
      "operation": "INSERT",
      "record_id": 1,
      "before_values": null,
      "after_values": "{\"id\": 1, \"name\": \"Clean Kitchen\", \"frequency_in_weeks\": 1}",
      "changed_at": "2026-04-22T10:00:00Z",
      "changed_by": "api"
    }
  ]
}
```

**Note**: Result set limited to maximum 1000 records. Returns HTTP 400 if limit exceeded.

## MODIFIED

None

## Removed

None - this is a new API

## Renamed

None
