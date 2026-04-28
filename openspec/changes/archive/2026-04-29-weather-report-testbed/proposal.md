## Why

The weather reporting code in `weather.py` has no isolated test harness. Verifying the visual output and data-driven behaviour of `weather_report()` requires running the full eink backend against a live API. A self-contained test bed with synthetic `WeatherForecast` data and PNG chart output makes it fast to iterate on the weather display logic without network access.

## What Changes

- Add a standalone test script (`tools/weather_testbed.py`) that constructs a `WeatherForecast` object with hand-crafted hourly data for a day (covering 07:00–14:00).
- The script renders four matplotlib charts as PNG images: temperature, precipitation probability, UV index, and wind speed.
- Each chart has no axes, only the plotted line, and annotates the minimum and maximum values at their respective data points.
- Images are written to `tmp/weather_testbed/` so they can be viewed directly in VS Code.

## Capabilities

### New Capabilities

- `weather-testbed`: A developer tool script that generates diagnostic PNG charts from synthetic `WeatherForecast` data, covering temperature, precipitation, UV index, and wind speed for the 07:00–14:00 window.

### Modified Capabilities

_(none)_

## Impact

- New file: `tools/weather_testbed.py`
- New output directory: `tmp/weather_testbed/` (gitignored)
- Dependency: `matplotlib` (already present or to be added to dev dependencies)
- No changes to production code.
