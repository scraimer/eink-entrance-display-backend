## Why

The current color coding of due-date badges in the Chores UI is misleading: chores due far in the future show green (which implies "good" or "done"), while chores due imminently show the same yellow as overdue-adjacent ones. The colors should better reflect urgency — neutral for far-off, positive for upcoming, and alarming only for truly urgent or overdue items.

## What Changes

- Due-date badges more than 7 days away change from **green** to **grey** (neutral, no urgency)
- Due-date badges within the next week (2–7 days) change from yellow to **green** (upcoming, worth noticing)
- Due-date badges due today or tomorrow (0–1 days) keep **yellow** (attention needed soon)
- Due-date badges that are overdue remain **red** (no change)

## Capabilities

### New Capabilities
<!-- None -->

### Modified Capabilities
- `chores-ui`: Due-date badge color thresholds and color assignments are changing

## Impact

- `src/eink_backend/chores_ui.py` — the `dueBadge()` JavaScript function and its color logic
- No API changes, no data model changes, no backend changes
