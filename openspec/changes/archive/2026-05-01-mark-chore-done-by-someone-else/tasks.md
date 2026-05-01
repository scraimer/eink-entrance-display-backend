## 1. UI — Chore Detail Panel

- [x] 1.1 Add a "Done by someone else?" text link to `choreDetailHTML()` in `chores_ui.py`, rendered only when `canMarkDone` is true
- [x] 1.2 Add the inline sub-panel markup (hidden by default): a `<select>` populated with all people, a "Confirm" button, and a "Cancel" link
- [x] 1.3 Pre-select no person in the dropdown (empty/placeholder option) so the Confirm button starts disabled

## 2. JavaScript — Sub-panel Behaviour

- [x] 2.1 Add a `showDoneByOther(choreId)` JS function that reveals the sub-panel and hides the trigger link
- [x] 2.2 Add a `hideDoneByOther(choreId)` JS function that hides the sub-panel and restores the trigger link
- [x] 2.3 Wire the Confirm button's `onclick` to call `markDone(choreId, selectedPersonId)` with the dropdown value
- [x] 2.4 Disable the Confirm button when the dropdown value is empty; enable it on change

## 3. Verification

- [x] 3.1 Manually open the Chores UI, expand a scheduled chore, and verify the "Done by someone else?" link appears
- [x] 3.2 Click the link, verify the sub-panel opens with all people listed and Confirm disabled
- [x] 3.3 Select a person, confirm, and verify the execution is recorded against that person (check Audit Log tab)
- [x] 3.4 Verify the cancel link closes the sub-panel without any API call
- [x] 3.5 Verify the primary "Mark as Done" button still works independently of the sub-panel
