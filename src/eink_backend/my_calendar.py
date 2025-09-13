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
"""

from __future__ import print_function

import datetime
import textwrap
from typing import Any, Dict, List, Optional

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from string import Template

from . import config, render

INDENT = "    "


def get_next_10_events() -> Optional[List[Dict[str, Any]]]:
    try:
        service = build(
            "calendar", "v3", developerKey=config.config.google_calendar.api_key
        )

        # Call the Calendar API
        now = datetime.datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
        horizon = (
            datetime.datetime.utcnow() + datetime.timedelta(days=3)
        ).isoformat() + "Z"
        events_result = (
            service.events()
            .list(
                calendarId=config.config.google_calendar.calendar_id,
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


def calendar_render(events: List[Dict[str, Any]]):
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
        summary = event.get("summary", "-MISSING SUMMARY-")
        event_out = {
            "start_hour": start.strftime("%H:%M"),
            "summary": summary,
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
            t.substitute(x=textwrap.indent(day_events_str, prefix=render.INDENT * 3)),
            prefix=render.INDENT,
        )

    return calender_str


EMPTY_CALENDER = "-no calendar data-"
CALENDER_ERROR = "-error getting calendar data-"


def collect_data():
    try:
        events = get_next_10_events()
    except Exception:
        # TODO: Print the exception, or send Shalom a notice
        # (but only if a notice hasn't been sent in the pas day)
        return CALENDER_ERROR
    if not events:
        return EMPTY_CALENDER
    return calendar_render(events=events)


if __name__ == "__main__":
    events = get_next_10_events()
    print(events)
