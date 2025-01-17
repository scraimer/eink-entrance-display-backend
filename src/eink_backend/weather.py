import sys
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from string import Template
from typing import Dict, List, Optional, Union

from pyowm.owm import OWM
import requests

from . import render
from .config import config

WMO_IMAGE_CROP_AREA = (10, 10, 90, 90)
"""There's a lot of empty white space in the images, crop just the middle 80x80"""

WMO_CODES = {
    "0": {
        "day": {
            "description": "Sunny",
            "image": "http://openweathermap.org/img/wn/01d@2x.png",
        },
        "night": {
            "description": "Clear",
            "image": "http://openweathermap.org/img/wn/01n@2x.png",
        },
    },
    "1": {
        "day": {
            "description": "Mainly Sunny",
            "image": "http://openweathermap.org/img/wn/01d@2x.png",
        },
        "night": {
            "description": "Mainly Clear",
            "image": "http://openweathermap.org/img/wn/01n@2x.png",
        },
    },
    "2": {
        "day": {
            "description": "Partly Cloudy",
            "image": "http://openweathermap.org/img/wn/02d@2x.png",
        },
        "night": {
            "description": "Partly Cloudy",
            "image": "http://openweathermap.org/img/wn/02n@2x.png",
        },
    },
    "3": {
        "day": {
            "description": "Cloudy",
            "image": "http://openweathermap.org/img/wn/03d@2x.png",
        },
        "night": {
            "description": "Cloudy",
            "image": "http://openweathermap.org/img/wn/03n@2x.png",
        },
    },
    "45": {
        "day": {
            "description": "Foggy",
            "image": "http://openweathermap.org/img/wn/50d@2x.png",
        },
        "night": {
            "description": "Foggy",
            "image": "http://openweathermap.org/img/wn/50n@2x.png",
        },
    },
    "48": {
        "day": {
            "description": "Rime Fog",
            "image": "http://openweathermap.org/img/wn/50d@2x.png",
        },
        "night": {
            "description": "Rime Fog",
            "image": "http://openweathermap.org/img/wn/50n@2x.png",
        },
    },
    "51": {
        "day": {
            "description": "Light Drizzle",
            "image": "http://openweathermap.org/img/wn/09d@2x.png",
        },
        "night": {
            "description": "Light Drizzle",
            "image": "http://openweathermap.org/img/wn/09n@2x.png",
        },
    },
    "53": {
        "day": {
            "description": "Drizzle",
            "image": "http://openweathermap.org/img/wn/09d@2x.png",
        },
        "night": {
            "description": "Drizzle",
            "image": "http://openweathermap.org/img/wn/09n@2x.png",
        },
    },
    "55": {
        "day": {
            "description": "Heavy Drizzle",
            "image": "http://openweathermap.org/img/wn/09d@2x.png",
        },
        "night": {
            "description": "Heavy Drizzle",
            "image": "http://openweathermap.org/img/wn/09n@2x.png",
        },
    },
    "56": {
        "day": {
            "description": "Light Freezing Drizzle",
            "image": "http://openweathermap.org/img/wn/09d@2x.png",
        },
        "night": {
            "description": "Light Freezing Drizzle",
            "image": "http://openweathermap.org/img/wn/09n@2x.png",
        },
    },
    "57": {
        "day": {
            "description": "Freezing Drizzle",
            "image": "http://openweathermap.org/img/wn/09d@2x.png",
        },
        "night": {
            "description": "Freezing Drizzle",
            "image": "http://openweathermap.org/img/wn/09n@2x.png",
        },
    },
    "61": {
        "day": {
            "description": "Light Rain",
            "image": "http://openweathermap.org/img/wn/10d@2x.png",
        },
        "night": {
            "description": "Light Rain",
            "image": "http://openweathermap.org/img/wn/10n@2x.png",
        },
    },
    "63": {
        "day": {
            "description": "Rain",
            "image": "http://openweathermap.org/img/wn/10d@2x.png",
        },
        "night": {
            "description": "Rain",
            "image": "http://openweathermap.org/img/wn/10n@2x.png",
        },
    },
    "65": {
        "day": {
            "description": "Heavy Rain",
            "image": "http://openweathermap.org/img/wn/10d@2x.png",
        },
        "night": {
            "description": "Heavy Rain",
            "image": "http://openweathermap.org/img/wn/10n@2x.png",
        },
    },
    "66": {
        "day": {
            "description": "Light Freezing Rain",
            "image": "http://openweathermap.org/img/wn/10d@2x.png",
        },
        "night": {
            "description": "Light Freezing Rain",
            "image": "http://openweathermap.org/img/wn/10n@2x.png",
        },
    },
    "67": {
        "day": {
            "description": "Freezing Rain",
            "image": "http://openweathermap.org/img/wn/10d@2x.png",
        },
        "night": {
            "description": "Freezing Rain",
            "image": "http://openweathermap.org/img/wn/10n@2x.png",
        },
    },
    "71": {
        "day": {
            "description": "Light Snow",
            "image": "http://openweathermap.org/img/wn/13d@2x.png",
        },
        "night": {
            "description": "Light Snow",
            "image": "http://openweathermap.org/img/wn/13n@2x.png",
        },
    },
    "73": {
        "day": {
            "description": "Snow",
            "image": "http://openweathermap.org/img/wn/13d@2x.png",
        },
        "night": {
            "description": "Snow",
            "image": "http://openweathermap.org/img/wn/13n@2x.png",
        },
    },
    "75": {
        "day": {
            "description": "Heavy Snow",
            "image": "http://openweathermap.org/img/wn/13d@2x.png",
        },
        "night": {
            "description": "Heavy Snow",
            "image": "http://openweathermap.org/img/wn/13n@2x.png",
        },
    },
    "77": {
        "day": {
            "description": "Snow Grains",
            "image": "http://openweathermap.org/img/wn/13d@2x.png",
        },
        "night": {
            "description": "Snow Grains",
            "image": "http://openweathermap.org/img/wn/13n@2x.png",
        },
    },
    "80": {
        "day": {
            "description": "Light Showers",
            "image": "http://openweathermap.org/img/wn/09d@2x.png",
        },
        "night": {
            "description": "Light Showers",
            "image": "http://openweathermap.org/img/wn/09n@2x.png",
        },
    },
    "81": {
        "day": {
            "description": "Showers",
            "image": "http://openweathermap.org/img/wn/09d@2x.png",
        },
        "night": {
            "description": "Showers",
            "image": "http://openweathermap.org/img/wn/09n@2x.png",
        },
    },
    "82": {
        "day": {
            "description": "Heavy Showers",
            "image": "http://openweathermap.org/img/wn/09d@2x.png",
        },
        "night": {
            "description": "Heavy Showers",
            "image": "http://openweathermap.org/img/wn/09n@2x.png",
        },
    },
    "85": {
        "day": {
            "description": "Light Snow Showers",
            "image": "http://openweathermap.org/img/wn/13d@2x.png",
        },
        "night": {
            "description": "Light Snow Showers",
            "image": "http://openweathermap.org/img/wn/13n@2x.png",
        },
    },
    "86": {
        "day": {
            "description": "Snow Showers",
            "image": "http://openweathermap.org/img/wn/13d@2x.png",
        },
        "night": {
            "description": "Snow Showers",
            "image": "http://openweathermap.org/img/wn/13n@2x.png",
        },
    },
    "95": {
        "day": {
            "description": "Thunderstorm",
            "image": "http://openweathermap.org/img/wn/11d@2x.png",
        },
        "night": {
            "description": "Thunderstorm",
            "image": "http://openweathermap.org/img/wn/11n@2x.png",
        },
    },
    "96": {
        "day": {
            "description": "Light Thunderstorms With Hail",
            "image": "http://openweathermap.org/img/wn/11d@2x.png",
        },
        "night": {
            "description": "Light Thunderstorms With Hail",
            "image": "http://openweathermap.org/img/wn/11n@2x.png",
        },
    },
    "99": {
        "day": {
            "description": "Thunderstorm With Hail",
            "image": "http://openweathermap.org/img/wn/11d@2x.png",
        },
        "night": {
            "description": "Thunderstorm With Hail",
            "image": "http://openweathermap.org/img/wn/11n@2x.png",
        },
    },
}

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
class WeatherDaily:
    timestamp: datetime
    apparent_temperature_min: float
    """This is "feels like", combining wind chill factor, relative humidity and solar radiation"""
    apparent_temperature_max: float
    """This is "feels like", combining wind chill factor, relative humidity and solar radiation"""
    weather_code: str


@dataclass
class WeatherForecast:
    current: WeatherHourly
    hourlies: List[WeatherHourly]
    tomorrow: WeatherDaily


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
        f"&daily=weather_code,apparent_temperature_max,apparent_temperature_min"
        f"&timezone=auto&forecast_days=3"
    )
    response = requests.get(request_url)
    data = response.json()

    DATETIME_FORMAT = "%Y-%m-%dT%H:%M"
    DATE_FORMAT = "%Y-%m-%d"
    current_data = data["current"]
    current = WeatherHourly(
        timestamp=datetime.strptime(current_data["time"], DATETIME_FORMAT),
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
            timestamp=datetime.strptime(hourly_data["time"][i], DATETIME_FORMAT),
            apparent_temperature=hourly_data["apparent_temperature"][i],
            temperature_2m=hourly_data["temperature_2m"][i],
            rain_mm=hourly_data["rain"][i],
            weather_code=hourly_data["weather_code"][i],
            wind_speed_10m=hourly_data["wind_speed_10m"][i],
            wind_direction_10m=hourly_data["wind_direction_10m"][i],
            uv_index=hourly_data["uv_index"][i],
        )
        hourlies.append(hourly)

    daily_data: Dict[str, List[Union[str, float, int]]] = data["daily"]
    tmrw_idx = 1
    tomorrow = WeatherDaily(
        timestamp=datetime.strptime(daily_data["time"][tmrw_idx], DATE_FORMAT),
        weather_code=daily_data["weather_code"][tmrw_idx],
        apparent_temperature_max=daily_data["apparent_temperature_max"][tmrw_idx],
        apparent_temperature_min=daily_data["apparent_temperature_min"][tmrw_idx],
    )

    return WeatherForecast(current=current, hourlies=hourlies, tomorrow=tomorrow)


def weather_report(weather_forecast: WeatherForecast, color: str):
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

    hours_template = Template(
        """<li>
        <ul>
            <li class="black hour">$hour_modified</li>
            <li class="black temp">$feels_like_rounded&deg;C</li>
            <li class="$color icon"><img src="$icon_url_modified"/></li>
            <li class="black status">$extra_details</li>
        </ul>
        </li>"""
    )

    hours_str = ""
    for hourly in hourlies_to_display:
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
            icon_url_modified=render.image_extract_color_channel(
                img_url=WMO_CODES[str(hourly.weather_code)][
                    "night" if hourly.timestamp.hour > 17 else "day"
                ]["image"],
                color=color,
                crop_area=WMO_IMAGE_CROP_AREA,
            ).strip(),
            feels_like_rounded=round(hourly.apparent_temperature),
            color=color,
        )

    current_uv = ""
    current_precipitation = ""
    if weather_forecast.current.uv_index > 3:
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

    tomrrow_template = Template(
        """<li class="tomorrow">
        <ul>
            <li class="black hour">$tomorrow_day_of_week</li>
            <li class="black temp">$tomorrow_min_max&deg;C</li>
            <li class="$color icon"><img src="$icon_url_modified"/></li>
        </ul>
        </li>"""
    )
    tomorrow_day_of_week = weather_forecast.tomorrow.timestamp.strftime("%a")
    tomorrow_str = tomrrow_template.substitute(
        **weather_forecast.tomorrow.__dict__,
        tomorrow_day_of_week=tomorrow_day_of_week,
        icon_url_modified=render.image_extract_color_channel(
            img_url=WMO_CODES[str(weather_forecast.tomorrow.weather_code)]["day"][
                "image"
            ],
            color=color,
            crop_area=WMO_IMAGE_CROP_AREA,
        ),
        tomorrow_min_max=f"{round(weather_forecast.tomorrow.apparent_temperature_min)}-{round(weather_forecast.tomorrow.apparent_temperature_max)}",
        color=color,
    ).strip()

    return f"""
    <span class="black">Outside temperature: </span>
    <span style="font-size: 2em" class="red">{current_temp}&deg;C</span>
    {weather_warning_icon}
    <span id="current-uv" class="black">{current_uv}</span>
    <span id="current-rain" class="black">{current_precipitation}</span>
    <br />
    <span>
         <div id="weather-table">
            <ul>{hours_str}{tomorrow_str}</ul>
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
