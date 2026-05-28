## 1. API contract and backend implementation

- [x] 1.1 Define request/response models for bulk next-due-date updates (chore IDs list, due date, per-item results).
- [x] 1.2 Add a chores API endpoint for bulk next-due-date updates with validation for required fields and input limits.
- [x] 1.3 Implement bulk update persistence logic in the chores data layer and return per-chore success/failure details.
- [x] 1.4 Add backend tests for success, empty selection validation, invalid due date validation, and partial-failure responses.

## 2. Chores UI multi-select and bulk action

- [x] 2.1 Add row selection UI and selection state management (including clear selection behavior) in the chores page.
- [x] 2.2 Add bulk due-date controls (single date input + apply action) and disable/block submit when nothing is selected.
- [x] 2.3 Wire bulk submit to the new API endpoint and send selected chore IDs with one chosen due date.
- [x] 2.4 Refresh chore data after completion and show user feedback for full success and partial-failure outcomes.

## 3. Verification and rollout readiness

- [x] 3.1 Add/update integration coverage for end-to-end bulk due-date update flows across API and UI behavior.
- [x] 3.2 Perform manual verification in the chores page for select-many, submit, and error handling scenarios.
- [x] 3.3 Document any API contract additions in developer docs if endpoint semantics are newly introduced.