## 1. Broom Icon Assets

- [x] 1.1 Generate stable broom artwork from the `🧹` source as 192x192 and 512x512 PNG assets.
- [x] 1.2 Regenerate `assets/favicon.ico` from the same broom artwork with embedded browser-compatible sizes.
- [x] 1.3 Add asset validation that confirms the PNG dimensions, ICO format, and non-empty icon files.

## 2. PWA Metadata and Serving

- [x] 2.1 Add manifest, theme-color, and Apple touch icon metadata to `assets/chores_ui.html`.
- [x] 2.2 Add `assets/manifest.webmanifest` with standalone display settings, `/chores` start URL, broom icon entries, and install metadata.
- [x] 2.3 Add explicit FastAPI routes for the manifest and 192/512 PNG icon assets with correct media types.
- [x] 2.4 Preserve the `/favicon.ico` route and return the regenerated broom ICO with `image/x-icon`.

## 3. Verification

- [x] 3.1 Add focused tests asserting `/chores` contains all required PWA metadata.
- [x] 3.2 Add focused tests asserting the manifest response parses and references both icon sizes.
- [x] 3.3 Add focused tests asserting all icon routes return valid image content and expected media types.
- [x] 3.4 Run the focused tests and relevant project validation.