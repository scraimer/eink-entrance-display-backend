## Context

`tools/weather_testbed.py` was updated in the previous change to detect discomfort values and annotate the maximum (and optionally the minimum) on each chart. The `render_chart` function currently accepts an `annotate_min_below` keyword argument but has no mechanism for drawing zone boundary markers.

The new requirement is to draw vertical dashed lines at the **first** and **last** x-positions where a data point is in the discomfort range, and to label each line with the corresponding hour string from the `hours` list.

## Goals / Non-Goals

**Goals:**
- Add a helper `discomfort_zone(values, *, low=None, high=None) -> tuple[int, int] | None` that returns the first and last index of any discomfort point, or `None` when no discomfort exists.
- Extend `render_chart` with a `discomfort_zone` keyword parameter (tuple of two ints) that, when provided, draws two labelled vertical dashed lines.
- Compute the zone in `main()` for each metric and pass it to `render_chart`.

**Non-Goals:**
- Shading the zone between the two lines.
- Marking individual discomfort points (that is left to the existing max/min annotation).
- Making thresholds or line styles configurable at runtime.

## Decisions

### `discomfort_zone` returns indices, not hours

`render_chart` uses integer x-positions internally (`x = list(range(len(hours)))`). Returning indices means `render_chart` can draw the vertical line with `ax.axvline(x=idx)` without any conversion, while still looking up the label via `hours[idx]`.

**Alternative considered:** Return hour strings and let `render_chart` find the index — rejected because the chart doesn't expose a reverse lookup from label to x.

### Single `discomfort_zone` parameter carrying both bounds

Passing `(start_idx, end_idx)` as one tuple keeps the `render_chart` signature clean. `None` means "no zone", a tuple of two equal values means the zone is a single hour (single pair of coincident lines, or just one line — implementation may de-duplicate).

**Alternative considered:** Two separate `discomfort_start` / `discomfort_end` parameters — rejected as more verbose with no benefit.

### Vertical dashed line style

`ax.axvline` with `linestyle="--"`, a muted colour (e.g. `#f59e0b` amber), and `alpha=0.7` is visually distinct from the data line without being distracting. The hour label is placed at the top of the axes using a small text annotation.

## Risks / Trade-offs

- [Label collision with max annotation] If the discomfort boundary coincides with the maximum, the hour label and the max value annotation may overlap. Mitigation: offset the hour label to the opposite side of the line (left for start, right for end).
- [Start == End edge case] When only one data point is in discomfort, start and end are the same index. Drawing two coincident lines is harmless but redundant; the implementation may draw only one line in this case.
