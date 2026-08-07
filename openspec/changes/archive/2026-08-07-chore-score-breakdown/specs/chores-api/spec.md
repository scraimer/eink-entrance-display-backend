## ADDED Requirements

### Requirement: Score breakdown components are included in person_scores entries
Each entry in the `person_scores` array returned by `GET /api/v1/chores/summary` SHALL include two additional fields alongside the existing `score` value:
- `execution_count`: the number of times the person executed this chore within the scoring window (last `SCORE_EXECUTION_WINDOW_DAYS` days).
- `days_since_last`: the number of days since the person last executed this chore, capped at `SCORE_RECENCY_CAP_DAYS`. SHALL be `null` when the person has never executed this chore (in which case the cap value is used in the formula).

The computed `score` SHALL continue to equal `execution_count × 1000 − min(days_since_last, SCORE_RECENCY_CAP_DAYS)` (or `execution_count × 1000 − SCORE_RECENCY_CAP_DAYS` when `days_since_last` is null).

#### Scenario: Summary includes breakdown for person who has done the chore
- **WHEN** a client calls `GET /api/v1/chores/summary` and person A has executed chore X twice in the last two years, most recently 14 days ago
- **THEN** person A's entry in `person_scores` for chore X SHALL include `execution_count: 2`, `days_since_last: 14`, and `score: 1986`

#### Scenario: Summary includes breakdown for person who has never done the chore
- **WHEN** a client calls `GET /api/v1/chores/summary` and person B has never executed chore X
- **THEN** person B's entry in `person_scores` for chore X SHALL include `execution_count: 0`, `days_since_last: null`, and `score: -365` (i.e. 0 × 1000 − 365)

#### Scenario: Fixed-executor chore still returns empty person_scores
- **WHEN** a client calls `GET /api/v1/chores/summary` for a chore with `same_person_next_time: true`
- **THEN** `person_scores` SHALL be an empty array (no breakdown exposed)
