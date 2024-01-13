from dataclasses import dataclass
import datetime
from typing import Callable, Dict, Optional

from . import my_calendar, weather, efrat_zmanim, chores

@dataclass
class PageData:
    zmanim: Optional[efrat_zmanim.ShabbatZmanim]
    weather_forecast: weather.WeatherForToday
    calendar_content: str
    chores_content: chores.ChoreData
    collected_at: datetime.datetime

@dataclass
class CollectibleDatum:
    name: str
    update_func: Callable[[datetime.datetime], any]
    stale_after: datetime.timedelta

data_to_collect = {
    "zmanim": CollectibleDatum(
        name="zmanim",
        update_func=efrat_zmanim.collect_data,
        stale_after = datetime.timedelta(days=1),
    ),
    "weather_forecast": CollectibleDatum(
        name="weather_forecast",
        update_func=weather.collect_data,
        stale_after = datetime.timedelta(hours=1),
    ),
    "calendar_content": CollectibleDatum(
        name="calendar_content",
        update_func=my_calendar.collect_data,
        stale_after = datetime.timedelta(hours=1),
    ),
    "chores_content": CollectibleDatum(
        name="chores_content",
        update_func=chores.collect_data,
        stale_after = datetime.timedelta(hours=1),
    ),
}

@dataclass
class CollectedDatum:
    stale_at: datetime.datetime
    datum: any

@dataclass
class CollectedData:
    data: Dict[str, CollectedDatum]
    collected_at: datetime.datetime

# This is a global variable, so that it survives between requests.
# I would use a DB, if I wanted it to survive between server restarts.
last_collected_data : CollectedData = CollectedData(
    data={},
    collected_at=datetime.datetime.min,
)

def refresh_last_collected_data(now: datetime.datetime) -> CollectedData:
    global last_collected_data

    for k,v in data_to_collect.items():
        missing = (k not in last_collected_data.data)
        stale = (k in last_collected_data.data) and (now >= last_collected_data.data[k].stale_at)
        print(f"{k} missing={missing} stale={stale}")
        if k in last_collected_data.data:
            print("last_collected_data.data[k].stale_at", last_collected_data.data[k].stale_at)
        if missing or stale:
            print(f"Collecting {k}... (missing or stale)")
            last_collected_data.data[k] = CollectedDatum(
                stale_at = now + v.stale_after,
                datum = v.update_func(now=now),
            )
            last_collected_data.collected_at = now

    return last_collected_data


def collect_data(now: datetime.datetime):
    collected_data = refresh_last_collected_data(now=now)

    return PageData(
        zmanim=collected_data.data["zmanim"].datum,
        weather_forecast=collected_data.data["weather_forecast"].datum,
        calendar_content=collected_data.data["calendar_content"].datum,
        chores_content=collected_data.data["chores_content"].datum,
        collected_at=collected_data.collected_at,
    )

if __name__ == "__main__":
    now = datetime.datetime.now()
    later = now + datetime.timedelta(hours=1)
    collected1 = collect_data(now=now)
    collected2 = collect_data(now=later)
    for k in collected1.__dict__:
        if collected1.__dict__[k] != collected2.__dict__[k]:
            print(f"{k} is different")
