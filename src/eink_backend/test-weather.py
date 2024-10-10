from typing import Dict, List, Union
import requests
import datetime
import json
from dataclasses import dataclass

API_KEY = "f9bd5d24e1f445a5a5c180628242509"  # TODO: Move to key
BASE_URL = "https://api.open-meteo.com/v1/forecast"


@dataclass
class WeatherHourly:
    time: str
    temperature_2m: float
    rain_mm: float
    wind_speed_10m: float
    wind_direction_10m: int
    uv_index: float


@dataclass
class WeatherForecast:
    current: WeatherHourly
    hourlies: List[WeatherHourly]


def get_weather_forecast(lat, lon):
    request_url = (
        f"{BASE_URL}?latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,precipitation,rain,weather_code,wind_speed_10m,wind_direction_10m,uv_index"
        f"&hourly=temperature_2m,rain,wind_speed_10m,wind_direction_10m,uv_index"
        f"&timezone=auto&forecast_days=3"
    )
    response = requests.get(request_url)
    data = response.json()

    current_data = data["current"]
    current = WeatherHourly(
        time=datetime.strptime(current_data["time"], DATE_FORMAT),
        temperature_2m=current_data["temperature_2m"],
        rain_mm=current_data["rain"],
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
            time=datetime.strptime(hourly_data["time"][i], DATE_FORMAT),
            temperature_2m=hourly_data["temperature_2m"][i],
            rain_mm=hourly_data["rain"][i],
            wind_speed_10m=hourly_data["wind_speed_10m"][i],
            wind_direction_10m=hourly_data["wind_direction_10m"][i],
            uv_index=hourly_data["uv_index"][i],
        )
        hourlies.append(hourly)

    print(current)
    print(hourlies)
    print(json.dumps(data, indent=4))


if __name__ == "__main__":
    lat = 31.392880
    lon = 35.091116
    get_weather_forecast(lat, lon)
