## Context

The eink backend fetches live weather data from open-meteo.com and renders it as HTML. The `weather_report()` function in `weather.py` is the core rendering logic, but there is no way to test or visualise its data-driven behaviour without running the full backend. This design covers a lightweight developer tool that bypasses the network and the HTML renderer, instead producing matplotlib PNG charts from a hand-crafted `WeatherForecast` fixture.

## Goals / Non-Goals

**Goals:**
- Produce a standalone Python script (`tools/weather_testbed.py`) runnable from the repo root.
- Construct a `WeatherForecast` with synthetic hourly data spanning at least 07:00–14:00.
- Render four PNG charts (temperature, precipitation probability, UV index, wind speed) into `tmp/weather_testbed/`.
- Each chart: no axes, only the line; min and max points annotated with their values.

**Non-Goals:**
- Modifying `weather_report()` or any production code.
- Automated assertions / pytest integration (this is a visual inspection tool).
- Rendering HTML or the eink layout.
- Fetching any live data.

## Decisions

### Use matplotlib directly

**Decision**: Use `matplotlib` with `Axes.set_axis_off()` to suppress axes.

**Rationale**: matplotlib is the standard Python charting library; it is either already present in the dev environment or trivially added. Alternatives like `plotly` or `bokeh` introduce heavy dependencies and are aimed at interactive/web use, which is unnecessary here.

### Synthetic fixture with realistic values

**Decision**: Hard-code a `WeatherForecast` covering 07:00–14:00 (8 hourly data points) with plausible Israeli summer values.

**Rationale**: The goal is visual inspection of chart rendering logic. Realistic values (e.g., temperature 22–34°C, UV 1–9) make it easier to spot rendering defects than arbitrary numbers.

### Precipitation probability as a separate field

**Decision**: Add a `precipitation_probability` field to the hourly fixture data for chart purposes; since `WeatherHourly` does not carry this field, the testbed will use raw lists rather than `WeatherHourly` objects for the chart data.

**Rationale**: The open-meteo API provides `precipitation_probability` as an hourly variable but the current `WeatherHourly` dataclass omits it (the production code doesn't use it). Rather than modifying the dataclass, the testbed holds the probability list alongside the `WeatherForecast`.

### Output directory

**Decision**: Write PNGs to `tmp/weather_testbed/` which is already gitignored (`tmp/`).

**Rationale**: Keeps generated artefacts out of version control with zero configuration.

## Risks / Trade-offs

- **matplotlib not installed** → Mitigation: script prints a clear error and exits; README note instructs `pip install matplotlib`.
- **WeatherHourly dataclass changes** → Mitigation: testbed constructs objects directly so type errors surface immediately at import time.

## Migration Plan

No migration needed — this is a new developer tool only.
