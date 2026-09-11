## ADDED Requirements

### Requirement: Chore management page declares a favicon
The HTML document returned by `GET /chores` SHALL include a favicon link in its `<head>` that references `/favicon.ico` and identifies the asset as an ICO image.

#### Scenario: Chore page includes favicon metadata
- **WHEN** a client requests `GET /chores`
- **THEN** the HTML response SHALL contain a `<link rel="icon">` declaration whose href is `/favicon.ico` and whose type is `image/x-icon`

### Requirement: Chore management favicon is served
The application SHALL serve the checked-in chore management favicon at `GET /favicon.ico` with the `image/x-icon` media type.

#### Scenario: Browser requests the favicon
- **WHEN** a client requests `GET /favicon.ico`
- **THEN** the application SHALL return the favicon asset with a successful response and `Content-Type: image/x-icon`

#### Scenario: Favicon asset is unavailable
- **WHEN** the favicon asset cannot be found by the application
- **THEN** `GET /favicon.ico` SHALL return HTTP 404 rather than exposing another asset or returning an HTML page as the icon