"""
See chores.py for info

To run this script:

    cd src
    python3 -m eink_backend.seating
"""

from __future__ import print_function
import datetime
from dataclasses import dataclass
from datetime import date
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pygsheets
from string import Template
import textwrap
import traceback
from typing import Any, Dict, List, Optional

from . import config, render


@dataclass
class Seat:
    name: str
    rotate: bool
    number: int


@dataclass
class SeatingDataFromSpreadsheet:
    start_date: date
    seats: List[Seat]


@dataclass
class SeatingData:
    seats: List[Seat]
    error: Optional[str] = None


def get_seating_from_spreadsheet() -> SeatingDataFromSpreadsheet:
    gc: pygsheets.client.Client = pygsheets.authorize(
        service_file=config.config.google_sheets.json_file
    )
    sh: pygsheets.Spreadsheet = gc.open_by_key(config.config.google_sheets.sheet_id)
    worksheet: pygsheets.Worksheet = sh.worksheet_by_title(
        config.config.google_sheets.seating_worksheet_name
    )

    def parse_record(src: Dict[str, Any]) -> Seat:
        seat_number = 1
        try:
            seat_number = int(src["Seat"])
        except ValueError:
            print(f"Error parsing Seat number from value {src['Seat']}")

        return Seat(
            number=seat_number,
            name=src["Name"],
            rotate=(str(src["Rotate"]).strip() == "1"),
        )

    # TODO:
    # start_date = date.fromisoformat(src["Start Date"])

    records = worksheet.get_all_records()
    seats: List[Seat] = []
    for r in records:
        seat = parse_record(r)
        if seat.rotate:
            seats.append(seat)
    # TODO: rotate the seats
    return SeatingData(
        seats=seats,
    )
    return [parse_record(r) for r in records]


SHEETS_ERROR = "-error getting seating from Google Sheets-"


def collect_data(now: datetime) -> SeatingData:
    try:
        seat_db = get_seating_from_spreadsheet()
        # TODO: Rotate the seats according to date and `now`
        seats = seat_db.seats
    except Exception as ex:
        print(f"Exception {ex} in get_chores_from_spreadsheet")
        traceback.print_exc()
        # TODO: text Shalom a notice
        # (but only if a notice hasn't been sent in the pas day)
        return SeatingData(seats=[], error=SHEETS_ERROR)
    return SeatingData(seats=seats)


# python3 -m eink_backend.chores
if __name__ == "__main__":
    # out = collect_data(now=datetime.datetime(year=2023, month=12, day=15, hour=10, minute=00))
    out = collect_data(now=datetime.datetime.now())
    print(out)
