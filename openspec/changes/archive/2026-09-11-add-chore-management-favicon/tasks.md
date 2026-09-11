## 1. Favicon Asset

- [x] 1.1 Create a small, valid `assets/favicon.ico` artwork for the chore management page.
- [x] 1.2 Add an asset-level validation check or test that confirms the ICO can be opened and is not empty.

## 2. Page and Backend Wiring

- [x] 2.1 Add the `/favicon.ico` link metadata to the `<head>` of `assets/chores_ui.html`.
- [x] 2.2 Add a dedicated FastAPI `GET /favicon.ico` route that returns the asset as `image/x-icon` and returns 404 when unavailable.

## 3. Verification

- [x] 3.1 Add focused tests asserting `/chores` includes the favicon declaration.
- [x] 3.2 Add focused tests asserting `/favicon.ico` returns the checked-in bytes, successful status, and `image/x-icon` media type.
- [x] 3.3 Run the focused tests and the relevant project test suite.