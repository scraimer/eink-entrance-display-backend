## 1. Update the Chores Management UI to default to today

- [x] Initialize `selectedPlanDate` to today in `assets/chores_ui.html`.
- [x] Ensure the page bootstrap sets the plan-date label and input values to today.
- [x] Confirm the initial load path calls `loadChores()` using today’s plan date on page load.

## 2. Make server-side summary load today’s persisted plan by default

- [x] In `src/eink_backend/chores_api.py`, verify that `build_chores_summary()` resolves missing `plan_date` to today.
- [x] Ensure the backend returns a persisted plan for today if it exists, or generates and stores it when necessary.
- [x] Update any comments or docstrings to reflect that `/summary` is today-first by default.

## 3. Align html-dev rendering with today’s plan behavior

- [x] Confirm the html-dev generation path ultimately uses `build_chores_summary(plan_date=...)` and will therefore surface today’s plan when no other plan date is selected.
- [x] Add or update any tests needed to validate html-dev uses the current persisted plan snapshot.

## 4. Add verification tests

- [ ] Add a UI test (or manual regression note) to confirm the Chores Management page loads today’s plan automatically on initial page load.
- [x] Add an API test that GET `/summary` without `plan_date` returns today’s persisted plan date.
- [x] Add a render or integration test that html-dev content uses today’s plan when it is persisted.
