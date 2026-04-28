## Why

The discomfort detection added in the previous change tells us *whether* uncomfortable conditions exist, but not *when*. Adding vertical markers at the first and last hours within each discomfort zone makes it immediately obvious how long a discomfort window lasts and exactly when it starts and ends.

## What Changes

- Compute the first and last index in the data series where a value is in the discomfort range.
- Draw a vertical dashed line at each of those positions on the chart.
- Label each vertical line with the hour string (e.g. "09:00") so the viewer can read off the discomfort window without counting data points.
- When no discomfort values exist, no markers are drawn (behaviour is identical to before for comfortable conditions).

## Capabilities

### New Capabilities

- `discomfort-zone-markers`: Per-chart vertical line markers at the start and end of the discomfort zone, each labelled with the corresponding hour.

### Modified Capabilities

- `weather-discomfort-detection`: The existing `render_chart` signature must accept discomfort zone boundary information so the chart helper can draw the markers.

## Impact

- `tools/weather_testbed.py` — all changes are confined to this single script.
- No API, database, or dependency changes.
