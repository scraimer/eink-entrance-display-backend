"""
Installation:

pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib

Running:

The first time you run this program, it will to OAuth, giving you a JSON file that
must be provided to the Google API.
But part of this auth during the first run of the program is a port that is opened
and a URL launched to send data to this port. Check the port number, then forward it
from the computer doing the auth, to the computer running the Google Cloud API.
"""

from __future__ import print_function

import datetime
import json
import os.path
import sys
import textwrap
from typing import Any, Dict, List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from string import Template

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

TOKEN_FILE_PATH = "token.json"

# XXX
sharable_url = "https://calendar.google.com/calendar/u/0?cid=OGI3MWQ0MmY5MDZmMjU5ZjM3Y2Q0YTJlYmU4N2RkYTk1ZWYwMmE4ZmQ2MjYxZGY1NzAxNjQzNTM1YTZkZDVmZEBncm91cC5jYWxlbmRhci5nb29nbGUuY29t"

# XXX
# Pass this key with

APK_KEY = "AIzaSyCfaptvOYXlddH__RcKJkR0PYs9dYIDibw"

# XXX
CALENDAR_ID = "8b71d42f906f259f37cd4a2ebe87dda95ef02a8fd6261df5701643535a6dd5fd@group.calendar.google.com"

INDENT = "    "


def auth_or_get_creds() -> Credentials:
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(TOKEN_FILE_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE_PATH, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Follow the instructions at
            # https://developers.google.com/calendar/api/quickstart/python
            # to create this file again.
            flow = InstalledAppFlow.from_client_secrets_file(
                "config-google-calendar-credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(TOKEN_FILE_PATH, "w") as token:
            token.write(creds.to_json())
    return creds


def get_next_10_events(creds: Credentials) -> Optional[List[Dict[str, Any]]]:
    try:
        service = build("calendar", "v3", credentials=creds)

        # Call the Calendar API
        now = datetime.datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
        horizon = (
            datetime.datetime.utcnow() + datetime.timedelta(days=3)
        ).isoformat() + "Z"
        events_result = (
            service.events()
            .list(
                calendarId=CALENDAR_ID,
                timeMin=now,
                timeMax=horizon,
                maxResults=20,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])
        if not events:
            print("No upcoming events found.")
            return None
        return events

    except HttpError as error:
        print("An error occurred: %s" % error)
        return None


def render(events: List[Dict[str, Any]]):
    event_template = Template(
        textwrap.dedent(
            """\
        <li>
            <ul>
                <li class="black start_hour">$start_hour</li>
                <li class="black summary">$summary</li>
            </ul>
        </li>"""
        )
    )

    # Group the events by day
    by_days: Dict[str, List[Dict[str, str]]] = {}
    for event in events:
        start_s = event["start"].get("dateTime", event["start"].get("date"))
        start = datetime.datetime.fromisoformat(start_s)
        event_out = {
            "start_hour": start.strftime("%H:%M"),
            "summary": event["summary"],
        }
        day_key = start.strftime("%A %-d/%b")
        if day_key not in by_days:
            by_days[day_key] = []
        by_days[day_key].append(event_out)

    # Prints the start and name of the next 10 events
    MAX_DAYS = 2
    day_key_count = 0
    calender_str = ""
    for key, day in by_days.items():
        if day_key_count >= MAX_DAYS:
            break
        else:
            day_key_count += 1

        day_events_str = ""
        for event in day:
            day_events_str += event_template.substitute(event)
        t = Template(
            textwrap.dedent(
                f"""\
                <ul class="black day">
                    <li class="day_title">{key}</li>
                    <li>
                        <ul class="day_events">
                $x
                        </ul>
                    <li>
                </ul>
                """
            )
        )
        calender_str += textwrap.indent(
            t.substitute(x=textwrap.indent(day_events_str, prefix=INDENT * 3)),
            prefix=INDENT,
        )

    return calender_str


def collect_data():
    creds = auth_or_get_creds()
    events = get_next_10_events(creds=creds)
    if not events:
        return "-no calendar data-"
    return render(events=events)
