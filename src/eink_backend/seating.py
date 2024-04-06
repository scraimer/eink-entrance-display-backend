"""
See chores.py for info

To run this script:

    cd src
    python3 -m eink_backend.seating
"""

from __future__ import print_function
from collections import deque
import datetime
from dataclasses import dataclass
from datetime import date
import pygsheets
import traceback
from typing import Any, Dict, List, Tuple, Optional

from . import config


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
            return None

        return Seat(
            number=seat_number,
            name=src["Name"],
            rotate=(str(src["Rotate"]).strip() == "1"),
        )

    records = worksheet.get_all_records()
    seats: List[Seat] = []
    for r in records:
        seat = parse_record(r)
        seats.append(seat)
    if records and len(records) > 0:
        start_date = date.fromisoformat(records[0]["Start Date"])
    return SeatingDataFromSpreadsheet(
        seats=seats,
        start_date=start_date,
    )


def rotate_seats(now: datetime, seat_db: SeatingDataFromSpreadsheet) -> List[Seat]:
    DAYS_IN_WEEK = 7
    weeks_since_start = (now.date() - seat_db.start_date).days / DAYS_IN_WEEK
    # Every week is 2 rotations. And there's one rotation between supper and lunch.
    rotations = int(weeks_since_start) * 2 + (
        0 if weeks_since_start.is_integer() else 1
    )

    # split the list of seats to get just the indexes we need to rotate, and rotate
    # just those, and then rebuild the list

    out_seats: List[Seat] = [None] * len(seat_db.seats)
    rotateable_indexes: List[int] = []
    for idx, seat in enumerate(seat_db.seats):
        if seat.rotate:
            rotateable_indexes.append(idx)
        else:
            out_seats[idx] = seat
    rotated_indexes = deque(rotateable_indexes)
    rotated_indexes.rotate(rotations)
    for idx, seat in enumerate(out_seats):
        if seat_db.seats[idx].rotate:
            new_idx = rotated_indexes.popleft()
            out_seats[idx] = seat_db.seats[new_idx]
            out_seats[idx].number = idx + 1
    return out_seats


SHEETS_ERROR = "-error getting seating from Google Sheets-"


def collect_data(now: datetime) -> SeatingData:
    try:
        seat_db = get_seating_from_spreadsheet()
    except Exception as ex:
        print(f"Exception {ex} in get_chores_from_spreadsheet")
        traceback.print_exc()
        # TODO: text Shalom a notice
        # (but only if a notice hasn't been sent in the past day)
        return SeatingData(seats=[], error=SHEETS_ERROR)

    seats = rotate_seats(now=now, seat_db=seat_db)
    return SeatingData(seats=seats)


# python3 -m eink_backend.chores
if __name__ == "__main__":
    # out = collect_data(now=datetime.datetime.now())

    dates = {
        "1-supper": datetime.datetime(year=2024, month=4, day=5, hour=0, minute=0),
        "1-lunch ": datetime.datetime(year=2024, month=4, day=6, hour=0, minute=0),
        "2-supper": datetime.datetime(year=2024, month=4, day=12, hour=0, minute=0),
        "2-lunch ": datetime.datetime(year=2024, month=4, day=13, hour=0, minute=0),
    }
    seat_db = SeatingDataFromSpreadsheet(
        start_date=datetime.date(2024, 4, 5),
        seats=[
            Seat(name="", rotate=False, number=1),
            Seat(name="A1", rotate=True, number=2),
            Seat(name="A2", rotate=True, number=3),
            Seat(name="A3", rotate=True, number=4),
            Seat(name="-", rotate=False, number=5),
            Seat(name="A5", rotate=True, number=6),
            Seat(name="-", rotate=False, number=7),
            Seat(name="A4", rotate=True, number=8),
        ],
    )
    for k, d in dates.items():
        out = rotate_seats(now=d, seat_db=seat_db)
        o = ",".join([f"{s.name}={s.number}" for s in out])
        print(f"{k} = {o}")
