## Context

The chores management UI shows a ranking grid when a chore's detail row is expanded. Each person's row contains a score badge — a single integer. The score is computed by `compute_chore_scores()` in `chores_db.py` using the formula:

```
score = execution_count × K − min(days_since_last, RECENCY_CAP)
```

where `K = 1000`, `SCORE_EXECUTION_WINDOW_DAYS = 730`, and `SCORE_RECENCY_CAP_DAYS = 365`.

Currently the API returns `{person_id, score}` pairs. There is no breakdown of the components in the payload, so the UI has no data to display. Adding `execution_count` and `days_since_last` to the SQL query and propagating them to the client is the minimal change needed.

## Goals / Non-Goals

**Goals:**
- Expose `execution_count` and `days_since_last` per person-chore pair in `GET /api/v1/chores/summary`.
- Render those components in the chores UI as an expandable section under each score badge.
- Keep the change purely additive — no existing consumers are broken.

**Non-Goals:**
- Changing the scoring formula or constants.
- Exposing score breakdown on the e-ink display renderer.
- Persisting score breakdown in the database.
- Adding a standalone score breakdown API endpoint.

## Decisions

### D1: Extend SQL query rather than add a separate query

`compute_chore_scores()` already runs a single aggregation query. Adding `COUNT(e.id)` and the raw recency distance to the `SELECT` clause keeps everything in one round-trip. The function returns a `list[ChoreScore]` where `ChoreScore` is a dataclass with named fields (`person_id`, `chore_id`, `score`, `execution_count`, `days_since_last`), replacing the previous anonymous `tuple[int, int, int]`.

Alternative: run a second query after the fact. Rejected — unnecessary database round-trip and more code.

### D2: Return `days_since_last` as the capped value

The UI should display the value actually used in the formula, which is `min(raw_days, RECENCY_CAP)`. This avoids confusion where the displayed breakdown does not reproduce the displayed score. A `None`/`null` is returned when the person has never done the chore (uses the cap as the default).

### D3: Expand on score badge click; collapse on second click (toggle)

A simple inline toggle with a `<details>`-style expand avoids adding a new UI component. A small `▸`/`▾` indicator signals interactivity. The expanded breakdown line uses the formula notation shown in the requirement: `{count} × 1000 − {days} = {score}`.

Alternative: always-visible breakdown text. Rejected — it would clutter the compact rankings grid.

## Risks / Trade-offs

- [Test coverage] Existing tests for `compute_chore_scores` may need updating to unpack the new tuple shape. → Check and update all call sites and tests.
- [UI complexity] Toggle state is managed in plain JS without a framework; could become fragile if the ranking grid is re-rendered while a breakdown is open. → Re-rendering collapses all open breakdowns, which is acceptable behaviour.

## Migration Plan

Purely additive change, no data migration or deployment coordination needed. Deploy normally.
