# Architecture Overview

This document describes how the code in `src/eink_backend` is organized, how requests move through the system, and how the major components depend on each other.

## Purpose

The backend renders content for an e-ink display. It combines several data sources:

- local Shabbat/zmanim data
- weather forecasts
- Google Calendar events
- Google Sheets data for chores
- Google Sheets data for seating assignments

It then fills an HTML template, renders that HTML to an image, and serves either the generated HTML or the final PNG files over HTTP.

## Source Layout

The Python package lives under `src/eink_backend`.

| File | Responsibility |
| --- | --- |
| `src/eink_backend/main.py` | FastAPI application, route handlers, orchestration, template selection, HTML generation, image rendering |
| `src/eink_backend/config.py` | Loads secrets and builds strongly-typed configuration objects |
| `src/eink_backend/data_cache.py` | SQLite-backed cache with per-data-type TTL rules |
| `src/eink_backend/efrat_zmanim.py` | Reads local zmanim JSON and picks the nearest relevant Shabbat data |
| `src/eink_backend/weather.py` | Fetches forecast data, normalizes it into dataclasses, and renders weather HTML |
| `src/eink_backend/my_calendar.py` | Reads upcoming Google Calendar events and renders grouped HTML |
| `src/eink_backend/chores.py` | Reads chores from Google Sheets and renders the chores list |
| `src/eink_backend/seating.py` | Reads seat assignments from Google Sheets and rotates selected seats over time |
| `src/eink_backend/render.py` | Shared image-processing helpers for icons and avatars |
| `src/eink_backend/__init__.py` | Package marker; currently empty |

## High-Level System Flow

At a high level, the backend works like this:

1. FastAPI starts.
2. Startup code initializes the SQLite cache.
3. A request arrives for HTML or an image.
4. The app collects the current page data, using cached values when possible.
5. The app selects the appropriate HTML template for the current time.
6. The template is filled with data from the domain modules.
7. If needed, Firefox renders the HTML into a screenshot.
8. The screenshot is converted into black/red/joined output files.
9. The resulting file is returned to the client.

## Component Map

```mermaid
flowchart TD
    Client[Client / browser / e-ink device] --> Main[main.py FastAPI app]

    Main --> Cache[data_cache.py]
    Main --> Zmanim[efrat_zmanim.py]
    Main --> Weather[weather.py]
    Main --> Calendar[my_calendar.py]
    Main --> Chores[chores.py]
    Main --> Seating[seating.py]
    Main --> Render[render.py]

    Weather --> Render
    Calendar --> Render
    Chores --> Render

    Weather --> OpenMeteo[Open-Meteo API]
    Calendar --> GoogleCalendar[Google Calendar API]
    Chores --> GoogleSheets[Google Sheets API]
    Seating --> GoogleSheets

    Zmanim --> ZmanimJson[assets/efrat_zmanim.json]
    Main --> Templates[assets/layout-*.html + CSS]
    Cache --> SQLite[/app/data_cache.db]
    Render --> ImageCache[/image-cache]
    Main --> Output[/tmp/eink-display/*.png]
```

## Startup Flow

The application entrypoint is `src/eink_backend/main.py`.

### FastAPI app setup

`main.py` creates the `FastAPI` app and defines a startup hook:

- `startup_event()` initializes the cache database with `data_cache.init_db()`
- it also removes stale expired cache rows with `data_cache.clean_expired_records()`

This means the cache layer is prepared before the first request is handled.

## Main Request Paths

The HTTP API in `main.py` exposes several routes.

### `/`

Returns a small help payload.

### `/html-dev/{color}`

Generates and returns HTML only. This is mainly a development/debug route.

Flow:

1. parse optional `at` timestamp override
2. call `generate_html_content(color, now)`
3. return the generated HTML directly

### `/render/{color}`

Forces a render pass and writes the PNG output file.

Flow:

1. compute `now`
2. call `render_one_color(color, now)`
3. return a simple status string

### `/eink/{color}`

Returns the generated image path as a file response target.

Behavior:

- sanitizes the color name with `untaint_filename()`
- supports the optional `at` timestamp override
- automatically renders `joined` and `black`
- expects `red` to already exist, otherwise returns `404`

This route is the main runtime route for clients retrieving display images.

### `/image-cache/{filename}`

Serves processed icon/avatar images from `/image-cache`.

### `/css/{filename}`

Serves CSS assets from `/app/assets`.

## End-to-End Render Flow

The core request-to-image pipeline looks like this:

```mermaid
sequenceDiagram
    participant C as Client
    participant M as main.py
    participant DC as data_cache.py
    participant Z as efrat_zmanim.py
    participant W as weather.py
    participant GCal as my_calendar.py
    participant Ch as chores.py
    participant S as seating.py
    participant T as HTML template
    participant F as Firefox screenshot
    participant O as Output PNG

    C->>M: GET /render/{color} or /eink/{color}
    M->>M: collect_data(now)
    M->>DC: cache_or_fetch("zmanim", ...)
    DC-->>M: cached or fresh value
    M->>DC: cache_or_fetch("weather", ...)
    DC-->>M: cached or fresh value
    M->>DC: cache_or_fetch("calendar", ...)
    DC-->>M: cached or fresh value
    M->>DC: cache_or_fetch("chores", ...)
    DC-->>M: cached or fresh value
    M->>DC: cache_or_fetch("seating", ...)
    DC-->>M: cached or fresh value

    Note over DC,Z: fetches call module collectors on cache miss
    DC->>Z: collect_data(now)
    DC->>W: collect_data(now)
    DC->>GCal: collect_data()
    DC->>Ch: collect_data(now)
    DC->>S: collect_data(now)

    M->>M: collect_all_values_of_data(...)
    M->>T: load_template_by_time(now)
    T-->>M: HTML template + required keys
    M->>M: substitute values into HTML
    M->>F: render_html_template_single_color()
    F-->>M: screenshot PNG
    M->>O: convert/copy/crop output file
    M-->>C: rendered file/result
```

## `main.py`: Orchestration Layer

`main.py` is the coordination hub of the application.

### Main responsibilities

#### 1. Validate and normalize request input

- `untaint_filename()` strips unsafe characters from route parameters
- `get_filename()` validates that the requested output color is one of:
  - `red`
  - `black`
  - `joined`

#### 2. Collect page data

`collect_data(now)` gathers all domain data and wraps it in the `PageData` dataclass.

It does not fetch directly. Instead it goes through `data_cache.cache_or_fetch()` for each source:

- `zmanim`
- `weather`
- `calendar`
- `chores`
- `seating`

That gives `main.py` one place where all feature modules come together.

#### 3. Convert domain data into template values

`collect_all_values_of_data(...)` is the main data-merging function.

It takes the results of all domain collectors and builds a single dictionary for template substitution.

This function is responsible for:

- deriving the Hebrew date
- deriving parasha information
- flattening `ShabbatZmanim.times` into template keys
- generating the weather HTML snippet
- generating the chores HTML snippet
- flattening seating data into keys like `seat1`, `seat2`, ...
- adding page-level values such as:
  - `day_of_week`
  - `date`
  - `render_timestamp`
  - `heb_date`
  - `additional_css`
- adding Omer text and visibility flags

#### 4. Choose the page layout

`load_template_by_time(now)` picks one of three HTML templates:

- `layout-shabbat.html` as the default
- `layout-choreday.html` on Friday before 16:00
- `layout-shabbat-seating.html` on Friday evening or around Shabbat lunch time

This is one of the most important pieces of application behavior, because the same backend can produce different display modes depending on time.

#### 5. Inline CSS into the HTML template

`replace_css_link_with_css_content()` rewrites stylesheet links into inline `<style>` blocks.

This matters because the HTML is later rendered via a local browser screenshot flow. Inlining CSS makes the final HTML more self-contained.

#### 6. Render HTML to an image

`render_html_template_single_color()` does the image-generation work:

1. write generated HTML to `/tmp/content.html`
2. invoke Firefox with `--screenshot`
3. save an intermediate screenshot file
4. convert it to monochrome for `red` and `black`
5. copy directly for `joined`
6. crop/clip to device dimensions
7. save the final file under `/tmp/eink-display/{color}.png`

## `config.py`: Configuration and Secrets

`config.py` loads runtime configuration at import time.

### Data model

It uses dataclasses to define typed config sections:

- `GeoLocation`
- `GoogleCalendar`
- `GoogleSheet`
- `Config`

### Load behavior

When the module is imported, it immediately:

1. loads `.secrets`
2. verifies that `google-sheets-bot-auth.json` exists
3. constructs the global `config` object

### Effect on the rest of the system

Other modules import `config.config` and use it directly for:

- Google Calendar API key and calendar ID
- Google Sheets spreadsheet metadata and service-account JSON
- the Efrat latitude/longitude used for weather requests

Because loading happens at import time, missing secrets fail early rather than later during request handling.

## `data_cache.py`: Cache Layer

`data_cache.py` is a small persistence layer around SQLite.

### Storage model

The cache table stores:

- `data_type`
- pickled `data`
- `timestamp`
- `expiration`
- `created_at`

### TTL rules

The `EXPIRATION_HOURS` map controls refresh windows:

- `zmanim`: 24 hours
- `weather`: 1 hour
- `calendar`: 4 hours
- `chores`: 4 hours
- `seating`: 6 hours

### Main API

- `init_db()` creates the table if needed
- `clean_expired_records()` deletes very old expired rows
- `get_cached_data()` returns only unexpired values
- `save_cached_data()` upserts the latest value for a data type
- `cache_or_fetch()` is the entrypoint used by `main.py`

### Role in program flow

The cache layer isolates external calls from the rest of the code. The domain modules do not need to know whether the data is fresh or cached; `main.py` always asks the cache layer first.

## `efrat_zmanim.py`: Local Zmanim Data

This module reads static zmanim data from `assets/efrat_zmanim.json`.

### Main logic

- `find_zmanim_for_day()` filters the JSON records by Gregorian date
- `find_nearest_shabbat_or_yom_tov()` scans forward up to 8 days and picks the nearest Saturday entry
- `kbalat_shabat_from_candle_lighting()` derives a value 5 minutes after candle lighting
- `collect_data()` is the exported wrapper used by `main.py`

### Output shape

It returns `ShabbatZmanim`, which contains:

- `name`
- `times` dictionary with values such as:
  - `candle_lighting`
  - `tzet_shabat`
  - `kabalat_shabbat`
  - `tset_shabat_as_datetime`
  - optional fast-related times

### System role

This is the only source that does not depend on a remote API at runtime.

## `weather.py`: Forecast Collection and Weather HTML

`weather.py` performs two jobs:

1. fetch weather data
2. render the weather fragment inserted into the page template

### Domain models

The weather data is normalized into dataclasses:

- `WeatherHourly`
- `WeatherDaily`
- `WeatherForecast`
- `TemperatureAtTime` is defined but not central to the current flow

### Data collection

`collect_data(now)` delegates to `_collect_data_impl(now)` and catches failures.

`_collect_data_impl(now)`:

- calls Open-Meteo
- requests current, hourly, and daily forecast fields
- builds a `WeatherForecast`
- stores the current conditions, hourly slices, and tomorrow summary

### HTML rendering

`weather_report(weather_forecast, color)` turns the forecast into HTML.

It chooses:

- the current temperature
- a warning icon if the weather is cold enough for a jacket
- a few selected hourly forecast points
- tomorrow’s summary

The function also generates icon paths by calling `render.image_extract_color_channel()` so icons are preprocessed for the target display color.

### Dependencies

`weather.py` depends on:

- `config.py` for geolocation
- `render.py` for icon extraction and recoloring
- external Open-Meteo data

## `my_calendar.py`: Calendar Events to HTML

This module fetches upcoming Google Calendar events and formats them as HTML.

### Main logic

- `get_next_10_events()` creates a Google Calendar client and fetches the next events within a short horizon
- `calendar_render(events)` groups events by day and renders nested HTML lists
- `collect_data()` is the safe wrapper used by `main.py`

### Output behavior

Unlike some other modules, the exported value here is already an HTML string, not a rich dataclass.

The returned value is one of:

- rendered HTML for upcoming events
- `-no calendar data-`
- `-error getting calendar data-`

### System role

This module is simple: it fetches data, groups it by day, and hands `main.py` a ready-to-embed HTML fragment.

## `chores.py`: Chores from Google Sheets

This module loads chore assignments from a spreadsheet and renders them into HTML.

### Domain models

- `Chore`
- `ChoreData`
- `Assignee`

### Data collection

`get_chores_from_spreadsheet()`:

- authorizes with `pygsheets`
- opens the configured spreadsheet
- reads the `Friday Chores` worksheet
- parses each row into a `Chore`

`collect_data(now)` wraps that call and returns `ChoreData`.

### Rendering

`render_chores(chores, now, color)`:

- sorts chores by assignment state, assignee, and frequency
- skips chores whose due date is in the future
- normalizes assignee names with `normalize_assigneed()`
- picks matching avatar filenames
- sends avatar images through `render.image_extract_color_channel()`
- renders the final list HTML

### System role

This module is both a data adapter and a presentation module. It translates spreadsheet rows into Python objects, then translates those objects into HTML ready for template insertion.

## `seating.py`: Rotating Seating Plan

This module computes a seating arrangement from spreadsheet input.

### Domain models

- `Seat`
- `SeatingDataFromSpreadsheet`
- `SeatingData`

### Data collection

`get_seating_from_spreadsheet()`:

- authorizes with `pygsheets`
- reads the `Shabbat Seating` worksheet
- parses rows into `Seat` objects
- extracts a `start_date`

### Rotation logic

`rotate_seats(now, seat_db)` applies the project’s rotation rules:

- compute weeks since the configured start date
- derive how many seating rotations should have happened
- rotate only seats marked as rotatable
- preserve fixed seats in place
- renumber the rotated seats to match their final position

### Output shape

`collect_data(now)` returns `SeatingData`, which `main.py` later flattens into template keys like `seat1`, `seat2`, and so on.

## `render.py`: Shared Image Processing

`render.py` is a support module used by several features.

### Main responsibilities

- cache extracted image assets under `/image-cache`
- download remote images when needed
- handle local `file://` assets
- extract red-only images
- convert icons into black/gray-friendly output
- optionally crop icon images before saving

### Key functions

- `image_extract_color_channel()` is the main public helper
- `extract_red()` isolates red pixels
- `extract_black_and_gray()` converts an image to black/white output using HSV thresholds and dithering-like logic
- `should_download_to_cache()` determines whether cached files should be refreshed

### Who uses it

- `weather.py` uses it for weather icons
- `chores.py` uses it for avatar images
- `main.py` imports it for the test route
- `my_calendar.py` imports `render.INDENT` for HTML formatting consistency

## How the Major Components Connect

### `main.py` as the orchestrator

All major feature modules connect through `main.py`.

- it decides when data is needed
- it decides which template is active
- it decides when to render HTML to PNG
- it owns the route layer

### `data_cache.py` as the fetch gateway

Every remote or semi-static data source is pulled through the cache layer. That gives the system:

- fewer API calls
- stable output during short outages
- a single refresh policy per data type

### Feature modules as data providers

Each feature module has a narrow role:

- `efrat_zmanim.py` provides time/date religious data
- `weather.py` provides forecast data and weather HTML
- `my_calendar.py` provides calendar HTML
- `chores.py` provides chore records and chore HTML
- `seating.py` provides seat assignments

### `render.py` as a shared asset adapter

Several features need images that work on an e-ink display. `render.py` is the shared translation layer between ordinary full-color assets and display-friendly output files.

## Template and Asset Strategy

The visual layout is driven by files in `assets/` rather than by Python-generated HTML pages.

That design has a few consequences:

- Python builds data and fragments
- layout is mostly controlled in HTML and CSS templates
- different moments in the week can reuse the same backend and change only the chosen layout
- the screenshot renderer treats the HTML page as the final render surface

## Important Data Shapes

A few structures are worth knowing when navigating the code:

### `PageData`

Defined in `main.py`, this bundles the current page inputs:

- `zmanim`
- `weather_forecast`
- `calendar_content`
- `chores_content`
- `seating_content`

### Template value dictionary

`collect_all_values_of_data()` converts rich Python objects into a flat dictionary of template placeholders. This is the key boundary between application logic and presentation.

### Generated files

The runtime creates or uses several important filesystem locations:

- `/tmp/content.html` for the current render source
- `/app/tmp/firefox-{color}.png` for the browser screenshot
- `/tmp/eink-display/{color}.png` for the final output
- `/image-cache/*` for processed icons and avatars
- `/app/data_cache.db` for the SQLite cache

## Operational Notes and Caveats

The current code has a few design details worth knowing.

### Import-time secret loading

`config.py` fails immediately if `.secrets` or the Google Sheets JSON file is missing. That is useful in deployment, but it means modules that import config cannot be loaded in a partially configured environment.

### Mixed return styles across modules

Not all collectors return the same kind of result:

- `weather.collect_data()` returns a dataclass or `None`
- `chores.collect_data()` returns `ChoreData`
- `seating.collect_data()` returns `SeatingData`
- `my_calendar.collect_data()` returns an HTML string or an error string

That makes `main.py` responsible for normalizing several different conventions.

### Rendering behavior differs by color

`/eink/{color}` auto-renders `joined` and `black`, but not `red`. If `red` has not already been rendered, the route returns `404`.

### Template keys are flattened dynamically

The template layer depends on key names built at runtime. For example, seating becomes `seat1`, `seat2`, and so on. Missing keys are patched with `[ERR]` placeholders rather than failing the request.

### HTML fragments are built inside feature modules

Calendar, chores, and weather each generate their own HTML snippets. The project therefore mixes domain logic and presentation logic inside the same modules.

## Reading the Code Efficiently

If you are new to the codebase, the best order is:

1. `src/eink_backend/main.py`
2. `src/eink_backend/data_cache.py`
3. `src/eink_backend/config.py`
4. `src/eink_backend/weather.py`
5. `src/eink_backend/chores.py`
6. `src/eink_backend/seating.py`
7. `src/eink_backend/my_calendar.py`
8. `src/eink_backend/efrat_zmanim.py`
9. `src/eink_backend/render.py`

That order follows the runtime flow from outermost request handling toward supporting modules.

## Summary

The backend is organized around one central orchestration module, `main.py`, plus several focused feature modules. The system is intentionally pragmatic:

- data is fetched from local files and external services
- a cache reduces repeated work
- feature modules render their own HTML fragments
- templates decide the page layout for the current time window
- Firefox turns the final HTML into screenshot-based display images
- shared image processing adapts icons and avatars for e-ink output

The most important architectural pattern in the code is this:

**collect domain data -> flatten into template variables -> render HTML -> convert to image -> serve output**
