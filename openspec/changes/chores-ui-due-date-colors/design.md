## Context

The Chores UI renders a due-date badge for each chore via the `dueBadge()` JavaScript function in `src/eink_backend/chores_ui.py`. The current color scheme:

| Condition | Color | Label |
|---|---|---|
| Overdue | Red | "Overdue Nd" |
| Due today | Yellow | "Due today" |
| Due in 1–7 days | Yellow | "In Nd" |
| Due in 8+ days | Green | "In Nd" |
| No date | Grey | "No date" |

The problem: green signals "all good" but it's being applied to everything not yet due, including things due a month away. Yellow is overloaded across "due today" and "due within the week". The revised scheme communicates urgency more clearly through progressive color escalation.

## Goals / Non-Goals

**Goals:**
- Change the color thresholds for the `dueBadge()` function to match the new scheme
- Grey for 8+ days out (neutral, not urgent)
- Green for 2–7 days out (upcoming, take note)
- Yellow for today or tomorrow (act soon)
- Red for overdue (no change)

**Non-Goals:**
- No backend changes
- No API changes
- No data model changes
- No changes to badge text/labels
- No changes to other badge types (purple "Always same", grey "No date")

## Decisions

### Single function edit in `chores_ui.py`

The entire color logic lives in the `dueBadge()` JS function embedded in the Python file. The change is a direct rewrite of the threshold conditions within that function. No new abstractions are needed.

**Current logic:**
```javascript
if (diff < 0)  → badge-red
if (diff === 0) → badge-yellow
if (diff <= 7)  → badge-yellow
else            → badge-green
```

**New logic:**
```javascript
if (diff < 0)  → badge-red   (overdue)
if (diff <= 1)  → badge-yellow (today or tomorrow)
if (diff <= 7)  → badge-green  (within the week)
else            → badge-grey   (more than a week away)
```

This collapses `diff === 0` and `diff === 1` into the same yellow tier, promotes 2–7 days to green, and demotes 8+ days to grey.

## Risks / Trade-offs

- **Risk**: Grey badges may be visually confused with the existing "No date" grey badge.
  → Mitigation: The badge text still shows "In Nd", making the meaning unambiguous. No visual change is needed to the grey style itself.

- **Trade-off**: "Tomorrow" (1 day) was previously yellow; it stays yellow. This is intentional per the spec.
