from dataclasses import dataclass
import json
from pathlib import Path


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


private_config_path = Path(__file__).parent / "config-private-data.json"
private_config_json = json.loads(private_config_path.read_text(encoding="utf-8"))

config = Config(
    efrat=GeoLocation(lat=31.392880, lon=35.091116),
    google_calendar=GoogleCalendar(
        api_key=private_config_json["google_calendar"]["api_key"],
        calendar_id=private_config_json["google_calendar"]["calendar_id"],
    ),
)
