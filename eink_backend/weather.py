import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime, time, timedelta
from pyowm.owm import OWM

from . import appsecrets
from .config import config


@dataclass
class WeatherDataPoint:
    feels_like: float = None
    icon_url: str = None
    hour: str = None
    hour_int: int = None
    delta_hours: int = None
    relative_day: str = None
    hour_desc: str = None
    detailed_status: str = None


@dataclass
class WeatherForToday:
    current: WeatherDataPoint
    hourlies: Dict[str, WeatherDataPoint]
    all_hourlies: List[WeatherDataPoint]
    min_max_soon: str

@dataclass
class TemperatureAtTime:
    hour_str: str
    temperature: int

def collect_data() -> WeatherForToday:
    # Setup: The API key you got from the OpenWeatherMap website, save it
    #        as `weather_api_key` in the file `appsecrets.py`
    #
    # The code below is based on
    # https://pyowm.readthedocs.io/en/latest/v3/code-recipes.html#weather_forecasts
    #
    api_key = appsecrets.weather_api_key
    owm = OWM(api_key)
    mgr = owm.weather_manager()
    owm_forecast = mgr.one_call(lat=config.efrat.lat, lon=config.efrat.lon)

    now = datetime.now()
    tomorrow = datetime.combine(now.date(), datetime.min.time()) + timedelta(days=1)
    next_day = datetime.combine(now.date(), datetime.min.time()) + timedelta(days=1)
    last_hour = datetime(year=now.year, month=now.month, day=now.day, hour=now.hour)
    school_hours_hourlies: Dict[str, WeatherDataPoint] = {}
    all_hourlies: List[WeatherDataPoint] = []
    DAY_SUFFIX = " +1day"
    NEAR_FUTURE_HOURS = 10
    max_feels_like: Optional[TemperatureAtTime] = None
    min_feels_like: Optional[TemperatureAtTime] = None
    school_hours = {
        "07:00": "To school",
        "14:00": "From school",
        "16:00": "Pickup",
    }
    school_hours_with_suffix = {k + DAY_SUFFIX: v for k, v in school_hours.items()}
    school_hours = {**school_hours, **school_hours_with_suffix}
    for hourly in owm_forecast.forecast_hourly:
        ts = hourly.reference_time("unix")
        dt = datetime.utcfromtimestamp(ts)
        delta_hours = int(
            (dt - last_hour).total_seconds() / timedelta(hours=1).total_seconds()
        )
        relative_day = ""
        if dt.date() == tomorrow.date():
            relative_day = "tomorrow"
        elif dt.date() == next_day.date():
            relative_day = dt.strftime("%A")
        suffix = DAY_SUFFIX if now.day != dt.day else ""
        hour_str = dt.strftime("%H:%M") + suffix
        feels_like = hourly.temperature("celsius")["feels_like"]
        if delta_hours <= NEAR_FUTURE_HOURS:
            if max_feels_like is None or feels_like > max_feels_like.temperature:
                max_feels_like = TemperatureAtTime(hour_str=hour_str, temperature=feels_like)
            if min_feels_like is None or feels_like < min_feels_like.temperature:
                min_feels_like = TemperatureAtTime(hour_str=hour_str, temperature=feels_like)
        wdp = WeatherDataPoint(
            hour=hour_str,
            hour_int=dt.hour,
            delta_hours=delta_hours,
            relative_day=relative_day,
            hour_desc=school_hours.get(hour_str, f"_{hour_str}_"),
            feels_like=feels_like,
            icon_url=hourly.weather_icon_url(),
            detailed_status=hourly.status,
            #'_orig': hourly,
        )
        if hour_str in school_hours.keys():
            school_hours_hourlies[hour_str] = wdp
        all_hourlies.append(wdp)

    end_time = datetime.combine(now.date(), time(hour=now.hour)) + timedelta(hours=NEAR_FUTURE_HOURS)
    min_max_soon = (
        f"Between now and {NEAR_FUTURE_HOURS} hours from now ({end_time.strftime('%H:%M')}),"
        f" between {int(min_feels_like.temperature)}&deg;C ({min_feels_like.hour_str})"
        f" and {int(max_feels_like.temperature)}&deg;C ({max_feels_like.hour_str})"
    )

    out_data = WeatherForToday(
        current=WeatherDataPoint(
            feels_like=owm_forecast.current.temperature("celsius")["feels_like"],
            icon_url=owm_forecast.current.weather_icon_url(),
        ),
        hourlies=school_hours_hourlies,
        all_hourlies=all_hourlies,
        min_max_soon=min_max_soon,
    )
    return out_data


if __name__ == "__main__":
    forecast = collect_data()
    # print(
    #     f"""Current:
    #     Temperature (feels like): {forecast.current.feels_like}
    #     Icon Url: {forecast.current.icon_url}
    # """
    # )
    # print("Hourly forcast:")
    # for hour in forecast.hourlies.values():
    #     print(
    #         f"""   {hour.hour_desc} ({hour.hour}):
    #     Temperature (feels like): {hour.feels_like}
    #     Icon Url: {hour.icon_url}
    #     Detailed status: {hour.detailed_status}
    # """
    #     )
    print("\n".join([f"{x.hour} {x.hour_int} {x.relative_day}/ {x.delta_hours}: {x.feels_like}" for x in forecast.all_hourlies]))
    print(forecast.min_max_soon)
    sys.exit(0)
