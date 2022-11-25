import sys
from dataclasses import dataclass, field
from typing import Dict
from datetime import datetime
from pyowm.owm import OWM
import secrets
from config import config

@dataclass
class WeatherDataPoint:
    feels_like: float = None
    icon_url: str = None
    hour: str = None
    hour_desc: str = None
    detailed_status: str = None

@dataclass
class WeatherForToday:
    current:WeatherDataPoint
    hourlies:Dict[str,WeatherDataPoint] = field(default_factory=dict)

def collect_data() -> WeatherForToday:
    # Setup: The API key you got from the OpenWeatherMap website, save it
    #        as `weather_api_key` in the file `secrets.py`
    #
    # The code below is based on
    # https://pyowm.readthedocs.io/en/latest/v3/code-recipes.html#weather_forecasts
    #
    api_key = secrets.weather_api_key
    owm = OWM(api_key)
    mgr = owm.weather_manager()
    owm_forecast = mgr.one_call(
        lat=config.efrat.lat,
        lon=config.efrat.lon
    )

    out_data = WeatherForToday(
        current=WeatherDataPoint(
            feels_like=owm_forecast.current.temperature('celsius')['feels_like'],
            icon_url=owm_forecast.current.weather_icon_url(),
        )
    )
    hourlies = {}
    school_hours = {'07:00': 'To school', '14:00': 'From school', '16:00': 'Pickup'}
    for hourly in owm_forecast.forecast_hourly:
        ts = hourly.reference_time('unix')
        hour_str = datetime.utcfromtimestamp(ts).strftime('%H:%M')
        if hour_str not in school_hours.keys():
            continue
        out_data.hourlies[hour_str] = WeatherDataPoint(
            hour=hour_str,
            hour_desc=school_hours[hour_str],
            feels_like=hourly.temperature('celsius')['feels_like'],
            icon_url=hourly.weather_icon_url(),
            detailed_status=hourly.status,
            #'_orig': hourly,
        )
    out_data.hourlies['14:00'] = WeatherDataPoint(
        hour='14:00',
        hour_desc='From school',
        feels_like=16.67,
        icon_url='http://openweathermap.org/img/wn/04d.png',
        detailed_status='broken clouds'
    )
    out_data.hourlies['16:00'] = WeatherDataPoint(
        hour='16:00',
        hour_desc='Pickup',
        feels_like=16.53,
        icon_url='http://openweathermap.org/img/wn/04n.png',
        detailed_status='overcast clouds'
    )
    return out_data

if __name__ == '__main__':
    forecast = collect_data()
    print(f"""Current:
        Temperature (feels like): {forecast.current.feels_like}
        Icon Url: {forecast.current.icon_url}
    """)
    sys.exit(0)
    print("Hourly forcast:")
    for hour in forecast.hourlies.values():
        print(f"""   {hour.hour_desc} ({hour.hour}):
        Temperature (feels like): {hour.feels_like}
        Icon Url: {hour.icon_url}
        Detailed status: {hour.detailed_status}
    """)

