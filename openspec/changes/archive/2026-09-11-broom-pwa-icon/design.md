## Context

The `/chores` endpoint returns a standalone HTML SPA from `assets/chores_ui.html`. It currently references a single ICO asset, but the page has no web app manifest, no install metadata, and no high-resolution PNG icon variants. The backend serves browser assets through explicit FastAPI routes, so PWA resources need dedicated routes rather than a broad static-file mount.

## Goals / Non-Goals

**Goals:**

- Make `/chores` recognizable as an installable web app through a valid manifest and document metadata.
- Use the broom emoji `🧹` as the visual source for all app icons.
- Provide at least 192x192 and 512x512 PNG icons, plus a compatible ICO fallback.
- Serve each resource with an explicit route and correct media type.
- Validate manifest structure, icon dimensions, HTML metadata, and route responses.

**Non-Goals:**

- Add offline caching or a service worker. Installability metadata and icons are the requested scope; offline behavior is a separate capability.
- Change the chore application UI, API behavior, or e-ink display templates.
- Add a frontend build pipeline or external icon-generation dependency.

## Decisions

- **Use a web app manifest plus link metadata.** A manifest is the browser-recognized source for app name, display mode, theme color, and install icons. The HTML will reference it with `rel="manifest"` and include `apple-touch-icon` and theme-color metadata for platform coverage.
- **Provide 192x192 and 512x512 PNG assets.** These are the standard installable-PWA icon sizes and preserve the broom artwork at sufficient resolution for home-screen and launcher use. The manifest will declare both as `purpose: "any maskable"`.
- **Retain an ICO fallback.** The existing `/favicon.ico` browser convention remains useful for tabs and legacy clients, but its artwork will be regenerated from the same broom source at multiple embedded sizes.
- **Use explicit FastAPI routes.** Dedicated routes for the manifest and each icon keep the current asset-serving security boundary and allow precise media types, instead of exposing arbitrary files from `assets/`.

## Risks / Trade-offs

- [Emoji rendering can vary by platform] -> Render the broom into fixed PNG and ICO assets during implementation so browsers receive stable pixels rather than a platform-dependent text glyph.
- [Manifest metadata alone does not provide offline support] -> Keep service-worker/offline behavior explicitly out of scope and avoid implying that the app works offline.
- [Browsers cache icons and manifests] -> Keep stable URLs and validate the response contents; future artwork changes can use normal deployment cache invalidation if needed.
