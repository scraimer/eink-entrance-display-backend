## 1. Discomfort Zone Helper

- [x] 1.1 Add `discomfort_zone(values, *, low=None, high=None) -> tuple[int, int] | None` function to `tools/weather_testbed.py`
- [x] 1.2 Verify it returns `(first_idx, last_idx)` spanning all discomfort points
- [x] 1.3 Verify it returns `(idx, idx)` when only a single point is in discomfort
- [x] 1.4 Verify it returns `None` when no values cross the thresholds

## 2. Update render_chart Signature

- [x] 2.1 Add `discomfort_zone: tuple[int, int] | None = None` keyword parameter to `render_chart`
- [x] 2.2 When `discomfort_zone` is not None, draw a vertical dashed line at `start_idx` labelled with `hours[start_idx]`
- [x] 2.3 When `start_idx != end_idx`, draw a second vertical dashed line at `end_idx` labelled with `hours[end_idx]`
- [x] 2.4 Use a distinct muted style for the lines (dashed, amber-ish colour, partial opacity) so they don't clash with the data line

## 3. Wire Up main()

- [x] 3.1 For each metric in `main()`, call `discomfort_zone(values, ...)` with the correct thresholds (matching those already used for `has_discomfort`)
- [x] 3.2 Pass the result as `discomfort_zone=` to each `render_chart` call

## 4. Validation

- [x] 4.1 Run `/usr/local/bin/python3.12 tools/weather_testbed.py` and confirm no errors
- [x] 4.2 Inspect `tmp/weather_testbed/temperature.png` — expect two vertical lines marking the start and end of the hot zone (above 28 °C)
- [x] 4.3 Inspect `tmp/weather_testbed/wind_speed.png` — expect no vertical lines (all values comfortable)
- [x] 4.4 Inspect UV and precipitation PNGs — expect vertical lines at the discomfort zone boundaries
