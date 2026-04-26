## 1. Database Migration

- [x] 1.1 Add `ALTER TABLE chores ADD COLUMN same_person_next_time INTEGER NOT NULL DEFAULT 0 CHECK (same_person_next_time IN (0, 1))` migration to `chores_db_tools.py` or a dedicated migration script
- [x] 1.2 Run the migration against `chores.sqlite` and verify the column exists with value `0` for all existing rows

## 2. ORM Model

- [x] 2.1 Add `same_person_next_time = Column(Boolean, nullable=False, default=False)` to the `Chore` model in `chores_db.py`
- [x] 2.2 Update `ChoreData` dataclass in `chores_db.py` to include the `same_person_next_time: bool` field

## 3. API — Chore Endpoints

- [x] 3.1 Add `same_person_next_time: bool = False` to `ChoreRequest` in `chores_api.py`
- [x] 3.2 Add `same_person_next_time: bool` to `ChoreResponse` in `chores_api.py`
- [x] 3.3 Update the `POST /api/v1/chores` handler to persist `same_person_next_time` from the request
- [x] 3.4 Update the `PUT /api/v1/chores/{chore_id}` handler to persist `same_person_next_time` from the request

## 4. Execution Logic

- [x] 4.1 Locate the execution recording logic in `chores_api.py` (or `chores_db.py`) that advances `next_executor_id`
- [x] 4.2 After recording an execution, if `chore.same_person_next_time` is `True`, set `chore_state.next_executor_id = executor_id` instead of advancing to the next person

## 5. Rankings Filtering

- [x] 5.1 In the rankings endpoint handler (and any summary endpoint that returns ranking data), filter out chores where `same_person_next_time` is `True` before building the response

## 6. Chores UI

- [x] 6.1 In `chores_ui.py`, add a "Same person next time" badge/icon in the chores table for rows where `same_person_next_time` is `true` (set via JS after fetching chores)
- [x] 6.2 Add a "Same person next time" checkbox to the inline chore **create** form; default unchecked
- [x] 6.3 Add a "Same person next time" checkbox to the inline chore **edit** form; pre-populated from fetched chore data
- [x] 6.4 Include `same_person_next_time` in the JS payload when creating or updating a chore via the API
- [x] 6.5 In the rankings tab JS rendering, skip/exclude chores where `same_person_next_time` is `true` (server-side filter handles the API response, but add a defensive client-side guard as well)

## 7. Tests

- [x] 7.1 Write a unit/integration test: creating a chore with `same_person_next_time=True` and recording an execution leaves `next_executor_id` unchanged
- [x] 7.2 Write a test: creating a chore with `same_person_next_time=False` and recording an execution does advance `next_executor_id`
- [x] 7.3 Write a test: the rankings endpoint does not include flagged chores
- [x] 7.4 Write a test: `GET /api/v1/chores` response includes `same_person_next_time` for each chore
