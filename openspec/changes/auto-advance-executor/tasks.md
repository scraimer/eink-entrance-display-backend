## 1. Database Schema

- [x] 1.1 Add `in_rotation = Column(Boolean, nullable=False, default=True)` to the `Person` ORM model in `src/eink_backend/chores_db.py`
- [x] 1.2 Add a SQL migration that runs `ALTER TABLE people ADD COLUMN in_rotation INTEGER NOT NULL DEFAULT 1` (skip if column exists) in the DB init/migration path

## 2. API — Person Model and Endpoints

- [x] 2.1 Add `in_rotation: bool = True` to `PersonRequest` in `chores_api.py`
- [x] 2.2 Add `in_rotation: bool` to `PersonResponse` in `chores_api.py`
- [x] 2.3 Update `create_person()` to write `in_rotation` from the request onto the `Person` ORM object
- [x] 2.4 Update `update_person()` to write `in_rotation` from the request onto the `Person` ORM object
- [x] 2.5 Update all places that construct a `PersonResponse` to include the `in_rotation` field
- [x] 2.6 Update `peopleMap` construction in audit/summary helpers if they serialize person data

## 3. Execution Logic

- [x] 3.1 In `perform_execution()`, replace the `all_people` query with one filtered by `Person.in_rotation == True`, ordered by `Person.ordinal` ascending
- [x] 3.2 Change the empty-pool error message to "No people in the rotation pool"
- [x] 3.3 Confirm the `same_person_next_time` short-circuit remains intact (no rotation when flag is set)

## 4. Chores UI — People Management

- [x] 4.1 Add an "In rotation" column header to the People table in the Management tab
- [x] 4.2 Render a checkbox (disabled, reflecting current value) in each person row for `in_rotation`
- [x] 4.3 Add an "In rotation" checkbox field to the add-person inline form (checked by default)
- [x] 4.4 Add an "In rotation" checkbox field to the edit-person inline form (pre-populated from current value)
- [x] 4.5 Include `in_rotation` in the `PATCH`/`PUT` person API call when saving the edit form
- [x] 4.6 Update the `people` JS array population to carry `in_rotation` from the API response

## 5. Verify Behavior

- [ ] 5.1 Confirm `GET /api/v1/chores/people` returns `in_rotation` field for each person
- [ ] 5.2 Confirm `POST /api/v1/executions` skips a person with `in_rotation = false` and advances to the next eligible
- [ ] 5.3 Test wrap-around: execute a chore as the last `in_rotation` person — confirm next resolves to first `in_rotation` person
- [ ] 5.4 Confirm `same_person_next_time = true` chores still pin the executor
- [ ] 5.5 Toggle `in_rotation` off for a person via the UI — confirm they disappear from the rotation on the next execution
