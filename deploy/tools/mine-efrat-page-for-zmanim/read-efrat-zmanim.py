# 1. Download the PDF from https://www.efrat.muni.il/he/%D7%96%D7%9E%D7%A0%D7%99-%D7%9B%D7%A0%D7%99%D7%A1%D7%AA-%D7%94%D7%A9%D7%91%D7%AA/
# 2. Go to https://www.i2pdf.com/extract-tables-from-pdf and feed it the PDF to extact the tables. From the Options, select "JSON" as output.
# 3. Join the JSON files together
# From the docx, extract the tables into Excel into an xlsx file.
# pip3 install pandas openpyxl
# 4. Copy the `efrat_zmanim.json` to `assets` directory

from ctypes import Union
from dataclasses import dataclass
import datetime
import html
import json
from pathlib import Path
from typing import Any, Dict, List
import pandas as pd


OUT_FILE = "efrat_zmanim.json"


def main():
    INPUT_JSON = "1/src.json"
    print(f"Reading from {str(INPUT_JSON)}")
    table_from_pdf = json.loads(Path(INPUT_JSON).read_text(encoding="utf-8"))
    table_from_pdf = [x["cols"] for x in table_from_pdf["table"]]
    content = table_from_pdf[2:]

    results = []
    for row in content:
        row = [html.unescape(x).strip() for x in row]
        fixed_date = datetime.datetime.strptime(row[-1], "%d.%m.%y").date()
        if str(fixed_date) == "2025-05-10":
            print(f"DEBUG: Row: {row}")
        out = {
            "fast_end": row[0],
            "fast_start": row[1],
            "gregorian_date": str(fixed_date),
            "name": row[-2],
            "tzet_shabat": row[3],
            "candle_lighting": row[4],
        }
        out = {k: v for k, v in out.items() if v}
        results.append(out)

    outfile = Path(OUT_FILE)
    outfile.write_text(
        json.dumps(results, indent=3), encoding="utf-8", errors="backslashescape"
    )
    print(f"Wrote results to {str(outfile)}")


if __name__ == "__main__":
    main()
