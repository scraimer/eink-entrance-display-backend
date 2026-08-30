## Context

The chores UI already exposes a plan-date selector and a `selectedPlanDate` variable, but this change explicitly makes today the default plan date and ensures that the initial load path always uses today’s plan. In the backend, the chores summary builder should return a persisted plan for today if one exists, or generate and store it when missing.

## Goals / Non-Goals

**Goals:**
- Make today the initial plan date shown in the Chores Management UI.
- Automatically load today’s chore plan on page load without requiring additional user action.
- Ensure the code that generates the chore list always resolves to today’s plan when no explicit plan date is supplied.

**Non-Goals:**
- Changing plan generation rules or chore balancing logic.
- Supporting arbitrary historical plan defaults beyond today.
- Altering unrelated chore UI workflows such as bulk updates or audit navigation.

## Decisions

### 1. Default UI state to today explicitly

Initialize `selectedPlanDate` to today and update the visible plan-date inputs and label before data loading begins. Ensure the bootstrap logic loads the chores list for the current plan date so the page shows today’s plan on first render.

### 2. Use persisted today plan in summary generation

Update backend plan resolution so `/summary` with no `plan_date` parameter resolves to today and prefers an existing persisted todays plan. If the persisted plan is missing, generate and store it as the default current-plan snapshot.

### 3. Keep html-dev rendering aligned with the same resolved plan date

Treat the html-dev generation path as a consumer of the same summary/plan resolution behavior so rendered lists use today’s plan when it exists and not an unspecified fallback.

### 4. Maintain explicit plan-date selection behavior for operator changes

The user can still choose another date via the plan-date inputs and refresh the selected plan, but the default page entry should always pivot the UI to today.

## Risks / Trade-offs

- If the page is loaded with an explicit hash to the Management or Audit tab, the chores list may not refresh until the user navigates back to Chores. This is acceptable as the request is scoped to the default chore plan load path.
- Persisting today’s plan as the default may expose stale data if the underlying chore state changes mid-day; operators can refresh the plan manually as needed.
- The backend default plan resolution must stay aligned with the UI default to avoid mismatched expectations.
