# Downloaded from https://www.efrat.muni.il/he/%D7%96%D7%9E%D7%A0%D7%99-%D7%9B%D7%A0%D7%99%D7%A1%D7%AA-%D7%94%D7%A9%D7%91%D7%AA/
import json
import bs4
from pathlib import Path
from typing import List
import datetime

# Usage:
# 1. Download the zmanim page from https://www.efrat.muni.il/he/%D7%96%D7%9E%D7%A0%D7%99-%D7%9B%D7%A0%D7%99%D7%A1%D7%AA-%D7%94%D7%A9%D7%91%D7%AA/
# 2. Change SRC_FILENAME below to have the name of that file.
# 3. Take the `efrat_zmanim.json` and put it with the rest of the back-end

SRC_FILENAME = "efrat-zmanim-src-2022113.html"
OUT_FILE = "efrat_zmanim.json"


def text_date_in_heb_to_date(src: str):
    HEB_MONTHS = {
        "ינו׳": 1,
        "פבר׳": 2,
        "מרץ": 3,
        "אפר׳": 4,
        "מאי": 5,
        "יוני": 6,
        "יולי": 7,
        "אוג׳": 8,
        "ספט׳": 9,
        "אוק׳": 10,
        "נוב׳": 11,
        "דצמ׳": 12,
    }
    field = src.split(" ")
    if len(field) != 3:
        raise ValueError("Expected 3 fields in date.")
    day = int(field[0])
    month = HEB_MONTHS[field[1]]
    year = 2000 + int(field[2])
    return datetime.date(year=year, month=month, day=day)


def pick_column(tds: List[str]):
    # Special case: index 2 is empty, and the number of items is 14, then
    # shrink it to 13.
    if len(tds) == 14 and not tds[2]:
        del tds[2]

    gregorian_date_in_heb = tds[0]
    row_date = text_date_in_heb_to_date(gregorian_date_in_heb)
    row_data = {
        "gregorian_date": row_date.isoformat(),
        "name": tds[1],
        "hebrew_date": tds[2],
    }
    # Maybe it's a candle-lighting day?
    if len(tds) >= 4 and tds[3]:
        row_data["candle_lighting"] = tds[3]

    # Maybe it's a fast day?
    if len(tds) >= 13 and tds[11] and tds[12]:
        row_data["fast_start"] = tds[11]
        row_data["fast_end"] = tds[12]

    # Maybe it's a havdala day? (Think about 2nd day of Rosh Hashan)
    elif len(tds) >= 11 and tds[10]:
        # TODO: Only emit this if it's really a holiday.
        #       Don't confuse it with a fast day.
        row_data["tzet_shabat"] = tds[10]

    row_data["all_fields"] = {f"f_{i:02}": x for i, x in enumerate(tds)}

    return row_data


def extract_zmanim(doc: bs4.BeautifulSoup):
    table = doc.find("table")
    header_row = table.find("tr")
    rows = header_row.find_all_next("tr")
    out_rows = []
    for row in rows:
        tds = [td.getText().strip() for td in row.find_all("td")]
        if len(tds) == 0:
            continue
        row_data = pick_column(tds)
        out_rows.append(row_data)
    return out_rows


def main():
    doc = bs4.BeautifulSoup(
        Path(SRC_FILENAME).read_text(encoding="utf-8"), features="html.parser"
    )
    out_rows = extract_zmanim(doc)
    Path(OUT_FILE).write_text(data=json.dumps(out_rows, indent=4), encoding="utf-8")


if __name__ == "__main__":
    main()
