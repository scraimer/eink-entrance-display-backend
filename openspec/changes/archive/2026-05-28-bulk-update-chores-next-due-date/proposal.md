## Why

Updating next due dates one chore at a time is slow and error-prone when multiple chores need to move to the same date. A bulk date update flow makes recurring schedule adjustments fast and consistent.

## What Changes

- Add multi-select controls in the chores page so users can select more than one chore at once.
- Add a single date input/action that applies one chosen next due date to all selected chores.
- Add API support for bulk next-due-date updates in one request, including validation and partial-failure reporting.
- Refresh chores UI state after completion so updated due dates are immediately visible.

## Capabilities

### New Capabilities
- `bulk-update-next-due-date`: Apply one chosen next due date to multiple chores in a single user action and API call.

### Modified Capabilities
- `chores-ui`: Add bulk selection and bulk date update behavior to the chores page.
- `chores-api`: Add or extend endpoint behavior to support updating next due dates for multiple chore IDs in one operation.

## Impact

- Affected code: chores UI rendering/interaction in `src/eink_backend/chores_ui.py` and related client-side logic; chores API handlers and persistence path in `src/eink_backend/chores_api.py` and data layer modules.
- API: new or extended bulk update endpoint contract for next due dates.
- Data: updates existing chore records only; no schema migration expected.
- Testing: add API tests for validation and result reporting, plus UI behavior coverage for multi-select and bulk submit.