## ADDED Requirements

### Requirement: Chores UI HTML is loaded from a file
The system SHALL serve the chores SPA HTML by reading it from `assets/chores_ui.html` at request time, rather than embedding the HTML string in Python source code.

#### Scenario: HTML file exists and is served correctly
- **WHEN** a client requests `GET /chores`
- **THEN** the response SHALL contain the full SPA HTML loaded from `assets/chores_ui.html`

#### Scenario: HTML content is identical to previous inline version
- **WHEN** the chores UI page is loaded
- **THEN** the rendered page SHALL be functionally identical to the previous inline-string implementation
