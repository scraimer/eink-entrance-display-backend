from dataclasses import dataclass
import os
from pathlib import Path
from dotenv import load_dotenv

@dataclass
class GeoLocation:
    lat: float
    """Latitude. It's the part after the 'N' or 'S'"""
    lon: float
    """Longitude. It's the part after the 'E' or 'W'"""


@dataclass
class GoogleCalendar:
    api_key: str
    calendar_id: str


@dataclass
class GoogleSheet:
    sheet_id: str
    worksheet_name: str
    json_file: Path


@dataclass
class Config:
    efrat: GeoLocation
    google_calendar: GoogleCalendar
    google_sheets: GoogleSheet
    openweathermap_api_key: str


secrets_file_path = Path(__file__).parent.parent.parent / ".secrets"
load_result = load_dotenv(secrets_file_path)
if not load_result:
    raise FileNotFoundError(f"Could not read {str(secrets_file_path)}")
google_sheets_auth_json = Path(secrets_file_path.parent / "google-sheets-bot-auth.json")
if not google_sheets_auth_json.exists():
    raise FileNotFoundError(f"Could not find {str(google_sheets_auth_json)}")

config = Config(
    efrat=GeoLocation(lat=31.392880, lon=35.091116),
    google_calendar=GoogleCalendar(
        api_key=os.getenv("SECRETS_GOOGLE_CALENDAR_API_KEY"),
        calendar_id=os.getenv("SECRETS_GOOGLE_CALENDAR_CALENDAR_ID"),
    ),
    openweathermap_api_key=os.getenv("SECRETS_OPENWEATHERMAP_API_KEY"),
    google_sheets=GoogleSheet(
        sheet_id="1TJoMDv5UUEzY1IYEn3Ce-MmhlnP8ytGQLnx9dg8LFm8",
        worksheet_name="Friday Chores",
        json_file=google_sheets_auth_json,
    ),
)
