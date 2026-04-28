## 1. Setup

- [x] 1.1 Create `tools/` directory if it does not already exist
- [x] 1.2 Verify `matplotlib` is available in the dev environment; add to dev dependencies if missing
- [x] 1.3 Create `tmp/weather_testbed/` output directory (or ensure the script auto-creates it)

## 2. Synthetic Fixture

- [x] 2.1 In `tools/weather_testbed.py`, import `WeatherHourly`, `WeatherDaily`, and `WeatherForecast` from `src.eink_backend.weather`
- [x] 2.2 Construct 8 `WeatherHourly` objects for 07:00–14:00 with realistic values for `apparent_temperature`, `temperature_2m`, `rain_mm`, `wind_speed_10m`, `wind_direction_10m`, `uv_index`, and `weather_code`
- [x] 2.3 Construct a parallel list of precipitation probability values (0–100%) for the same 8 hours
- [x] 2.4 Construct a `WeatherDaily` object for tomorrow and a `WeatherHourly` current object
- [x] 2.5 Assemble a `WeatherForecast` from the fixture data

## 3. Chart Rendering Helper

- [x] 3.1 Write a `render_chart(hours, values, output_path, label)` helper function that plots a line chart with no axes
- [x] 3.2 Annotate the minimum value point with its numeric value
- [x] 3.3 Annotate the maximum value point with its numeric value
- [x] 3.4 Save the figure to the given `output_path` as PNG and close it

## 4. Individual Charts

- [x] 4.1 Call `render_chart` with `apparent_temperature` values → `tmp/weather_testbed/temperature.png`
- [x] 4.2 Call `render_chart` with precipitation probability values → `tmp/weather_testbed/precipitation_probability.png`
- [x] 4.3 Call `render_chart` with `uv_index` values → `tmp/weather_testbed/uv_index.png`
- [x] 4.4 Call `render_chart` with `wind_speed_10m` values → `tmp/weather_testbed/wind_speed.png`

## 5. Verification

- [x] 5.1 Run `python tools/weather_testbed.py` from the repo root and confirm all four PNG files are created
- [x] 5.2 Open each PNG in VS Code and visually confirm: line only, no axes, min/max annotated correctly
