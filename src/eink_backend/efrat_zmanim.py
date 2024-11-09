from dataclasses import dataclass
from datetime import date, timedelta, datetime, time
import json
from pathlib import Path
from typing import Dict, List, Union


@dataclass
class ShabbatZmanim:
    name: str
    times: Dict[str, Union[str, datetime]]


ZMANIM_DB_SRC = "assets/efrat_zmanim.json"


def find_zmanim_for_day(day: date, efrat_zmanim: Dict[str, Union[str, int]]):
    day_iso = day.isoformat()
    return filter(lambda d: d["gregorian_date"] == day_iso, efrat_zmanim)


def kbalat_shabat_from_candle_lighting(candle_lighting: str) -> str:
    t = datetime(
        year=2020,
        month=1,
        day=1,
        hour=int(candle_lighting[0:2]),
        minute=int(candle_lighting[3:5]),
    )
    t2: date = t + timedelta(minutes=5)
    return f"{t2.hour}:{t2.minute:02}"


def find_nearest_shabbat_or_yom_tov(
    now: datetime,
    db_json: str = Path(ZMANIM_DB_SRC).read_text(encoding="utf-8"),
) -> ShabbatZmanim:
    efrat_zmanim = json.loads(db_json)
    HOW_MANY_DAYS_TO_LOOK_AHEAD = 8
    DAY = timedelta(days=1)
    day_zmanims: List[Dict[str, Union[str, datetime]]] = []
    for i in range(HOW_MANY_DAYS_TO_LOOK_AHEAD):
        day = now.date() + (i * DAY)
        if day.weekday() == 5:  # Saturday
            found = [z for z in find_zmanim_for_day(day, efrat_zmanim)]
            if found:
                for z in found:
                    z["shabbat"] = True
                    z["datetime"] = datetime.combine(
                        date=day, time=time(), tzinfo=now.tzinfo
                    )
                day_zmanims += found
    if len(day_zmanims) > 0:
        z = day_zmanims[0]
        keys = ("name", "candle_lighting", "tzet_shabat", "fast_start", "fast_end")
        out_data = {k: v for k, v in z.items() if k in keys and v}
        if z["shabbat"]:
            try:
                kabalat_shabbat = kbalat_shabat_from_candle_lighting(
                    candle_lighting=out_data["candle_lighting"]
                )
                out_data["kabalat_shabbat"] = kabalat_shabbat
            except Exception:
                print(
                    f"Error parsing kabalat shabbat from: "
                    f"{out_data['candle_lighting']}"
                )
        if "tzet_shabat" in out_data:
            d = z["datetime"]
            out_data["tset_shabat_as_datetime"] = datetime.combine(
                date=d.date(),
                time=time.fromisoformat(out_data["tzet_shabat"]),
                tzinfo=d.tzinfo,
            )
        return ShabbatZmanim(name=out_data["name"], times=out_data)
    return None


def collect_data(
    now: datetime,
    db_json: str = Path(ZMANIM_DB_SRC).read_text(encoding="utf-8"),
) -> ShabbatZmanim:
    return find_nearest_shabbat_or_yom_tov(now=now, db_json=db_json)


if __name__ == "__main__":
    print(
        collect_data(
            now=datetime(year=2024, month=11, day=8, hour=16, minute=0, second=0)
        )
    )
