from dataclasses import dataclass
from datetime import date, timedelta, datetime
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Union
from urllib.parse import unquote

@dataclass
class ShabbatZmanim:
    name: str
    times: Dict[str,str]

ZMANIM_DB_SRC = "efrat_zmanim.json"

def find_zmanim_for_day(day: date, efrat_zmanim: Dict[str,Union[str,int]]):
    day_iso = day.isoformat()
    return filter(lambda d: d["gregorian_date"] == day_iso, efrat_zmanim)

def kbalat_shabat_from_candle_lighting(candle_lighting:str) -> str:
    t = datetime(year=2020, month=1, day=1,
        hour=int(candle_lighting[0:2]),
        minute=int(candle_lighting[3:5])
    )
    t2:date = (t + timedelta(minutes=5))
    return f"{t2.hour}:{t2.minute:02}"

def collect_data() -> ShabbatZmanim:
    efrat_zmanim = json.loads(Path(ZMANIM_DB_SRC).read_text(encoding="utf-8"))
    HOW_MANY_DAYS_TO_LOOK_AHEAD = 8
    DAY = timedelta(days=1)
    day_zmanims:List[Dict[str,str]] = []
    for i in range(HOW_MANY_DAYS_TO_LOOK_AHEAD):
        day = date.today() + (i * DAY)
        if day.weekday() == 5: # Saturday
            found = [z for z in find_zmanim_for_day(day, efrat_zmanim)]
            if found:
                for z in found:
                    z["shabbat"] = True
                day_zmanims += found
    if len(day_zmanims) > 0:
        z = day_zmanims[0]
        keys = ("name", "candle_lighting", "tzet_shabat", "fast_start", "fast_end")
        out_data = {k:v for k,v in z.items() if k in keys and v}
        if z["shabbat"]:
            try:
                kabalat_shabbat = kbalat_shabat_from_candle_lighting(
                    candle_lighting = out_data["candle_lighting"]
                )
                out_data["kabalat_shabbat"] = kabalat_shabbat
            except Exception:
                print(
                    f"Error parsing kabalat shabbat from: "
                    f"{out_data['candle_lighting']}"
                )

        # {
        #     "הדלקת נרות": ["--:--"],
        #     "קבלת שבת": ["--:--"],
        #     "שחרית": ["06:45", "08:30", "09:00"],
        #     "מוצאי שבת": ["--:--"],
        # }
        return ShabbatZmanim(name=out_data["name"], times=out_data)
    return None

if __name__ == "__main__":
    print(collect_data())