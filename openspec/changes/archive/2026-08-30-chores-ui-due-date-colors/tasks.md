## 1. Update Due-Date Badge Color Logic

- [x] 1.1 In `src/eink_backend/chores_ui.py`, update the `dueBadge()` function: change `if (diff <= 7)` from `badge-yellow` to `badge-green`, add `if (diff <= 1)` for `badge-yellow`, and change the default (else) from `badge-green` to `badge-grey`

## 2. Verify

- [x] 2.1 Manually test the Chores UI in the browser to confirm overdue = red, today/tomorrow = yellow, 2–7 days = green, 8+ days = grey
