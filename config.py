from dataclasses import dataclass


@dataclass
class GeoLocation:
    lat: float
    """Latitude. It's the part after the 'N' or 'S'"""
    lon: float
    """Longitude. It's the part after the 'E' or 'W'"""


@dataclass
class Config:
    efrat: GeoLocation


config = Config(efrat=GeoLocation(lat=31.392880, lon=35.091116))
