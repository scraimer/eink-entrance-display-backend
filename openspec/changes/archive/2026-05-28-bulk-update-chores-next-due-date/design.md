## Context

The chores page currently supports per-chore editing, which is inefficient when many chores need the same scheduling adjustment. The change introduces a bulk interaction spanning UI selection state, API contract, and batched persistence updates. Existing behavior for single-chore editing must remain intact.

## Goals / Non-Goals

**Goals:**
- Let users select multiple chores in the chores table.
- Let users choose one date and apply it to all selected chores in one action.
- Execute updates through one API request with clear success/failure reporting.
- Keep UI and backend validation consistent (valid date, at least one chore selected).

**Non-Goals:**
- Redesigning the chores page layout beyond minimal controls required for bulk update.
- Changing chore rotation/execution logic, ranking rules, or person assignment semantics.
- Introducing database schema changes.

## Decisions

1. Add explicit multi-select state in the chores UI.
   - Rationale: Checkbox-based row selection is predictable, accessible, and easy to combine with table workflows.
   - Alternative considered: Shift-click range selection only. Rejected because it is less discoverable and harder on touch devices.

2. Add a dedicated bulk-update API operation for next due date.
   - Rationale: One endpoint with a list of chore IDs and a shared due date keeps client behavior simple and enables server-side atomicity or structured partial results.
   - Alternative considered: Client loops existing single-update endpoint. Rejected because it increases round trips, complicates error handling, and can leave UI in inconsistent intermediate states.

3. Return per-chore outcome details when not all updates succeed.
   - Rationale: The UI can report exactly which chores failed and preserve user trust.
   - Alternative considered: Fail the whole operation without detail. Rejected because debugging and recovery are poor for users.

4. Refresh chores data from authoritative API response after bulk update.
   - Rationale: Prevents stale rows and avoids drift between optimistic UI state and persisted backend state.
   - Alternative considered: Optimistic local patching only. Rejected because it can diverge from server-side validation outcomes.

5. Use strict all-or-nothing semantics with bounded request size and date-only input.
   - Decision: Bulk update requests are transactional (if any chore fails validation/update, no chore is updated).
   - Decision: Maximum chores per request is 10.
   - Decision: The API accepts date-only values (no timestamp) interpreted in local application timezone rules.
   - Rationale: This keeps behavior predictable for users, limits operational risk from large batches, and avoids timezone ambiguity from mixed timestamp formats.
   - Alternative considered: Partial success with per-item commits and timestamp inputs. Rejected because it increases user confusion and timezone edge cases.

## Risks / Trade-offs

- [Large selection payload could be expensive] -> Mitigation: enforce a reasonable max item count and validate input size server-side.
- [Partial success may confuse users] -> Mitigation: show a concise summary with failed chore names/IDs and keep selection for retry.
- [Concurrency with simultaneous edits] -> Mitigation: apply updates with current server-side checks and report conflicts as per-item failures.
- [Additional UI complexity] -> Mitigation: keep controls simple (select all, clear selection, single date picker, apply button).

## Migration Plan

1. Implement backend endpoint and tests for bulk next-due-date update.
2. Implement UI selection and bulk action controls behind existing chores page.
3. Add/adjust integration tests covering successful and partial-failure flows.
4. Deploy normally (no schema migration).
5. Rollback strategy: revert to previous release; no data backfill required because only normal chore due-date fields are updated.

## Open Questions

None. Resolved in Decisions section:
- All-or-nothing transaction semantics.
- Maximum 10 chores per bulk request.
- Date-only API input format.