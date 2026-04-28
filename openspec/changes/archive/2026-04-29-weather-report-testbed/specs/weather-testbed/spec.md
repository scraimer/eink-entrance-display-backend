## ADDED Requirements

### Requirement: Testbed script generates weather charts from synthetic data
The system SHALL provide a standalone script `tools/weather_testbed.py` that constructs a `WeatherForecast` fixture with pre-loaded hourly data and renders four PNG chart images without making any network requests.

#### Scenario: Script runs without network access
- **WHEN** the script is executed with no arguments
- **THEN** it completes successfully and writes PNG files to `tmp/weather_testbed/` without contacting any external API

#### Scenario: Output directory is created automatically
- **WHEN** `tmp/weather_testbed/` does not exist
- **THEN** the script creates it before writing any files

### Requirement: Synthetic fixture covers 07:00–14:00
The fixture data SHALL contain hourly `WeatherHourly` entries for every hour from 07:00 to 14:00 inclusive (8 data points) with plausible weather values.

#### Scenario: All required hours are present
- **WHEN** the fixture is constructed
- **THEN** timestamps exist for 07:00, 08:00, 09:00, 10:00, 11:00, 12:00, 13:00, and 14:00

### Requirement: Temperature chart
The script SHALL render a PNG chart of `apparent_temperature` values across the 07:00–14:00 window.

#### Scenario: Chart has no axes
- **WHEN** the temperature chart is rendered
- **THEN** no axis lines, tick marks, or labels are visible in the output image

#### Scenario: Min and max are annotated
- **WHEN** the temperature chart is rendered
- **THEN** the minimum and maximum temperature values are annotated at their respective data points with the numeric value displayed

#### Scenario: File is written
- **WHEN** the script completes
- **THEN** `tmp/weather_testbed/temperature.png` exists

### Requirement: Precipitation probability chart
The script SHALL render a PNG chart of precipitation probability (0–100%) across the 07:00–14:00 window.

#### Scenario: Chart has no axes
- **WHEN** the precipitation chart is rendered
- **THEN** no axis lines, tick marks, or labels are visible

#### Scenario: Min and max are annotated
- **WHEN** the precipitation chart is rendered
- **THEN** the minimum and maximum probability values are annotated at their respective data points

#### Scenario: File is written
- **WHEN** the script completes
- **THEN** `tmp/weather_testbed/precipitation_probability.png` exists

### Requirement: UV index chart
The script SHALL render a PNG chart of `uv_index` values across the 07:00–14:00 window.

#### Scenario: Chart has no axes
- **WHEN** the UV index chart is rendered
- **THEN** no axis lines, tick marks, or labels are visible

#### Scenario: Min and max are annotated
- **WHEN** the UV index chart is rendered
- **THEN** the minimum and maximum UV index values are annotated at their respective data points

#### Scenario: File is written
- **WHEN** the script completes
- **THEN** `tmp/weather_testbed/uv_index.png` exists

### Requirement: Wind speed chart
The script SHALL render a PNG chart of `wind_speed_10m` values across the 07:00–14:00 window.

#### Scenario: Chart has no axes
- **WHEN** the wind speed chart is rendered
- **THEN** no axis lines, tick marks, or labels are visible

#### Scenario: Min and max are annotated
- **WHEN** the wind speed chart is rendered
- **THEN** the minimum and maximum wind speed values are annotated at their respective data points

#### Scenario: File is written
- **WHEN** the script completes
- **THEN** `tmp/weather_testbed/wind_speed.png` exists
