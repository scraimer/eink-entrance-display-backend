## ADDED Requirements

### Requirement: Chore management page declares a favicon
The HTML document returned by `GET /chores` SHALL include a favicon link in its `<head>` that references `/favicon.ico` and identifies the asset as an ICO image.

#### Scenario: Chore page includes favicon metadata
- **WHEN** a client requests `GET /chores`
- **THEN** the HTML response SHALL contain a `<link rel="icon">` declaration whose href is `/favicon.ico` and whose type is `image/x-icon`

### Requirement: Chore management page declares installable PWA metadata
The HTML document returned by `GET /chores` SHALL reference `/manifest.webmanifest` with `rel="manifest"`, declare a theme color, and declare `/icons/icon-192.png` as an Apple touch icon.

#### Scenario: Chore page includes PWA metadata
- **WHEN** a client requests `GET /chores`
- **THEN** the HTML response SHALL contain manifest, theme-color, and Apple touch icon metadata with the specified resource paths

### Requirement: Chore management manifest describes the broom app
The application SHALL serve `GET /manifest.webmanifest` as valid web app manifest JSON with an app name and short name for chore management, `start_url: "/chores"`, `display: "standalone"`, a theme color, and icon entries for `/icons/icon-192.png` and `/icons/icon-512.png`.

#### Scenario: Browser requests the web app manifest
- **WHEN** a client requests `GET /manifest.webmanifest`
- **THEN** the application SHALL return HTTP 200 with an application manifest media type and valid JSON containing the required install metadata and both icon entries

### Requirement: Chore management provides high-resolution broom icons
The application SHALL serve valid PNG icons at `/icons/icon-192.png` and `/icons/icon-512.png`, and SHALL serve a compatible ICO fallback at `/favicon.ico`. All icon variants SHALL depict the broom emoji `🧹` and the PNG icons SHALL have dimensions matching their filenames.

#### Scenario: High-resolution PNG icons are available
- **WHEN** a browser requests either supported PNG icon path
- **THEN** the application SHALL return HTTP 200 with `image/png` and an image whose dimensions are respectively 192x192 or 512x512

#### Scenario: ICO fallback remains available
- **WHEN** a browser requests `GET /favicon.ico`
- **THEN** the application SHALL return HTTP 200 with `image/x-icon` and a non-empty valid ICO containing the broom artwork