## Context

The chores system currently stores `next_executor_id` directly in `chore_state`. The next executor is selected by a combination of manual UI setting and a `same_person_next_time` flag. This means fairness is dependent on whoever manages the schedule keeping it balanced — it is not automatic.

People who are in rotation (`in_rotation = true` on the `people` table) should share chores equitably. Aviv (and potentially others) are excluded via `in_rotation = false`.

Chores where the executor never changes (e.g. only one person knows how to do it) need a new mechanism to record the fixed executor, since `next_executor_id` is being removed.

The `same_person_next_time` flag will be retained on `chores` as a semantic indicator that the executor is fixed. However, the actual identity of the fixed executor can no longer be stored in `next_executor_id`. We introduce `fixed_executor_id` on `chore_state` for this.

## Goals / Non-Goals

**Goals:**
- Dynamically compute the next executor for each chore using weighted execution history.
- Score formula: `score = (1000 × execution_count) + (−1 × min(days_since_last_execution, 365))`. Lower score wins.
- Only executions within the last 730 days count toward `execution_count`; older executions are ignored.
- For chores with `same_person_next_time = true`, use `fixed_executor_id` and bypass scoring.
- Expose per-person scores for each chore in the API and chores UI.
- Remove `next_executor_id` column from `chore_state`.
- Add `fixed_executor_id` column to `chore_state` for fixed-executor chores.
- Provide a migration that populates `fixed_executor_id` from the old `next_executor_id` where `same_person_next_time = true`.

**Non-Goals:**
- Changing the scoring formula to incorporate preference `rankings` (leave for a future change).
- Changing how `next_execution_date` is determined.
- Auto-assigning chores or sending notifications.
- Any changes to the auth model or multi-user access.

## Decisions

### 1. Score formula computed in a single SQL query

**Decision:** Compute scores in SQLite using a single query with subqueries, cap the recency term at 365 days, and restrict the execution count to the last 730 days:

```sql
SELECT
    p.id AS person_id,
    c.id AS chore_id,
    COALESCE(COUNT(e.id), 0) * 1000
        - COALESCE(
            MIN(julianday('now') - julianday(MAX(e.execution_date)), 365),
            365
          ) AS score
FROM people p
CROSS JOIN chores c
LEFT JOIN executions e
    ON e.executor_id = p.id
   AND e.chore_id = c.id
   AND julianday('now') - julianday(e.execution_date) <= 730
WHERE p.in_rotation = 1
GROUP BY p.id, c.id
ORDER BY c.id, score ASC
```

- `1000 × count` dominates: a person who did it even once outscores someone who never did it, regardless of recency. Only executions in the last 730 days (2 years) are counted, so very old history no longer inflates a person's score.
- `min(days_since_last_execution, 365)` is a tiebreaker: if two people have the same count, the one who last did it longer ago gets a lower (better) score, but the recency advantage stops growing after 365 days.
- If a person has never done a chore (or has no executions within the window), `days_since_last_execution` is treated as 365 for scoring purposes, which still gives them priority over anyone who has done it at least once.
- Both the 730-day window and the 365-day recency cap are defined as named constants (`SCORE_EXECUTION_WINDOW_DAYS` and `SCORE_RECENCY_CAP_DAYS`) in the code for easy adjustment.

Lower score = higher priority, so score = `1000 × count − min(days_since_last_execution, 365)`. A person who never did it gets `count=0` and `days=365` → score `= -365` (best among zero-count candidates). A person who did it once 1 day ago gets score `= 999`. A person who did it once 365 or more days ago gets score `= 635`. So among equal-count people, the one who did it longer ago wins, up to the 365-day cap.

**Rationale:** Keeps all computation in the DB layer without Python loops over all people × chores. The query is fast for the expected dataset size (< 20 people, < 50 chores, < 5000 executions).

**Alternative considered:** Python-side computation — rejected because it requires fetching all executions into memory and doing group-by in Python, which is more code and slower.

### 2. `fixed_executor_id` column on `chore_state`

**Decision:** Add `fixed_executor_id INTEGER FK→people(id) SET NULL` to `chore_state`. When this is non-null (and `same_person_next_time = true` on the chore), the scoring algorithm is bypassed and this person is always the next executor.

**Rationale:** Keeps the fixed-executor concept close to the chore state row (1:1 with the chore). Avoids a separate table for a simple single-value association.

**Alternative considered:** Store the fixed executor as a column on `chores` itself — rejected because executor identity is state (can change), while `chores` is a definition table.

### 3. Remove `next_executor_id` from `chore_state`

**Decision:** Drop the column via migration. The computed next executor is returned in API responses as a derived value, never stored.

**Migration strategy:**
1. Copy `next_executor_id` → `fixed_executor_id` for rows where `same_person_next_time = true` on the chore.
2. Drop `next_executor_id` (SQLite requires table rebuild; use `CREATE TABLE ... AS SELECT` + rename approach, or add new column and drop old via rename trick).
3. The `next_executor` field in API responses becomes a computed field.

**Rollback:** The migration is destructive (data loss for chores that had a manually set next executor but `same_person_next_time = false`). Before migrating production, a DB backup is required (per deployment checklist).

### 4. API response shape for next executor

**Decision:** The `GET /chores/summary` and related endpoints return:
- `next_executor_id`: computed ID of the person with the lowest score (or `fixed_executor_id` for fixed chores)
- `person_scores`: array of `{person_id, score}` objects for all in-rotation people (omitted for fixed-executor chores)

**Rationale:** The UI needs both the winner and the full score table. Returning them together avoids a second round-trip.

### 5. UI score display

**Decision:** In the Chores tab, each chore row shows a compact score list: person avatar + score for each in-rotation person, sorted by score ascending. Fixed-executor chores show just the executor's avatar with a lock icon or "(fixed)" label.

## Risks / Trade-offs

- [Data loss on migration] Old manually-set `next_executor_id` values for variable-executor chores will be discarded. → Mitigation: document in migration notes; back up DB before running.
- [Performance] The scoring query is a CROSS JOIN. For 20 people × 50 chores it produces 1000 rows — acceptable. → No mitigation needed at current scale.
- [Score gaming] The formula is simple and does not account for difficulty or preference. If a person is assigned many hard chores they will accumulate a high score and be deprioritized even if they're willing. → Accepted for now; rankings integration is a future change.
- [Window boundary] A person who did many chores just outside the 730-day window will temporarily appear as if they never did them, potentially being selected more often than expected for a brief period. → Accepted; the window is deliberately generous (2 years) to smooth this effect.
- [SQLite column removal] SQLite does not support `DROP COLUMN` before version 3.35. The migration must use a table-rebuild approach for older SQLite. → Use the established pattern from `migrate_chores_data.py` (already uses raw sqlite3 for migrations).

## Migration Plan

1. Back up `chores.sqlite`.
2. Run migration:
   a. `ALTER TABLE chore_state ADD COLUMN fixed_executor_id INTEGER REFERENCES people(id) ON DELETE SET NULL`
   b. `UPDATE chore_state SET fixed_executor_id = next_executor_id WHERE chore_id IN (SELECT id FROM chores WHERE same_person_next_time = 1)`
   c. Rebuild `chore_state` without `next_executor_id` (SQLite table-rename approach).
3. Deploy new application code.
4. Verify via `/api/v1/chores/summary` that scores are computed and `next_executor_id` is populated correctly.

**Rollback:** Restore from backup. There is no automated rollback; the migration is one-way.

## Open Questions

- Should the score formula cap the `days_since_last_execution` term (e.g., cap at 365 days) to prevent stale executions from dominating forever? → Yes. Cap at 365 days.
- Should `same_person_next_time` be renamed to `fixed_executor` for clarity, or is the current name acceptable? → Retain existing name to minimize schema churn; semantics are unchanged.
- Should old executions (beyond 2 years) be counted toward `execution_count`? → No. Only executions within the last 730 days count. This prevents very old history from permanently locking someone out of being selected.
