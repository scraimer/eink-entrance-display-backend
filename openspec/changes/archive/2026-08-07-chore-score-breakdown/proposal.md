## Why

When reviewing chore assignments, household members cannot see why a particular person was selected — the score is displayed as a single opaque number. Making the score breakdown visible helps people understand and trust the fairness system.

## What Changes

- The `person_scores` array in the `GET /api/v1/chores/summary` response will include per-person score component fields alongside the existing `score` value: `execution_count` (number of executions within the scoring window) and `days_since_last` (days since the person last did this chore, capped at the recency cap).
- The Chore Management UI will render each score badge as clickable/expandable, revealing a formatted breakdown line such as `2 × 1000 − 14 = 1986`.

## Capabilities

### New Capabilities

- `chore-score-breakdown`: Per-person score component data exposed via the API and rendered as an expandable breakdown in the chores UI.

### Modified Capabilities

- `chores-api`: The `person_scores` entries in the summary response will include two additional fields: `execution_count` and `days_since_last`.
- `chores-ui`: The score badge in the rankings grid becomes expandable to show the breakdown formula.

## Impact

- `src/eink_backend/chores_db.py` — `compute_chore_scores()` returns component values alongside the computed score.
- `src/eink_backend/chores_api.py` — score assembly propagates component fields into `person_scores`.
- `assets/chores_ui.html` — JS renders score breakdown on click; CSS adds expand affordance.
- No database schema changes required.
- No breaking changes to existing consumers (new fields are additive).
