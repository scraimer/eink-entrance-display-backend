from dataclasses import dataclass
import datetime
import json
from pyluach import dates, parshios
import traceback
from typing import Any, Dict, Optional

from . import my_calendar, weather, efrat_zmanim, chores, seating


@dataclass
class PageData:
    zmanim: Optional[efrat_zmanim.ShabbatZmanim]
    weather_forecast: Optional[weather.WeatherForecast]
    calendar_content: str
    chores_content: chores.ChoreData
    seating_content: seating.SeatingData


def collect_data(now: datetime.datetime):
    return PageData(
        zmanim=efrat_zmanim.collect_data(now=now),
        weather_forecast=weather.collect_data(now=now),
        calendar_content=my_calendar.collect_data(),
        chores_content=chores.collect_data(now=now),
        seating_content=seating.collect_data(now=now),
    )


def collect_all_values_of_data(
    zmanim: Optional[efrat_zmanim.ShabbatZmanim],
    weather_forecast: weather.WeatherForecast,
    calendar_content: str,
    chores_content: chores.ChoreData,
    seating_content: seating.SeatingData,
    color: str,
    now: datetime.datetime,
) -> Dict[str, Any]:
    heb_date = dates.HebrewDate.from_pydate(now.date())
    omer = omer_count(today=now.date())
    try:
        parasha = parshios.getparsha_string(heb_date, israel=True, hebrew=True)
        if not parasha and zmanim and zmanim.name:
            parasha = zmanim.name
        zmanim_dict = {
            "parasha": parasha,
            **{k: v for k, v in zmanim.times.items()},
        }
    # TODO: Can I do this try/except in some more uniform manner (print_exception_on_screen, and set value to {"error": "message of error"} or something)
    except Exception as ex:
        print("Warning: Could not collect zmanim data.")
        # TODO: indent
        traceback.print_exc()
        zmanim_dict = {"Error": str(ex)}

    weather_dict = {"weather_report": ""}
    try:
        weather_report = weather.weather_report(
            weather_forecast=weather_forecast, color=color
        )
        if weather_report:
            weather_dict["weather_report"] = weather_report
    except Exception as ex:
        msg = f"Exception colecting error report: {ex}"
        weather_dict["weather_report"] = msg
        print(msg)

    if zmanim and is_tset_soon(zmanim.times.get("tset_shabat_as_datetime", None), now):
        additional_css = """
            #shul { display: none; }
            #test-big { display: block; }
        """
    else:
        additional_css = """
            #tset-big { display: none; }
        """
    page_dict = {
        "day_of_week": now.date().strftime("%A"),
        "date": now.date().strftime("%-d of %B %Y"),
        "render_timestamp": now.strftime("%Y-%d-%m %H:%M:%S"),
        "heb_date": heb_date.hebrew_date_string(),
        "additional_css": additional_css,
    }
    calendar_dict = {"calendar_content": calendar_content}

    if chores_content.error:
        chores_str = chores_content.error
    else:
        chores_str = chores.render_chores(
            chores=chores_content.chores, now=now, color=color
        )
    chores_dict = {
        "chores_content": chores_str,
    }
    omer_dict = {
        "omer": f"{omer}",
        "omer_display": "inline" if omer else "none",
    }
    seating_dict: Dict[str, str] = {}
    for seat in seating_content.seats:
        seating_dict[f"seat{seat.number}"] = seat.name
    all_values = {
        **zmanim_dict,
        **page_dict,
        **weather_dict,
        **calendar_dict,
        **chores_dict,
        **seating_dict,
        **omer_dict,
    }
    return all_values


def is_tset_soon(tset_shabat: datetime.datetime, now: datetime.datetime) -> bool:
    if not tset_shabat:
        return False
    TSET_IS_SOON = datetime.timedelta(hours=2)
    diff: datetime.timedelta = tset_shabat - now
    return diff.total_seconds() > 0 and diff <= TSET_IS_SOON


def omer_count(today: datetime.date):
    today_heb = dates.HebrewDate.from_pydate(today)
    OMER_ZERO = dates.HebrewDate(year=today_heb.year, month=1, day=15).to_pydate()
    if today <= OMER_ZERO:
        return None
    delta = today - OMER_ZERO
    MAX_OMER = 49
    if delta.days <= 0 or delta.days > MAX_OMER:
        return None
    if delta.days > 7:
        return f"{delta.days // 7} * 7 + {delta.days % 7} = {delta.days} בעומר "
    else:
        return f"{delta.days} בעומר"


if __name__ == "__main__":
    collected_data = collect_data(
        now=datetime.datetime.now()
    )  # TODO Make data collection periodic
    from pprint import pprint

    pprint(collected_data, indent=4)

    def dataclass_encoder(obj):
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        raise TypeError(
            f"Object of type {obj.__class__.__name__} is not JSON serializable"
        )

    print(json.dumps(collected_data, indent=4, default=dataclass_encoder))
