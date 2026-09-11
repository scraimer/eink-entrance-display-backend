## Context

The chore management interface is a single HTML document loaded from `assets/chores_ui.html` and returned by the `/chores` endpoint. The backend already serves selected files from `assets/` through explicit routes, but it has no favicon route. The change must remain dependency-free and must not affect the e-ink display templates.

## Goals / Non-Goals

**Goals:**

- Give the chore management page a stable, recognizable browser icon.
- Keep the icon as a checked-in asset that can be replaced without changing application logic.
- Expose the conventional `/favicon.ico` URL with the correct binary media type.
- Cover both the HTML declaration and HTTP response with focused tests.

**Non-Goals:**

- Redesign the chore management header or other visual elements.
- Add favicon variants for the e-ink display pages.
- Add a frontend build step or an external icon dependency.

## Decisions

- **Use a checked-in ICO asset.** The request specifically targets `favicon.ico`, and ICO is broadly supported by browsers. A raster icon avoids introducing a rendering dependency or requiring client-side generation.
- **Declare the icon explicitly in `chores_ui.html`.** The page is returned as-is, so a `<link rel="icon" type="image/x-icon" href="/favicon.ico">` in its `<head>` is deterministic and does not rely on browser probing behavior.
- **Add a dedicated FastAPI route.** The existing CSS route is intentionally limited to CSS media and filenames. A dedicated `/favicon.ico` route can return the icon with `image/x-icon` and a clear 404 when the asset is unavailable, without broadening arbitrary file access.
- **Test at the application boundary.** Tests should assert that `/chores` contains the icon declaration and that `/favicon.ico` returns the checked-in bytes and media type. This catches both wiring errors and accidental asset removal.

## Risks / Trade-offs

- [Browsers cache favicons aggressively] -> Use the stable conventional URL; changing the artwork later may require normal browser cache invalidation or a versioned URL if cache-busting becomes necessary.
- [An invalid or oversized ICO can render inconsistently] -> Keep the asset as a conventional small multi-resolution favicon and validate that it can be opened during focused tests or asset review.
