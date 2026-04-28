"""Weather report test bed.

Generates four diagnostic PNG charts from a synthetic WeatherForecast fixture
covering the 07:00–14:00 window. No network access is required.

Usage:
    python tools/weather_testbed.py

Output is written to tmp/weather_testbed/.
"""
import sys
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Allow running from the repo root without installing the package
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from eink_backend.weather import WeatherDaily, WeatherForecast, WeatherHourly

OUTPUT_DIR = Path("tmp/weather_testbed")


# ---------------------------------------------------------------------------
# Synthetic fixture
# ---------------------------------------------------------------------------

_DATE = datetime(2026, 4, 28)

_HOURLY_DATA = [
    # (hour, apparent_temp, temperature_2m, rain_mm, wind_speed, wind_dir, uv, code)
    (7,  22.0, 21.5, 0.0,  8.0, 270, 1.2, 1),
    (8,  24.5, 23.8, 0.0, 10.0, 265, 3.1, 0),
    (9,  27.0, 26.2, 0.0, 12.0, 260, 5.4, 0),
    (10, 30.0, 29.1, 0.0, 14.0, 255, 7.2, 1),
    (11, 32.5, 31.8, 0.2, 15.5, 250, 8.9, 2),
    (12, 34.0, 33.2, 1.0, 16.0, 248, 9.5, 61),
    (13, 33.5, 32.8, 0.5, 13.0, 250, 8.1, 61),
    (14, 31.0, 30.4, 0.0, 11.0, 255, 6.3, 1),
]

# Precipitation probability (%) — parallel to _HOURLY_DATA
_PRECIP_PROBABILITY = [5, 5, 8, 12, 25, 60, 45, 20]

hourlies: list[WeatherHourly] = [
    WeatherHourly(
        timestamp=_DATE.replace(hour=hour),
        apparent_temperature=apparent_temp,
        temperature_2m=temperature_2m,
        rain_mm=rain_mm,
        wind_speed_10m=wind_speed,
        wind_direction_10m=wind_dir,
        uv_index=uv,
        weather_code=code,
    )
    for hour, apparent_temp, temperature_2m, rain_mm, wind_speed, wind_dir, uv, code
    in _HOURLY_DATA
]

current = WeatherHourly(
    timestamp=_DATE.replace(hour=7),
    apparent_temperature=22.0,
    temperature_2m=21.5,
    rain_mm=0.0,
    wind_speed_10m=8.0,
    wind_direction_10m=270,
    uv_index=1.2,
    weather_code=1,
)

tomorrow = WeatherDaily(
    timestamp=_DATE.replace(day=_DATE.day + 1),
    apparent_temperature_min=18.0,
    apparent_temperature_max=29.0,
    weather_code=2,
)

forecast = WeatherForecast(current=current, hourlies=hourlies, tomorrow=tomorrow)


# ---------------------------------------------------------------------------
# Discomfort detection
# ---------------------------------------------------------------------------

def has_discomfort(
    values: list[float],
    *,
    low: float | None = None,
    high: float | None = None,
) -> bool:
    """Return True if any value falls below *low* or above *high*.

    Thresholds that are None are ignored.
    """
    return any(
        (low is not None and v < low) or (high is not None and v > high)
        for v in values
    )


def discomfort_zone(
    values: list[float],
    *,
    low: float | None = None,
    high: float | None = None,
) -> tuple[int, int] | None:
    """Return (first_idx, last_idx) of discomfort values, or None if none.

    *first_idx* is the lowest index where a value crosses a threshold;
    *last_idx* is the highest such index.
    """
    indices = [
        i for i, v in enumerate(values)
        if (low is not None and v < low) or (high is not None and v > high)
    ]
    if not indices:
        return None
    return (indices[0], indices[-1])


# ---------------------------------------------------------------------------
# Chart helper
# ---------------------------------------------------------------------------

def render_chart(
    hours: list[str],
    values: list[float],
    output_path: Path,
    label: str,
    *,
    annotate_min_below: float | None = None,
    discomfort_zone: tuple[int, int] | None = None,
) -> None:
    """Render a line chart with no axes, annotating the max point always.

    If *annotate_min_below* is given, the minimum point is also annotated
    when its value is strictly below that threshold.

    If *discomfort_zone* is given as ``(start_idx, end_idx)``, vertical
    dashed lines are drawn at those positions, each labelled with the
    corresponding hour string.
    """
    fig, ax = plt.subplots(figsize=(6, 3))

    x = list(range(len(hours)))
    ax.plot(x, values, linewidth=2.5, color="#111827", solid_capstyle="round")

    # Conditionally annotate minimum
    if annotate_min_below is not None:
        min_idx = values.index(min(values))
        min_val = values[min_idx]
        if min_val < annotate_min_below:
            ax.annotate(
                f"{min_val:g}",
                xy=(min_idx, min_val),
                xytext=(0, -18),
                textcoords="offset points",
                ha="center",
                fontsize=10,
                fontweight="bold",
                color="#dc2626",
            )
            ax.plot(min_idx, min_val, "o", color="#dc2626", markersize=6)

    # Always annotate maximum
    max_idx = values.index(max(values))
    max_val = values[max_idx]
    _max_in_discomfort = (
        discomfort_zone is not None
        and discomfort_zone[0] <= max_idx <= discomfort_zone[1]
    )
    _max_color = "#dc2626" if _max_in_discomfort else "#111827"
    ax.annotate(
        f"{max_val:g}",
        xy=(max_idx, max_val),
        xytext=(0, 10),
        textcoords="offset points",
        ha="center",
        fontsize=10,
        fontweight="bold",
        color=_max_color,
    )
    ax.plot(max_idx, max_val, "o", color=_max_color, markersize=6)

    # Discomfort zone boundary markers
    if discomfort_zone is not None:
        start_idx, end_idx = discomfort_zone
        _ZONE_COLOR = "#dc2626"
        _ZONE_LABEL_COLOR = "#111827"
        _ZONE_STYLE = dict(color=_ZONE_COLOR, linestyle="--", linewidth=1.2, alpha=0.75)

        def _draw_zone_line(idx: int, *, label_ha: str) -> None:
            ax.axvline(x=idx, **_ZONE_STYLE)
            ax.text(
                idx + (0.05 if label_ha == "left" else -0.05),
                ax.get_ylim()[1],
                hours[idx],
                ha=label_ha,
                va="top",
                fontsize=8,
                color="#111827",
            )
            val = values[idx]
            ax.plot(idx, val, "o", color=_ZONE_COLOR, markersize=5, zorder=5)
            if idx != max_idx:
                ax.annotate(
                    f"{val:g}",
                    xy=(idx, val),
                    xytext=(0, -14),
                    textcoords="offset points",
                    ha="center",
                    fontsize=8,
                    fontweight="bold",
                    color=_ZONE_LABEL_COLOR,
                )

        _draw_zone_line(start_idx, label_ha="right")
        if end_idx != start_idx:
            _draw_zone_line(end_idx, label_ha="left")

    # Remove all axes
    ax.set_axis_off()

    # Title below the chart to avoid collision with top annotations
    fig.text(0.5, 0.02, label, ha="center", va="bottom", fontsize=11, color="#374151")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, bbox_inches="tight", dpi=150, facecolor="white")
    plt.close(fig)
    print(f"  Written: {output_path}")


# ---------------------------------------------------------------------------
# Generate charts
# ---------------------------------------------------------------------------

def _discomfort_label(name: str, present: bool) -> str:
    status = "discomfort values present" if present else "no discomfort values"
    return f"  {name}: {status}"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    hours = [h.timestamp.strftime("%H:%M") for h in forecast.hourlies]

    temp_values = [h.apparent_temperature for h in forecast.hourlies]
    print(_discomfort_label("temperature", has_discomfort(temp_values, low=8, high=28)))
    render_chart(
        hours=hours,
        values=temp_values,
        output_path=OUTPUT_DIR / "temperature.png",
        label="",  # "Apparent Temperature (°C)",
        annotate_min_below=8,
        discomfort_zone=discomfort_zone(temp_values, low=8, high=28),
    )

    print(_discomfort_label("precipitation_probability", has_discomfort(_PRECIP_PROBABILITY, high=40)))
    render_chart(
        hours=hours,
        values=_PRECIP_PROBABILITY,
        output_path=OUTPUT_DIR / "precipitation_probability.png",
        label="",  # "Precipitation Probability (%)",
        discomfort_zone=discomfort_zone(_PRECIP_PROBABILITY, high=40),
    )

    uv_values = [h.uv_index for h in forecast.hourlies]
    print(_discomfort_label("uv_index", has_discomfort(uv_values, high=3)))
    render_chart(
        hours=hours,
        values=uv_values,
        output_path=OUTPUT_DIR / "uv_index.png",
        label="",  # "UV Index",
        discomfort_zone=discomfort_zone(uv_values, high=3),
    )

    wind_values = [h.wind_speed_10m for h in forecast.hourlies]
    print(_discomfort_label("wind_speed", has_discomfort(wind_values, high=40)))
    render_chart(
        hours=hours,
        values=wind_values,
        output_path=OUTPUT_DIR / "wind_speed.png",
        label="",  # "Wind Speed (km/h)",
        discomfort_zone=discomfort_zone(wind_values, high=40),
    )

    print("Done. Open tmp/weather_testbed/ in VS Code to view the charts.")


if __name__ == "__main__":
    main()
