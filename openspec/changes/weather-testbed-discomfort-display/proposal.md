## Why

The weather testbed currently plots all data points on every chart, making it hard to spot conditions that actually matter. Highlighting discomfort values — the moments where weather is uncomfortable or unsafe — makes the charts immediately actionable at a glance.

## What Changes

- Add a `is_discomfort` detection function for each weather metric, returning whether any values cross the discomfort threshold.
- Print a per-chart presence summary to stdout indicating whether discomfort values exist.
- Modify the chart rendering to mark the **maximum** value on every chart.
- For temperature, also mark the **minimum** value when it falls in the discomfort range (below 8 °C).
- Discomfort thresholds:
  - Temperature: below 8 °C or above 28 °C
  - UV index: above 3
  - Wind speed: above 40 km/h
  - Precipitation probability: above 40 %

## Capabilities

### New Capabilities

- `weather-discomfort-detection`: A per-metric discomfort detection function that evaluates a list of values against defined thresholds and returns a boolean.

### Modified Capabilities

- (none)

## Impact

- `tools/weather_testbed.py` — all changes are confined to this single script.
- No API, database, or dependency changes.
