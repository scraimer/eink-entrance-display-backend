## Why

The Chores Management UI should show the plan for today immediately after the page loads, and the code that builds the chores list should always use today’s persisted plan when one exists. This prevents the UI from displaying an outdated or unspecified plan date and ensures html-dev rendering uses the same current plan that operators expect.

## What Changes

- Default the Management UI plan date to today and load that plan automatically on page load.
- Ensure the chores list generation path always resolves and loads today’s persisted plan if one exists, including html-dev rendering and the `/summary` API path.
- Keep the plan-date inputs synchronized with today’s plan on page initialization.

## Capabilities

### Modified Capabilities
- `chores-ui`: Default plan-date selection and initial chore list load behavior
- `chores-api`: Summary plan resolution and plan-date defaults
- `html-dev`: Rendered list generation should use persisted today plan when available

## Impact

- `assets/chores_ui.html` — default selected plan date, initial page bootstrap, chore summary loading flow
- `src/eink_backend/chores_api.py` — plan_date resolution and persisted plan loading behavior for `/summary`
- Potential test coverage for default plan loading in UI and summary rendering
