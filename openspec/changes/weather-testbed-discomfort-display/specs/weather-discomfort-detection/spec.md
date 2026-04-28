## ADDED Requirements

### Requirement: Discomfort detection function
The script SHALL expose a `has_discomfort(values, *, low=None, high=None) -> bool` function that returns `True` when any value in `values` falls below `low` (if provided) or above `high` (if provided).

#### Scenario: High threshold exceeded
- **WHEN** `has_discomfort([1, 2, 50], high=40)` is called
- **THEN** the function SHALL return `True`

#### Scenario: Low threshold breached
- **WHEN** `has_discomfort([5, 10, 20], low=8)` is called
- **THEN** the function SHALL return `True`

#### Scenario: Both thresholds, all values comfortable
- **WHEN** `has_discomfort([10, 20, 25], low=8, high=28)` is called
- **THEN** the function SHALL return `False`

#### Scenario: No thresholds provided
- **WHEN** `has_discomfort([100, 200])` is called with no `low` or `high`
- **THEN** the function SHALL return `False`

### Requirement: Per-chart discomfort console summary
Before saving each chart PNG, the script SHALL print a one-line message to stdout indicating whether discomfort values are present in that chart's data.

#### Scenario: Discomfort present
- **WHEN** the temperature values include readings above 28 °C
- **THEN** the console output SHALL contain `temperature: discomfort values present`

#### Scenario: No discomfort
- **WHEN** all UV index values are ≤ 3
- **THEN** the console output SHALL contain `uv_index: no discomfort values`

### Requirement: Maximum value always annotated on chart
Every chart SHALL annotate the maximum data point with its numeric value and a visible marker.

#### Scenario: Maximum annotated
- **WHEN** a chart is rendered
- **THEN** the point with the highest value SHALL be marked with a dot and labelled with its value

### Requirement: Temperature minimum annotated when below discomfort threshold
The temperature chart SHALL additionally annotate the minimum data point with its value and a marker, but only when that minimum is below 8 °C.

#### Scenario: Cold minimum present
- **WHEN** the minimum temperature value is below 8 °C
- **THEN** the minimum point SHALL be marked with a dot and labelled with its value

#### Scenario: Comfortable minimum not annotated
- **WHEN** the minimum temperature value is 8 °C or above
- **THEN** no minimum annotation SHALL appear on the chart
