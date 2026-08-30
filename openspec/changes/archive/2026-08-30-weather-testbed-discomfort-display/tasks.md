## 1. Discomfort Detection Helper

- [x] 1.1 Add `has_discomfort(values, *, low=None, high=None) -> bool` function to `tools/weather_testbed.py`
- [x] 1.2 Verify function returns `True` when any value exceeds `high` threshold
- [x] 1.3 Verify function returns `True` when any value falls below `low` threshold
- [x] 1.4 Verify function returns `False` when all values are within bounds and when no thresholds are given

## 2. Console Discomfort Summary

- [x] 2.1 Before saving each chart, call `has_discomfort` with the appropriate metric thresholds and print a summary line to stdout
- [x] 2.2 Confirm the four threshold sets: temperature (low=8, high=28), UV (high=3), wind (high=40), precipitation probability (high=40)

## 3. Chart Annotation Updates

- [x] 3.1 Update `render_chart` to always annotate the maximum value with a marker and label
- [x] 3.2 Add an optional `annotate_min_below` parameter (or equivalent) to `render_chart` for conditional minimum annotation
- [x] 3.3 In `main()`, pass `annotate_min_below=8` (or the discomfort minimum check) only for the temperature chart call
- [x] 3.4 Remove any existing unconditional minimum annotation that should now be conditional

## 4. Validation

- [x] 4.1 Run `python tools/weather_testbed.py` and confirm the four PNGs are written without errors
- [x] 4.2 Inspect console output: all four charts print a discomfort presence line
- [x] 4.3 Open `tmp/weather_testbed/temperature.png` and confirm max is annotated; no min annotation (fixture min is 22 °C, above 8 °C)
- [x] 4.4 Open the other three PNGs and confirm max is annotated and charts render cleanly
