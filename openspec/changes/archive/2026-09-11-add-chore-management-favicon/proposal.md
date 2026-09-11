## Why

The chore management page currently has no browser icon, so its tab and bookmarks use a generic appearance. Adding a dedicated favicon will make the management interface easier to recognize when it is open alongside other household tools.

## What Changes

- Add a chore-management favicon asset in the application assets.
- Declare the favicon in the `/chores` page HTML.
- Serve the favicon through a dedicated backend route so browsers can retrieve it using the conventional `/favicon.ico` URL.
- Verify the page metadata and favicon response through focused tests.

## Capabilities

### New Capabilities

### Modified Capabilities

- `chores-ui`: The chore management page includes a recognizable favicon and makes it available to browsers through the application.

## Impact

- `assets/chores_ui.html` gains favicon metadata.
- `assets/` gains a new icon file.
- `src/eink_backend/main.py` gains a small static favicon route.
- Existing chore page behavior and APIs remain unchanged; no new runtime dependency is required.