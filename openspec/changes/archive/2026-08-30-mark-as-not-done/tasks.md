## 1. Backend reversal flow

- [x] 1.1 Add an API operation that reverses the latest recorded execution for a chore and restores the previous chore state
- [x] 1.2 Update audit logging and stored-plan visibility handling so the reversal is recorded consistently
- [x] 1.3 Add targeted backend tests for successful reversal, missing-reversal failure, and restored state

## 2. Chores UI state switch

- [x] 2.1 Update the chore detail panel to show "Mark as Done" for incomplete chores and "Mark as not Done" for completed chores
- [x] 2.2 Hide the "Done by someone else?" link when the chore is already completed
- [x] 2.3 Wire the new undo action to the backend reversal flow and refresh the chore list after it completes

## 3. Validation

- [x] 3.1 Run the targeted chores API and chores UI tests for the new state transitions
- [x] 3.2 Verify the OpenSpec change is apply-ready with `openspec status --change "mark-as-not-done"`
