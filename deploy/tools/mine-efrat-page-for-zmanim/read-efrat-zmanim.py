# Downloaded from https://www.efrat.muni.il/he/%D7%96%D7%9E%D7%A0%D7%99-%D7%9B%D7%A0%D7%99%D7%A1%D7%AA-%D7%94%D7%A9%D7%91%D7%AA/
# Go to https://www.i2pdf.com/extract-tables-from-pdf to extact the tables
# From the docx, extract the tables into Excel into an xlsx file.
# pip3 install pandas openpyxl

from ctypes import Union
from dataclasses import dataclass
import datetime
import json
from pathlib import Path
from typing import Any, Dict, List
import pandas as pd

# Usage:
# 1. pip3 install --upgrade pip
# 2. pip3 install pdfplumber
# OLD:
# 1. Download the zmanim page from https://www.efrat.muni.il/he/%D7%96%D7%9E%D7%A0%D7%99-%D7%9B%D7%A0%D7%99%D7%A1%D7%AA-%D7%94%D7%A9%D7%91%D7%AA/
# 2. Change SRC_FILENAME below to have the name of that file.
# 3. Take the `efrat_zmanim.json` and put it with the rest of the back-end

SRC_FILENAME = "efrat-zmanim-src-2022113.html"
OUT_FILE = "efrat_zmanim.json"

def remove_spaces_and_invalid(row:Dict[str,Any]) -> Dict[str,Any]:
    # Remove extra whitespace in keys
    out1 = {k.strip():v for k,v in row.items()}
    out = {}
    for k,v in out1.items():
        k = k.strip()
        if isinstance(v, str):
            v = v.strip()
        if v and pd.notna(v):
            out[k] = v
    return out

@dataclass
class FieldName:
    raw: str
    fixed: str

class FieldsToModify:
    DATE = FieldName(raw="תאריך לועזי", fixed="gregorian_date")
    NAME = FieldName(raw="הפרשה", fixed="name")

WANTED_UNCHANGED_FIELDS = {
    "הדלקת נרות": "candle_lighting",
    "צאת החג/השבת": "tzet_shabat",
    "תחילת הצום - 72 דקות": "fast_start",
    "סוף הצום": "fast_end",
}

skipped_fields = set()


def replace_timestamps(row:Dict[str,Any]) -> Dict[str,Any]:
    out = {}

    # Fix the datetime
    event_date:str = row[FieldsToModify.DATE.raw]
    event_date = event_date.replace(".9.", ".09.")
    d = datetime.datetime.strptime(event_date, "%d.%m.%y").date()
    out[FieldsToModify.DATE.fixed] = str(d)

    out[FieldsToModify.NAME.fixed] = row[FieldsToModify.NAME.raw]

    # prepare any dates or times to be serialized
    for k,v in row.items():
        if k not in WANTED_UNCHANGED_FIELDS:
            global skipped_fields
            if k not in skipped_fields:
                skipped_fields.add(k)
            continue
        elif isinstance(v, datetime.time):
            v = v.strftime("%H:%M")
        out[WANTED_UNCHANGED_FIELDS[k]] = v

    return out

def normalize(row):
    return replace_timestamps(remove_spaces_and_invalid(row))

def main():
    # Define the path to your Excel file
    excel_file_path = 'Efrat Zmanim 2023-2024.xlsx'

    # Load the Excel file into a DataFrame
    df = pd.read_excel(excel_file_path, engine='openpyxl')

    dicts = df.to_dict(orient="records")
    dicts = [normalize(d) for d in dicts]
    print(dicts[0])
    Path(OUT_FILE).write_text(data=json.dumps(dicts, indent=4), encoding="utf-8")
    print("Skipped fields:\n   " + "\n   ".join(skipped_fields))

if __name__ == "__main__":
    main()
