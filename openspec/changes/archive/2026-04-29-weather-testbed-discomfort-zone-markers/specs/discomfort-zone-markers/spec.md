## ADDED Requirements

### Requirement: Discomfort zone boundary function
The script SHALL expose a `discomfort_zone(values, *, low=None, high=None) -> tuple[int, int] | None` function that returns a tuple of `(first_idx, last_idx)` where `first_idx` is the lowest index at which any value is in discomfort, and `last_idx` is the highest such index. Returns `None` when no values are in discomfort.

#### Scenario: Zone spans multiple points
- **WHEN** `discomfort_zone([1, 5, 10, 5, 1], high=4)` is called
- **THEN** the function SHALL return `(1, 3)`

#### Scenario: Single discomfort point
- **WHEN** `discomfort_zone([1, 2, 50, 2, 1], high=40)` is called
- **THEN** the function SHALL return `(2, 2)`

#### Scenario: No discomfort
- **WHEN** `discomfort_zone([1, 2, 3], high=10)` is called
- **THEN** the function SHALL return `None`

#### Scenario: Low threshold breach
- **WHEN** `discomfort_zone([5, 10, 20], low=8)` is called
- **THEN** the function SHALL return `(0, 0)`

## MODIFIED Requirements

### Requirement: Maximum value always annotated on chart
Every chart SHALL annotate the maximum data point with its numeric value and a visible marker. Additionally, when a discomfort zone is provided, the chart SHALL draw vertical dashed lines at the first and last discomfort hour, each labelled with the corresponding hour string. When `start_idx == end_idx`, only one vertical line SHALL be drawn.

#### Scenario: Maximum annotated
- **WHEN** a chart is rendered
- **THEN** the point with the highest value SHALL be marked with a dot and labelled with its value

#### Scenario: Discomfort zone markers drawn
- **WHEN** `render_chart` is called with `discomfort_zone=(2, 5)` and `hours=["07:00","08:00","09:00","10:00","11:00","12:00"]`
- **THEN** a vertical dashed line SHALL appear at x-position 2 labelled "09:00" and another at x-position 5 labelled "12:00"

#### Scenario: Single-point discomfort zone
- **WHEN** `render_chart` is called with `discomfort_zone=(3, 3)`
- **THEN** exactly one vertical dashed line SHALL be drawn at x-position 3

#### Scenario: No discomfort zone
- **WHEN** `render_chart` is called without `discomfort_zone` (or `discomfort_zone=None`)
- **THEN** no vertical lines SHALL appear on the chart
