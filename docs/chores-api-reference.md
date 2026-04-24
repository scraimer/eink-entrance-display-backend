# Chores REST API Reference

## Base URL

```
http://localhost:8000/api/v1/chores
```

## Response Format

All API responses follow a standard format:

```json
{
  "success": true,
  "data": {...},
  "error": null
}
```

- `success` (boolean): Whether the operation succeeded
- `data` (any): Response data (null if no data)
- `error` (string): Error message if `success=false`

## Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK - GET successful |
| 201 | Created - POST successful |
| 204 | No Content - DELETE successful |
| 400 | Bad Request - validation error or limit exceeded |
| 404 | Not Found - resource doesn't exist |
| 500 | Server Error - unexpected error |

## People Endpoints

### Create Person
```
POST /people
```

**Request:**
```json
{
  "name": "John Doe",
  "ordinal": 1,
  "avatar": "john.png"
}
```

**Validation:**
- `name` (required, string, 1-255 chars, unique)
- `ordinal` (required, integer, 1-1000)
- `avatar` (required, string, filename)

**Response (201):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "John Doe",
    "ordinal": 1,
    "avatar": "john.png",
    "created_at": "2026-04-24T10:30:00Z",
    "updated_at": "2026-04-24T10:30:00Z"
  }
}
```

**Errors:**
- 400: `"Name already exists"` - duplicate name
- 400: `"name: ensure this value has at most 255 characters"` - name too long
- 400: Missing required fields

### Get Person
```
GET /people/{id}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "John Doe",
    "ordinal": 1,
    "avatar": "john.png",
    "created_at": "2026-04-24T10:30:00Z",
    "updated_at": "2026-04-24T10:30:00Z"
  }
}
```

**Errors:**
- 404: `"Person not found"` - person doesn't exist

### List People
```
GET /people
```

Returns all people sorted by ordinal. Maximum 1000 records.

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "John Doe",
      "ordinal": 1,
      "avatar": "john.png",
      "created_at": "2026-04-24T10:30:00Z",
      "updated_at": "2026-04-24T10:30:00Z"
    },
    {
      "id": 2,
      "name": "Jane Smith",
      "ordinal": 2,
      "avatar": "jane.png",
      "created_at": "2026-04-24T10:31:00Z",
      "updated_at": "2026-04-24T10:31:00Z"
    }
  ]
}
```

**Errors:**
- 400: `"Result set would exceed 1000 records limit"` - limit exceeded

### Update Person
```
PUT /people/{id}
```

**Request (partial update):**
```json
{
  "ordinal": 5,
  "avatar": "updated.png"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "John Doe",
    "ordinal": 5,
    "avatar": "updated.png",
    "created_at": "2026-04-24T10:30:00Z",
    "updated_at": "2026-04-24T10:35:00Z"
  }
}
```

**Errors:**
- 404: `"Person not found"`
- 400: Validation errors (see Create Person for details)

### Delete Person
```
DELETE /people/{id}
```

**Response (204):** No content

**Cascading Effects:**
- All executions with this executor are deleted
- All rankings for this person are deleted
- All chore states with this executor (next/last) are updated (set to NULL)

**Errors:**
- 404: `"Person not found"`

## Chores Endpoints

### Create Chore
```
POST /chores
```

**Request:**
```json
{
  "name": "Clean Kitchen",
  "frequency_in_weeks": 1
}
```

**Validation:**
- `name` (required, string, 1-255 chars, unique)
- `frequency_in_weeks` (required, integer, minimum 1)

**Response (201):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Clean Kitchen",
    "frequency_in_weeks": 1,
    "created_at": "2026-04-24T10:30:00Z",
    "updated_at": "2026-04-24T10:30:00Z"
  }
}
```

**Errors:**
- 400: `"Chore name already exists"` - duplicate name
- 400: `"frequency_in_weeks: ensure this value is greater than or equal to 1"`

### Get Chore
```
GET /chores/{id}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Clean Kitchen",
    "frequency_in_weeks": 1,
    "created_at": "2026-04-24T10:30:00Z",
    "updated_at": "2026-04-24T10:30:00Z"
  }
}
```

**Errors:**
- 404: `"Chore not found"`

### List Chores
```
GET /chores
```

Returns all chores. Maximum 1000 records.

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "Clean Kitchen",
      "frequency_in_weeks": 1,
      "created_at": "2026-04-24T10:30:00Z",
      "updated_at": "2026-04-24T10:30:00Z"
    }
  ]
}
```

**Errors:**
- 400: Result set limit exceeded

### Update Chore
```
PUT /chores/{id}
```

**Request:**
```json
{
  "frequency_in_weeks": 2
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Clean Kitchen",
    "frequency_in_weeks": 2,
    "created_at": "2026-04-24T10:30:00Z",
    "updated_at": "2026-04-24T10:35:00Z"
  }
}
```

**Errors:**
- 404: `"Chore not found"`
- 400: Validation errors

### Delete Chore
```
DELETE /chores/{id}
```

**Response (204):** No content

**Cascading Effects:**
- ChoreState record is deleted
- All Execution records are deleted
- All Ranking records are deleted

**Errors:**
- 404: `"Chore not found"`

## Execution Endpoints

### Create Execution
```
POST /executions
```

**Request:**
```json
{
  "chore_id": 1,
  "executor_id": 2
}
```

**Validation:**
- `chore_id` (required, integer ≥ 1, must exist)
- `executor_id` (required, integer ≥ 1, must exist)
- Execution date is automatically set to today (UTC)

**Response (201):**
```json
{
  "success": true,
  "data": {
    "execution": {
      "id": 1,
      "chore_id": 1,
      "executor_id": 2,
      "execution_date": "2026-04-24",
      "created_at": "2026-04-24T10:30:00Z"
    },
    "updated_state": {
      "id": 1,
      "chore_id": 1,
      "last_executor_id": 2,
      "last_execution_date": "2026-04-24",
      "next_executor_id": 3,
      "next_execution_date": "2026-05-01",
      "created_at": "2026-04-24T10:30:00Z",
      "updated_at": "2026-04-24T10:30:00Z"
    }
  }
}
```

**Side Effects:**
- Updates ChoreState.last_executor_id and last_execution_date
- Automatically calculates and sets next executor and execution date

**Errors:**
- 400: Invalid chore_id or executor_id
- 400: Invalid execution_date format

### List Executions
```
GET /executions?chore_id=1&executor_id=2
```

**Query Parameters:**
- `chore_id` (integer, optional): Filter by chore
- `executor_id` (integer, optional): Filter by executor

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "chore_id": 1,
      "executor_id": 2,
      "execution_date": "2026-04-24",
      "created_at": "2026-04-24T10:30:00Z",
      "updated_at": "2026-04-24T10:30:00Z"
    }
  ]
}
```

### Override Next Executor
```
PUT /executions/next-executor
```

**Request:**
```json
{
  "chore_id": 1,
  "next_executor_id": 3,
  "next_execution_date": "2026-05-01"
}
```

**Validation:**
- `chore_id` (required, integer ≥ 1)
- `next_executor_id` (optional, integer ≥ 1): Person to assign as next executor
- `next_execution_date` (optional, ISO date format YYYY-MM-DD): When to schedule next execution

**Response (200):**
```json
{
  "success": true,
  "data": {
    "chore_id": 1,
    "next_executor_id": 3,
    "next_execution_date": "2026-05-01"
  }
}
```

**Use Cases:**
- Manually assign a specific person to an upcoming chore
- Override round-robin scheduling
- Handle special cases or conflicts

**Errors:**
- 400: Invalid chore_id or executor_id

## Rankings Endpoints

### Create or Update Ranking
```
POST /rankings
```

**Request:**
```json
{
  "person_id": 1,
  "chore_id": 1,
  "rating": 8
}
```

**Validation:**
- `person_id` (required, integer, must exist)
- `chore_id` (required, integer, must exist)
- `rating` (required, integer, 1-10)

**Response (201 if new, 200 if updated):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "person_id": 1,
    "chore_id": 1,
    "rating": 8,
    "created_at": "2026-04-24T10:30:00Z",
    "updated_at": "2026-04-24T10:30:00Z"
  }
}
```

**Note:** If a ranking already exists for this person+chore combination, it's updated.

**Errors:**
- 400: Invalid rating (must be 1-10)
- 400: Invalid person_id or chore_id

### List Rankings
```
GET /rankings?person_id=1&chore_id=1
```

**Query Parameters:**
- `person_id` (integer, optional): Filter by person
- `chore_id` (integer, optional): Filter by chore

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "person_id": 1,
      "chore_id": 1,
      "rating": 8,
      "created_at": "2026-04-24T10:30:00Z",
      "updated_at": "2026-04-24T10:30:00Z"
    }
  ]
}
```

### Delete Ranking
```
DELETE /rankings/{person_id}/{chore_id}
```

**Response (204):** No content

**Errors:**
- 404: Ranking not found

## Composite Endpoints

### Summary
```
GET /summary
```

**Response (200):**
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
          "id": 1,
          "chore_id": 1,
          "last_executor_id": 1,
          "last_execution_date": "2026-04-23",
          "next_executor_id": 2,
          "next_execution_date": "2026-04-24"
        },
        "rankings": [
          {
            "id": 1,
            "person_id": 1,
            "chore_id": 1,
            "rating": 8
          }
        ]
      }
    ]
  }
}
```

**Use:** Perfect for rendering the e-ink display with complete chore state

### Audit Log
```
GET /audit?table_name=chores&operation=INSERT&record_id=1&since=2026-04-24&until=2026-04-25
```

**Query Parameters:**
- `table_name` (string, optional): Filter by table (people, chores, executions, rankings, chore_state)
- `operation` (string, optional): INSERT, UPDATE, or DELETE
- `record_id` (integer, optional): Filter by specific record
- `since` (ISO date, optional): Start date (inclusive)
- `until` (ISO date, optional): End date (inclusive)

Maximum 1000 records returned.

**Response (200):**
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
      "after_values": {
        "id": 1,
        "name": "Clean Kitchen",
        "frequency_in_weeks": 1,
        "created_at": "2026-04-24T10:30:00Z",
        "updated_at": "2026-04-24T10:30:00Z"
      },
      "changed_at": "2026-04-24T10:30:00Z",
      "changed_by": "migration"
    }
  ]
}
```

**Use Cases:**
- Audit trail of all changes
- Debugging data inconsistencies
- Compliance/historical records
- Recovering deleted data (before_values in DELETE operations)

## Error Response Examples

### Validation Error (400)
```json
{
  "success": false,
  "data": null,
  "error": "Chore name already exists"
}
```

### Not Found (404)
```json
{
  "success": false,
  "data": null,
  "error": "Person not found"
}
```

### Limit Exceeded (400)
```json
{
  "success": false,
  "data": null,
  "error": "Result set would exceed 1000 records limit. Please use pagination with skip/limit parameters."
}
```

### Server Error (500)
```json
{
  "success": false,
  "data": null,
  "error": "Internal server error"
}
```

## Pagination

All list endpoints support pagination:

```
GET /people?skip=0&limit=50
GET /people?skip=50&limit=50  # Next page
GET /people?skip=100&limit=50 # Third page
```

**Limits:**
- Default limit: 50 records
- Maximum limit: 1000 records
- Returns HTTP 400 if total results would exceed 1000

## Timestamp Format

All timestamps are in UTC ISO 8601 format:

- With time: `2026-04-24T10:30:00Z`
- Dates only: `2026-04-24`

## Example Workflow

### 1. Create people
```bash
curl -X POST http://localhost:8000/api/v1/chores/people \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "ordinal": 1, "avatar": "john.png"}'
```

### 2. Create chores
```bash
curl -X POST http://localhost:8000/api/v1/chores/chores \
  -H "Content-Type: application/json" \
  -d '{"name": "Clean Kitchen", "frequency_in_weeks": 1}'
```

### 3. Record an execution
```bash
curl -X POST http://localhost:8000/api/v1/chores/executions \
  -H "Content-Type: application/json" \
  -d '{"chore_id": 1, "executor_id": 1, "execution_date": "2026-04-24"}'
```

### 4. View summary
```bash
curl http://localhost:8000/api/v1/chores/summary
```

### 5. Query audit log
```bash
curl "http://localhost:8000/api/v1/chores/audit?table_name=chores"
```
