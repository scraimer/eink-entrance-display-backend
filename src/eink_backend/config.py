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
class Config:
    efrat: GeoLocation
    google_calendar: GoogleCalendar
    openweathermap_api_key: str


secrets_file_path = Path(__file__).parent.parent.parent / ".secrets"
load_result = load_dotenv(secrets_file_path)
if not load_result:
    raise FileNotFoundError(f"Could not read {str(secrets_file_path)}")

config = Config(
    efrat=GeoLocation(lat=31.392880, lon=35.091116),
    google_calendar=GoogleCalendar(
        api_key=os.getenv("SECRETS_GOOGLE_CALENDAR_API_KEY"),
        calendar_id=os.getenv("SECRETS_GOOGLE_CALENDAR_CALENDAR_ID"),
    ),
    openweathermap_api_key=os.getenv("SECRETS_OPENWEATHERMAP_API_KEY"),
)
