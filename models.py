"""
Shared data models for all Alpine decks.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Gebirgsgruppe:
    """One mountain group entry."""
    group_id: str           # e.g. "1", "3a", "45c"
    name: str               # German name
    hauptgruppe: str        # Regional division
    hoechster_gipfel: str   # Highest peak with elevation
    osm_ref: str            # Ref value for matching GeoJSON features


@dataclass
class POI:
    """One point-of-interest entry (peak, pass, valley, town)."""
    poi_id: str             # Unique ID, e.g. "peak_01", "pass_03"
    name: str               # Display name, e.g. "Zugspitze"
    category: str           # "peak", "pass", "valley", "town"
    lat: float              # WGS84 latitude
    lon: float              # WGS84 longitude
    elevation: Optional[int] = None   # Metres (peaks, passes)
    subtitle: Optional[str] = None    # e.g. "Mittagsspitze" for Hirschberg
    tags: list = field(default_factory=list)  # Anki tags for filtering
