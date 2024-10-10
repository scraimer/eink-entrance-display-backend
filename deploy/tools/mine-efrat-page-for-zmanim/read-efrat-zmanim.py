# 1. Download the PDF from https://www.efrat.muni.il/he/%D7%96%D7%9E%D7%A0%D7%99-%D7%9B%D7%A0%D7%99%D7%A1%D7%AA-%D7%94%D7%A9%D7%91%D7%AA/
# 2. Go to https://www.i2pdf.com/extract-tables-from-pdf and feed it the PDF to extact the tables. From the Options, select "JSON" as output.
# 3. Join the JSON files together
# From the docx, extract the tables into Excel into an xlsx file.
# pip3 install pandas openpyxl

from ctypes import Union
from dataclasses import dataclass
import datetime
import html
import json
from pathlib import Path
from typing import Any, Dict, List
import pandas as pd

# 3. Take the `efrat_zmanim.json` and put it with the rest of the back-end

OUT_FILE = "efrat_zmanim.json"


# def remove_spaces_and_invalid(row: Dict[str, Any]) -> Dict[str, Any]:
#     # Remove extra whitespace in keys
#     out1 = {k.strip(): v for k, v in row.items()}
#     out = {}
#     for k, v in out1.items():
#         k = k.strip()
#         if isinstance(v, str):
#             v = v.strip()
#         if v and pd.notna(v):
#             out[k] = v
#     return out


# @dataclass
# class FieldName:
#     raw: str
#     fixed: str


# class FieldsToModify:
#     DATE = FieldName(raw="תאריך לועזי", fixed="gregorian_date")
#     NAME = FieldName(raw="הפרשה", fixed="name")


# WANTED_UNCHANGED_FIELDS = {
#     "הדלקת נרות": "candle_lighting",
#     "צאת החג/השבת": "tzet_shabat",
#     "תחילת הצום - 72 דקות": "fast_start",
#     "סוף הצום": "fast_end",
# }

# skipped_fields = set()


# def replace_timestamps(row: Dict[str, Any]) -> Dict[str, Any]:
#     out = {}

#     # Fix the datetime
#     event_date: str = row[FieldsToModify.DATE.raw]
#     event_date = event_date.replace(".9.", ".09.")
#     d = datetime.datetime.strptime(event_date, "%d.%m.%y").date()
#     out[FieldsToModify.DATE.fixed] = str(d)

#     out[FieldsToModify.NAME.fixed] = row[FieldsToModify.NAME.raw]

#     # prepare any dates or times to be serialized
#     for k, v in row.items():
#         if k not in WANTED_UNCHANGED_FIELDS:
#             global skipped_fields
#             if k not in skipped_fields:
#                 skipped_fields.add(k)
#             continue
#         elif isinstance(v, datetime.time):
#             v = v.strftime("%H:%M")
#         out[WANTED_UNCHANGED_FIELDS[k]] = v

#     return out


# def normalize(row):
#     return replace_timestamps(remove_spaces_and_invalid(row))


def main():
    INPUT_JSON = "1/src.json"
    table_from_pdf = json.loads(Path(INPUT_JSON).read_text(encoding="utf-8"))
    table_from_pdf = [x["cols"] for x in table_from_pdf["table"]]
    content = table_from_pdf[2:]

    results = []
    for row in content:
        row = [html.unescape(x).strip() for x in row]
        fixed_date = datetime.datetime.strptime(row[-1], "%d.%m.%y").date()
        out = {
            "fast_end": row[0],
            "fast_start": row[1],
            "gregorian_date": str(fixed_date),
            "name": row[-2],
            "tzet_shabat": row[4],
            "candle_lighting": row[5],
        }
        out = {k: v for k, v in out.items() if v}
        results.append(out)

    Path(OUT_FILE).write_text(
        json.dumps(results), encoding="utf-8", errors="backslashescape"
    )


if __name__ == "__main__":
    main()
