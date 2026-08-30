## Context

The `POST /api/v1/executions` endpoint already performs a round-robin rotation when it sets `next_executor_id`. Currently it queries **all** people ordered by `ordinal` and rotates through the full set.

The household wants to control who is in the rotation from the Chores UI, without code changes. The People management section (Management tab) already supports adding/editing people; it needs an `in_rotation` toggle column.

The relevant rotation logic lives in `src/eink_backend/chores_api.py` inside `perform_execution()`. The data model is in `src/eink_backend/chores_db.py`.

## Goals / Non-Goals

**Goals:**
- Add an `in_rotation` boolean to the `Person` model, API, and UI.
- Filter the rotation pool to only `in_rotation = true` people, ordered by `ordinal`.
- Let operators toggle `in_rotation` from the Chores UI People management section without redeploying.
- Preserve the `same_person_next_time` short-circuit.

**Non-Goals:**
- Separate per-chore rotation pools — all chores share the same pool.
- Changing the ordinal-based rotation order within the pool.
- Any UI changes outside the People management section.

## Decisions

### Decision 1: `in_rotation` flag on Person, not a separate table or hardcoded list

**Options considered:**

- **A) Hardcoded name list in code** — zero DB changes, but requires a deploy to add/remove anyone. Rejected: the user explicitly wants UI-driven control.
- **B) Separate `rotation_members` join table** — maximum flexibility, but over-engineered for a household app with a small fixed set of people.
- **C) `in_rotation` boolean column on `people`** — one column, visible in the existing People UI, easy to toggle. No extra tables.

**Choice: C.** Minimal schema change, naturally surfaced in the existing People management UI.

### Decision 2: Default `in_rotation = true` for all existing people

The migration sets `in_rotation = 1` for all existing rows so the rotation pool does not silently shrink after the deploy. Operators can then disable anyone via the UI.

### Decision 3: Rotation pool is `in_rotation = true` people ordered by `ordinal`

Ordering by `ordinal` is already the established convention for round-robin sequencing throughout the codebase. No new ordering concept is needed.

### Decision 4: Empty pool is a 400 error

If all people have `in_rotation = false`, `perform_execution()` raises HTTP 400 ("No people in the rotation pool"). This is an operator error, not a runtime bug.

## Risks / Trade-offs

- **Default-true migration** — existing people are all defaulted into the rotation. An operator must explicitly opt out anyone not wanted. → Acceptable: the user wants Ariel, Asaf, Alon, Amalya in by default.
- **Shared pool across all chores** — a person removed from rotation is removed from all chores simultaneously. → By design; this is the intended behavior.

## Migration Plan

1. Add `in_rotation INTEGER NOT NULL DEFAULT 1` column to the `people` table via `chores_db.py` schema and a SQL migration.
2. Update `Person` ORM model and all person-related dataclasses/Pydantic schemas.
3. Update `perform_execution()` to filter `in_rotation = true`.
4. Update the Chores UI People table and edit form with a toggle.
5. No downtime required — column has a default so existing rows are immediately valid.
