import sys
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from string import Template
from typing import Dict, List, Optional, Union

from pyowm.owm import OWM
import requests

from . import render
from .config import config


# @dataclass
# class WeatherDataPoint:
#     at: datetime = None
#     feels_like: float = None
#     icon_url: str = None
#     hour: str = None
#     hour_int: int = None
#     delta_hours: int = None
#     relative_day: str = None
#     hour_desc: str = None
#     uv_index: float = None
#     probability_of_precipiration: float = None


@dataclass
class WeatherHourly:
    timestamp: datetime
    temperature_2m: float
    apparent_temperature: float
    """This is "feels like", combining wind chill factor, relative humidity and solar radiation"""
    rain_mm: float
    wind_speed_10m: float
    wind_direction_10m: int
    uv_index: float
    weather_code: str


@dataclass
class WeatherForecast:
    current: WeatherHourly
    hourlies: List[WeatherHourly]


@dataclass
class TemperatureAtTime:
    hour_str: str
    temperature: int


def collect_data(now: datetime) -> Optional[WeatherForecast]:
    try:
        return _collect_data_impl(now)
    except Exception as ex:
        print(f"Error getting weather data: {ex}")
        return None


def _collect_data_impl(now: datetime) -> WeatherForecast:
    # Setup: The API key you got from the open-meteo.com website, save it
    #        as `SECRETS_OPEN_METEO_API_KEY` in the file `.secrets`
    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    request_url = (
        f"{BASE_URL}?latitude={config.efrat.lat}&longitude={config.efrat.lon}"
        f"&current=temperature_2m,precipitation,rain,weather_code,wind_speed_10m,wind_direction_10m,uv_index,apparent_temperature"
        f"&hourly=temperature_2m,rain,weather_code,wind_speed_10m,wind_direction_10m,uv_index,apparent_temperature"
        f"&timezone=auto&forecast_days=3"
    )
    response = requests.get(request_url)
    data = response.json()

    DATE_FORMAT = "%Y-%m-%dT%H:%M"
    current_data = data["current"]
    current = WeatherHourly(
        timestamp=datetime.strptime(current_data["time"], DATE_FORMAT),
        apparent_temperature=current_data["apparent_temperature"],
        temperature_2m=current_data["temperature_2m"],
        rain_mm=current_data["rain"],
        weather_code=current_data["weather_code"],
        wind_speed_10m=current_data["wind_speed_10m"],
        wind_direction_10m=current_data["wind_direction_10m"],
        uv_index=current_data["uv_index"],
    )

    hourly_data: Dict[str, List[Union[str, float, int]]] = data["hourly"]
    time_len = len(hourly_data["time"])
    for key in hourly_data:
        assert (
            len(hourly_data[key]) == time_len
        ), f"Error: key {key} has a different length."
    hourlies: List[WeatherHourly] = []
    for i in range(time_len):
        hourly = WeatherHourly(
            timestamp=datetime.strptime(hourly_data["time"][i], DATE_FORMAT),
            apparent_temperature=hourly_data["apparent_temperature"][i],
            temperature_2m=hourly_data["temperature_2m"][i],
            rain_mm=hourly_data["rain"][i],
            weather_code=hourly_data["weather_code"][i],
            wind_speed_10m=hourly_data["wind_speed_10m"][i],
            wind_direction_10m=hourly_data["wind_direction_10m"][i],
            uv_index=hourly_data["uv_index"][i],
        )
        hourlies.append(hourly)

    return WeatherForecast(current=current, hourlies=hourlies)


def weather_report(weather_forecast: WeatherForecast, color: str):
    hours_template = Template(
        """
        <li>
        <ul>
            <li class="black hour">$hour_modified</li>
            <li class="black temp">$feels_like_rounded&deg;C</li>
            <li class="black status">$extra_details</li>
        </ul>
        </li>"""
        # Removed: <li class="$color icon"><img src="$icon_url_modified"/></li>
    )

    # When looking at the board, I want it to warn me what to prepare for:
    # - rising temperature
    # - rain (take coat!) or snow (don't go!)
    # - sun (sunscreen!)
    # - going to be hot, so take water
    # - going to be freezing
    # I also want it to tell me when it will be safe to go outside:
    # - wind stopping
    # - rain stopping
    # - temperature going up in winter or down in summer

    # For now, I want to see 4 things
    # - the next hourly that is at least 45 minutes away
    # - the next 2 hourlies that are either 7:00, 14:00, 16:00
    # - the forecast for the whole of tomorrow

    now = datetime.now()
    next_hourly_key = datetime(
        year=now.year, month=now.month, day=now.day, hour=now.hour
    )
    next_hourly_matches = [
        hourly
        for hourly in weather_forecast.hourlies
        if hourly.timestamp == next_hourly_key
    ]
    assert (
        len(next_hourly_matches) == 1
    ), f"Expected 1 match, found {len(next_hourly_matches)}"
    next_hourly = next_hourly_matches[0]

    DESIRED_HOURS = [7, 14, 16]  # 07:00, 14:00, 16:00
    matching_hourlies = []
    # skip the next 2 hours, they are too near
    for hourly in weather_forecast.hourlies[2:]:
        if hourly.timestamp.hour in DESIRED_HOURS:
            matching_hourlies.append(hourly)
        if len(matching_hourlies) >= 2:
            break

    hourlies_to_display = [next_hourly] + matching_hourlies

    hours_str = ""
    for hourly in hourlies_to_display:
        # hour_modified = hour.hour[0:5] + (
        #     f'<span class="tomorrow">{hour.relative_day}</span>'
        #     if hour.relative_day
        #     else ""
        # )
        hour_modified = hourly.timestamp.strftime("%H:%M") + (
            f'<span class="tomorrow">{hourly.timestamp.strftime("%A")}</span>'
            if hourly.timestamp.day != datetime.today().day
            else ""
        )

        # during summer and hot days, the UV index is more important, and during winter
        # and cold days, the rain probability is more important
        extra_details = ""
        uv = ""
        if hourly.uv_index >= 11:
            uv = f"UV: {hourly.uv_index} (EXTREME! stay indoors)"
        elif hourly.uv_index >= 8:
            uv = f"UV: {hourly.uv_index} (dangerous!)"
        elif hourly.uv_index >= 6:
            uv = f"UV: {hourly.uv_index} (sunscreen!)"
        elif hourly.uv_index >= 3:
            uv = f"UV: {hourly.uv_index} (careful)"
        extra_details += uv
        if hourly.rain_mm > 0:
            extra_details += f"Rain: {hourly.rain_mm}mm"
        hours_str += hours_template.substitute(
            **hourly.__dict__,
            extra_details=extra_details,
            hour_modified=hour_modified,
            # icon_url_modified=render.image_extract_color_channel(
            #     img_url=hour.icon_url, color=color
            # ),
            feels_like_rounded=round(hourly.apparent_temperature),
            color=color,
        )

    current_uv = ""
    current_precipitation = ""
    if weather_forecast.current.uv_index:
        current_uv = f"UV: {weather_forecast.current.uv_index}"
    if weather_forecast.current.rain_mm:
        current_precipitation = f"Rain: {weather_forecast.current.rain_mm}mm"

    current_temp = round(weather_forecast.current.apparent_temperature)
    weather_warning_icon = ""
    JACKET_WEATHER_TEMPERATURE = 13
    if weather_forecast.current.apparent_temperature <= JACKET_WEATHER_TEMPERATURE:
        x = f"""
            <span id="current-weather-warning-icon">
                <img src="/app/assets/pic/jacket-black.png" class="black" />
            </span>"""
        weather_warning_icon = x

    return f"""
    <span class="black">Outside temperature: </span>
    <span style="font-size: 2em" class="red">{current_temp}&deg;C</span>
    {weather_warning_icon}
    <span id="current-uv" class="black">{current_uv}</span>
    <span id="current-rain" class="black">{current_precipitation}</span>
    <br />
    <span>
         <div id="weather-table">
            <ul>
                {hours_str}
            </ul>
        </div>
    </span>
    """


if __name__ == "__main__":
    forecast = collect_data(now=datetime.now())
    if forecast is None:
        sys.exit(1)
    # print(forecast)
    report = weather_report(weather_forecast=forecast, color="joined")
    # print(report)
    sys.exit(0)
