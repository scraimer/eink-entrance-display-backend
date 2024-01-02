"""
Installation:

pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib

Running:

You need to create an API Key for this.
Go to :

https://console.cloud.google.com/apis/credentials/consent?project=entrace-display

The first time you run this program, it will to OAuth, giving you a JSON file that
must be provided to the Google API.
But part of this auth during the first run of the program is a port that is opened
and a URL launched to send data to this port. Check the port number, then forward it
from the computer doing the auth, to the computer running the Google Cloud API.

Since I'm using a key I was already using for Google Calendar API, I have to add
it to the list of the API's allowed to this API. To do that, go to:

https://console.cloud.google.com/apis/credentials/key/c36fafd6-946c-4a4b-8be0-7aa411362fe4?project=entrace-display

(Which can be reached from the https://console.cloud.google.com/apis?project=entrace-display
and clicking on "Credentials" and selecting the "Entrance Display on iot-hinge (2)")

Scroll down to the "API restrictions" sections, click on the dropdown that
says "1 API", and select "Google Sheets API".

Click on "Save".

I got an error:

   "The caller does not have permission"

Which I fixed by "Sharing" the document with "Anyone with a link". I don't like that solution so much.

New plan:

Create Service Account credentials, and use that to auth. Also give that account
access to the spreadsheet.

1. Go to https://console.cloud.google.com/iam-admin/serviceaccounts?orgonly=true&project=entrace-display&supportedpurview=organizationId
2. Click on "+ CREATE SERVICE ACCOUNT"
3. Click on "Next" until the account is created.
4. Copy the "Email" address, and share the Google Sheet with that email address.
5. Click on the account, and select the "KEYS" tab, then click on "ADD KEY" to create
   a new key. Choose "JSON" as the type. It will download a JSON file. Save
   that file as `google-sheets-bot-auth.json`, and add that file to the .gitignore,
   since we don't want to commit it.

To run this script:

    cd src/eink_backend
    python3 -m eink_backend.chores

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

from . import config


@dataclass
class Chore:
    due: date
    name: str
    assignee: str
    frequency_in_weeks: int


@dataclass
class ChoreData:
    chores: List[Chore]
    error: Optional[str] = None

def get_chores_from_spreadsheet() -> List[Chore]:
    gc: pygsheets.client.Client = pygsheets.authorize(
        service_file=config.config.google_sheets.json_file
    )
    sh: pygsheets.Spreadsheet = gc.open_by_key(config.config.google_sheets.sheet_id)
    worksheet: pygsheets.Worksheet = sh.worksheet_by_title(
        config.config.google_sheets.worksheet_name
    )

    def parse_record(src:Dict[str,Any]) -> Chore:
        return Chore(
            due=date.fromisoformat(src["Due Date"]),
            name=src["Name"],
            assignee=src["Assignee"],
            frequency_in_weeks=src["Frequency in Weeks"],
        )

    records = worksheet.get_all_records()
    return [parse_record(r) for r in records]


EMPTY_CHORES = "-no chores data-"
SHEETS_ERROR = "-error getting chores from Google Sheets-"


def collect_data(now: datetime) -> ChoreData:
    try:
        chores = get_chores_from_spreadsheet()
    except Exception as ex:
        print(f"Exception {ex} in get_chores_from_spreadsheet")
        traceback.print_exc()
        # TODO: text Shalom a notice
        # (but only if a notice hasn't been sent in the pas day)
        return ChoreData(chores=[], error=SHEETS_ERROR)
    if not chores:
        return ChoreData(chores=[], error=EMPTY_CHORES)
    return ChoreData(chores=chores)


# python3 -m eink_backend.chores
if __name__ == "__main__":
    #out = collect_data(now=datetime.datetime(year=2023, month=12, day=15, hour=10, minute=00))
    out = collect_data(now=datetime.datetime.now())
    print(out)

