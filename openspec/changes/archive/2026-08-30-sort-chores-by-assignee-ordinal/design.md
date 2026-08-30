## Context

`src/eink_backend/chores.py` currently renders chores by sorting them based on whether an item is assigned, the assignee name string, and frequency. It also performs assignee normalization through `normalize_assigneed()` for avatar selection, which is a render-time hard-coded lookup rather than a database-driven model.

The source of truth for assignee order is the database `people` table, where each person has an `ordinal` value. The e-ink chores list should respect that database order instead of alphabetical name order.

## Goals / Non-Goals

**Goals:**
- Update chores rendering so assigned chores are sorted by `Person.ordinal` from the database.
- Keep unassigned chores last and preserve frequency-based secondary ordering.
- Move assignee ordering logic to use database-derived metadata rather than string normalization.
- Preserve UI avatar selection and display behavior, but derive display names from the actual person names loaded from the DB.

**Non-Goals:**
- Changing the chore list HTML structure or styles beyond sort order.
- Reworking the entire chores data model or API schema.
- Introducing any new external service or dependency.

## Decisions

- `Chore` will gain a database-derived `assignee_ordinal` field in `src/eink_backend/chores.py`.
- `get_chores_from_database()` will build a person lookup from the `people` table that includes both `name` and `ordinal`.
- When a chore has an assigned executor, the renderer will sort on `(not assignee, assignee_ordinal, frequency_in_weeks)` instead of the current alphabetic `assignee` key.
- Unassigned chores remain last by preserving the `not assignee` boolean in the sort key.
- `normalize_assigneed()` will no longer be used for sorting logic. It may remain for selecting avatars if display names still need normalization, but its use should be limited to presentation only.

## Risks / Trade-offs

- [Risk] If `build_chores_summary()` ever returns a chore with an executor name not present in the `people` table, the sort will fall back to unassigned behavior.
  → Mitigation: keep the existing fallback of empty `assignee` and treat missing `ordinal` as a high value so the item sorts after assigned chores.

- [Risk] Adding `assignee_ordinal` to the `Chore` object changes the local data shape.
  → Mitigation: `Chore` is only used in `chores.py`, so this is a low-impact internal change.

- [Risk] The DB fetch for people may add slight overhead during render.
  → Mitigation: this query is already performed to translate executor ids to names, so adding ordinal lookup is effectively zero additional cost.

## Open Questions

- Should `normalize_assigneed()` be removed entirely or retained only for avatar lookup? For this change, the safe path is to leave it available for presentation while removing it from ordering logic.
