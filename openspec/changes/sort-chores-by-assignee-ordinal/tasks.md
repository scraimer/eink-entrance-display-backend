## 1. Data collection

- [x] 1.1 Extend `src/eink_backend/chores.py` `Chore` model to carry the assignee's database ordinal alongside the assignee name
- [x] 1.2 Update `get_chores_from_database()` so it queries `Person.ordinal` from the database and populates the new `assignee_ordinal` field when a chore is assigned
- [x] 1.3 Preserve the current fallback behavior for unassigned chores and missing person records

## 2. Chore rendering

- [x] 2.1 Change `render_chores()` sorting to use `(not c.assignee, c.assignee_ordinal, c.frequency_in_weeks)` instead of sorting by assignee name
- [x] 2.2 Keep unassigned chores at the end of the rendered list
- [x] 2.3 Leave avatar selection for assigned chores intact while removing sort-time dependence on `normalize_assigneed()`

## 3. Verification

- [x] 3.1 Add or update a regression test covering chore ordering by assignee ordinal and frequency tie-breaker
- [x] 3.2 Run the relevant e-ink chores rendering tests or smoke checks
- [x] 3.3 Confirm the updated change proposal, design, and specs files are complete and consistent with the implementation plan
