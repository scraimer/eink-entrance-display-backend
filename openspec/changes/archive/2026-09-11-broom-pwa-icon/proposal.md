## Why

The chore management page's current icon is not reliably recognized as an installable app icon, and it does not represent the chore-focused experience. Replacing it with a high-resolution broom icon and adding the required PWA metadata will improve browser-tab recognition and make installation behavior consistent across supported browsers.

## What Changes

- Replace the current chore management icon artwork with a high-resolution icon depicting the broom emoji `🧹`.
- Provide the icon in the sizes and formats expected by browser tabs, home-screen shortcuts, and PWA manifests.
- Add a web app manifest for the `/chores` application with installable metadata and icon references.
- Add the required document metadata and backend routes for the manifest and icon assets.
- Verify the manifest, icon dimensions, HTML metadata, and application routes with focused tests.

## Capabilities

### New Capabilities

### Modified Capabilities

- `chores-ui`: The chore management page becomes a recognizable, installable PWA using the broom icon and high-resolution app assets.

## Impact

- `assets/chores_ui.html` gains manifest, theme, Apple touch icon, and PWA-related metadata.
- `assets/` gains the manifest and high-resolution broom icon assets.
- `src/eink_backend/main.py` gains explicit routes for the manifest and icon variants.
- Focused UI tests will validate the browser-facing contract; no external runtime dependency is required.