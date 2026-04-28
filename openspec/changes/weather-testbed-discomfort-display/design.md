## Context

`tools/weather_testbed.py` is a standalone diagnostic script that generates line-chart PNGs for four weather metrics from a synthetic fixture: apparent temperature, UV index, wind speed, and precipitation probability. Currently, every chart annotates both the minimum and maximum values. The goal is to make the charts focus on discomfort — the readings that actually warrant attention — and add a console summary for quick scanning.

## Goals / Non-Goals

**Goals:**
- Define a `has_discomfort(values, *, low=None, high=None) -> bool` helper that accepts a list of floats and optional threshold bounds.
- Add per-metric discomfort detection using that helper with the defined thresholds.
- Print a one-line presence summary per chart before saving it (e.g. `  temperature: discomfort values present`).
- Always annotate the maximum value on every chart.
- For temperature only, additionally annotate the minimum value when it is below the low threshold (8 °C).

**Non-Goals:**
- Changing any production source files under `src/`.
- Visualising discomfort zones as shaded regions or colour gradients on the chart.
- Making thresholds configurable at runtime.

## Decisions

### Single generic `has_discomfort` helper

One function with optional `low` and `high` keyword-only parameters covers all four metrics cleanly without per-metric functions. Metrics that have only an upper threshold (UV, wind, precipitation) pass only `high`; temperature passes both. This avoids four near-identical functions.

**Alternative considered:** per-metric functions (`temperature_has_discomfort`, etc.) — rejected as unnecessarily repetitive for a single-file script.

### Annotate maximum on all charts; minimum only for temperature when discomfort

Keeps annotation logic consistent across charts while respecting the temperature-specific rule from the proposal. For temperature the minimum annotation is only added when the minimum value actually crosses the discomfort threshold (< 8 °C), keeping the chart clean when all values are comfortable.

**Alternative considered:** always annotate minimum on temperature — rejected because it adds noise when there is nothing to flag.

### Console output before each chart save

A short `print` statement per chart gives immediate feedback during development without requiring the user to open image files.

## Risks / Trade-offs

- [Tight coupling of thresholds to fixture data] The synthetic fixture was chosen so discomfort values are present in the data (temperature reaches 33 °C, UV hits 9.5, etc.), making the feature easy to verify visually. If the fixture is later changed to all-comfortable values, the prints will show "no discomfort" and annotated minima will disappear — this is correct behaviour, not a bug.
- [No test coverage] The script is a testbed with no automated tests. The only validation is visual inspection of the PNGs.
