"""
deck.py — Region / Classification / Deck definitions
======================================================
Central place for all configuration.

Architecture:
  - **Region**: geographic scope (bbox, projection, cities, DEM, rivers)
  - **Classification**: grouping system (groups, hauptgruppen, colors, OSM tag)
  - **Deck**: Region × Classification combination with property delegation

Usage in scripts::

    from deck import get_deck, add_deck_arguments
    parser = argparse.ArgumentParser()
    add_deck_arguments(parser)
    args = parser.parse_args()
    d = get_deck(args.region, args.system)
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from models import Gebirgsgruppe, POI

# ═══════════════════════════════════════════════════════════════════════════════
# SHARED CONSTANTS  (identical for every deck)
# ═══════════════════════════════════════════════════════════════════════════════

PROJECT_ROOT = Path(__file__).parent

# ─── Data directories (shared) ───────────────────────────────────────────────
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR_OSM = DATA_DIR / "osm"
DATA_DIR_DEM = DATA_DIR / "dem"

# ─── Overpass API ─────────────────────────────────────────────────────────────
OVERPASS_API_URL = "https://overpass-api.de/api/interpreter"
OVERPASS_TIMEOUT = 300

# ─── Bbox buffers ─────────────────────────────────────────────────────────────
DEM_BBOX_BUFFER = 0.2
RENDER_BUFFER = 0.5

# ─── DEM downsampling ─────────────────────────────────────────────────────────
DEM_DOWNSAMPLE_THRESHOLD = 7000
MAX_HILLSHADE_ELEVATION = 4200

# ─── Label positioning (negative-buffer technique fractions) ───────────────────
LABEL_SHRINK_FRACTIONS = (0.10, 0.06, 0.03, 0.01)

# ─── Figure ───────────────────────────────────────────────────────────────────
FIGURE_DPI = 480
BASEMAP_LONG_EDGE = 7680   # px – max for the longest side (8K UHD)
BASEMAP_SHORT_EDGE = 4320  # px – max for the shortest side (8K UHD)
BASEMAP_WEBP_QUALITY = 90  # lossy WebP quality for opaque basemap (0-100)

# ─── Polygon styling ─────────────────────────────────────────────────────────
POLYGON_ALPHA = 0.55
POLYGON_BORDER_COLOR = "#FFFFFF"
POLYGON_BORDER_WIDTH = 0.8

# ─── Label styling ───────────────────────────────────────────────────────────
LABEL_FONTSIZE_ID = 11

# ─── Circle-packing question marks ────────────────────────────────────────────
QMARK_FONTSIZE_MIN = 14              # clamp: skip circles whose glyph would be < this
QMARK_FILL_FACTOR = 0.85             # glyph height as fraction of circle diameter
QMARK_MIN_RADIUS_RATIO = 0.45        # stop adding circles when r_next / r_max < this
QMARK_MAX_REST_AREA = 0.40            # keep adding if uncovered fraction exceeds this
QMARK_POLYLABEL_TOL = 0.001          # polylabel tolerance (degrees)
QMARK_MIN_RADIUS_ABS = 0.008         # absolute minimum circle radius (degrees)

# ─── Hillshade ────────────────────────────────────────────────────────────────
HILLSHADE_AZIMUTH = 315
HILLSHADE_AZIMUTH_ROT = 135               # azimuth for 180° map rotation (south-up)
HILLSHADE_ALTITUDE = 45
HILLSHADE_VERT_EXAG = 0.05
HILLSHADE_BLEND_MODE = "soft"

# ─── Compass needle ──────────────────────────────────────────────────────────
COMPASS_RADIUS_RATIO = 0.020     # needle radius relative to short image edge
COMPASS_MARGIN_RATIO = 0.015     # margin from top/right edge
COMPASS_NORTH_COLOR = "#CC0000"  # red = north half of needle
COMPASS_SOUTH_COLOR = "#FFFFFF"  # white = south half
COMPASS_OUTLINE_COLOR = "#555555"
COMPASS_BG_ALPHA = 180           # background circle opacity (0-255)
COMPASS_FONT = "segoeui.ttf"     # Segoe UI (available on Windows)

# ─── Rivers & Lakes ──────────────────────────────────────────────────────────
OCEAN_COLOR = "#c6ddf0"
RIVER_COLOR = "#4A7FB5"
RIVER_LINEWIDTH = 0.4
RIVER_MIN_LENGTH_KM = 20          # Minimum total river length (km) to display
VALLEY_MIN_LENGTH_KM = 20         # Minimum total valley length (km) to include
LAKE_FACECOLOR = "#7FAFCF"
LAKE_EDGECOLOR = "#4A7FB5"
LAKE_LINEWIDTH = 0.3
LAKE_MIN_AREA_KM2 = 0.2           # Minimum lake area (km²) for OSM lakes

# ─── Country borders ─────────────────────────────────────────────────────────
COUNTRY_BORDER_COLOR = "#555555"
COUNTRY_BORDER_WIDTH = 0.6
COUNTRY_BORDER_STYLE = "--"



# ═══════════════════════════════════════════════════════════════════════════════
# REGION DATACLASS — geographic scope
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Region:
    """Geographic region (bounding box, projection, cities, rivers, DEM)."""

    name: str                   # "ostalpen" / "westalpen"

    # ── Geography ────────────────────────────────────────────────────────────
    bbox_west: float
    bbox_east: float
    bbox_south: float
    bbox_north: float
    projection_params: dict

    # ── Figure ───────────────────────────────────────────────────────────────
    figure_width: float         # inches
    figure_height: float        # inches

    # ── Cities:  (name, lon, lat, dx, dy) ────────────────────────────────────
    cities: List[Tuple[str, float, float, float, float]]

    # ── Region-specific file paths ───────────────────────────────────────────
    osm_rivers_geojson: Path
    osm_lakes_geojson: Path
    osm_valleys_geojson: Path
    osm_borders_geojson: Path
    dem_tif: Path

    # ── Convenience properties ───────────────────────────────────────────────

    @property
    def extent(self) -> list:
        return [self.bbox_west, self.bbox_east, self.bbox_south, self.bbox_north]

    @property
    def dem_bbox_west(self) -> float:
        return self.bbox_west - DEM_BBOX_BUFFER

    @property
    def dem_bbox_east(self) -> float:
        return self.bbox_east + DEM_BBOX_BUFFER

    @property
    def dem_bbox_south(self) -> float:
        return self.bbox_south - DEM_BBOX_BUFFER

    @property
    def dem_bbox_north(self) -> float:
        return self.bbox_north + DEM_BBOX_BUFFER


# ═══════════════════════════════════════════════════════════════════════════════
# CLASSIFICATION DATACLASS — grouping system
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Classification:
    """A mountain group classification system (AVE 84, SOIUSA, etc.)."""

    name: str                   # "ave84" / "soiusa_sz"
    title: str                  # Human-readable, e.g. "AVE 84"

    # ── Groups & classification ──────────────────────────────────────────────
    groups: List[Gebirgsgruppe]
    hauptgruppen: List[str]
    colors: Dict[str, dict]

    # ── OSM integration ──────────────────────────────────────────────────────
    osm_tag: str                # e.g. "ref:aveo", "ref:soiusa"
    osm_fallback_ids: Dict[str, int] = field(default_factory=dict)

    # ── Hierarchy (optional) ─────────────────────────────────────────────────
    parent_osm_tag: Optional[str] = None   # GeoJSON property for parent level (e.g. "SZ")

    # ── Computed lookups (populated in __post_init__) ────────────────────────
    _by_id: Dict[str, Gebirgsgruppe] = field(init=False, repr=False)
    _by_osm_ref: Dict[str, Gebirgsgruppe] = field(init=False, repr=False)
    _by_hauptgruppe: Dict[str, List[Gebirgsgruppe]] = field(init=False, repr=False)

    def __post_init__(self):
        self._by_id = {g.group_id: g for g in self.groups}
        self._by_osm_ref = {g.osm_ref: g for g in self.groups}
        self._by_hauptgruppe = {}
        for g in self.groups:
            self._by_hauptgruppe.setdefault(g.hauptgruppe, []).append(g)

    @property
    def valid_osm_refs(self) -> set:
        return set(self._by_osm_ref.keys())

    def group_by_id(self, group_id: str) -> Gebirgsgruppe:
        return self._by_id[group_id]

    def group_by_osm_ref(self, ref: str) -> Gebirgsgruppe:
        return self._by_osm_ref[ref]

    def has_osm_ref(self, ref: str) -> bool:
        return ref in self._by_osm_ref


# ═══════════════════════════════════════════════════════════════════════════════
# POI CLASSIFICATION — for point-of-interest decks
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class POIClassification:
    """Classification for point-of-interest decks (peaks, passes, towns, valleys)."""

    name: str               # e.g. "pois"
    title: str              # Human-readable, e.g. "Peak Soaring POIs"
    pois: List[POI]
    category_style: dict    # {"peak": {"marker": "^", "color": ...}, ...}

    # ── Computed lookups ─────────────────────────────────────────────────────
    _by_id: Dict[str, POI] = field(init=False, repr=False)
    _by_category: Dict[str, List[POI]] = field(init=False, repr=False)

    def __post_init__(self):
        self._by_id = {p.poi_id: p for p in self.pois}
        self._by_category = {}
        for p in self.pois:
            self._by_category.setdefault(p.category, []).append(p)

    def poi_by_id(self, poi_id: str) -> POI:
        return self._by_id[poi_id]

    def pois_by_category(self, category: str) -> List[POI]:
        return self._by_category.get(category, [])

    @property
    def categories(self) -> List[str]:
        return list(self._by_category.keys())


# ═══════════════════════════════════════════════════════════════════════════════
# BASE DECK — shared between Deck and POIDeck
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class BaseDeck:
    """Common base for Region × Classification deck configurations.

    Provides shared filename generation, property delegation to the
    ``region`` attribute, and automatic directory creation.
    Subclasses must override ``_classification_name`` and
    ``_classification_title``.
    """

    region: Region
    output_images_dir: Path
    output_csv_dir: Path
    anki_csv_name: str

    def __post_init__(self):
        self.output_images_dir.mkdir(parents=True, exist_ok=True)
        self.output_csv_dir.mkdir(parents=True, exist_ok=True)

    # ── Abstract: override in subclasses ─────────────────────────────────

    @property
    def _classification_name(self) -> str:
        raise NotImplementedError

    @property
    def _classification_title(self) -> str:
        raise NotImplementedError

    # ── Identity ─────────────────────────────────────────────────────────

    @property
    def is_poi_deck(self) -> bool:
        return False

    @property
    def name(self) -> str:
        return f"{self.region.name}_{self._classification_name}"

    @property
    def title(self) -> str:
        return f"{self.region.name.capitalize()} — {self._classification_title}"

    # ── Filename generation (with ps_ prefix for Peak Soaring) ───────────

    @property
    def prefix(self) -> str:
        return f"ps_{self.region.name}_{self._classification_name}"

    def filename_partition(self, ext: str = ".png") -> str:
        """Generate filename for partition map (Einteilung)."""
        return f"{self.prefix}_partition{ext}"

    def filename_context(self) -> str:
        """Generate filename for shared context overlay (borders + cities)."""
        return f"{self.prefix}_context.webp"

    def filename_basemap(self) -> str:
        """Generate filename for shared basemap WebP (hillshade + rivers + lakes)."""
        return f"{self.prefix}_basemap.webp"

    def filename_basemap_rot(self) -> str:
        """Generate filename for 180° rotated basemap (hillshade azimuth 135°)."""
        return f"{self.prefix}_basemap_rot.webp"


# ═══════════════════════════════════════════════════════════════════════════════
# DECK DATACLASS — Region × Classification with property delegation
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Deck(BaseDeck):
    """Complete configuration for one Anki card deck.

    Combines a Region and a Classification.  Attribute access is
    automatically delegated to ``region`` and ``classification``, so
    ``d.groups``, ``d.bbox_west``, ``d.cities`` etc. all work directly.
    """

    classification: Classification

    # ── Deck-specific file paths (depend on region × classification) ─────────
    osm_geojson: Path

    # ── Overrides ────────────────────────────────────────────────────────

    @property
    def _classification_name(self) -> str:
        return self.classification.name

    @property
    def _classification_title(self) -> str:
        return self.classification.title

    # ── Filename generation ──────────────────────────────────────────────

    def filename_group_front(self, group_id: str, ext: str = ".png") -> str:
        """Generate filename for group front card (question mark)."""
        safe_id = group_id.replace("/", "_")
        return f"{self.prefix}_group_{safe_id}_front{ext}"

    def filename_group_back(self, group_id: str, ext: str = ".png") -> str:
        """Generate filename for group back card (polygon overlay)."""
        safe_id = group_id.replace("/", "_")
        return f"{self.prefix}_group_{safe_id}_back{ext}"

    # ── Delegation ───────────────────────────────────────────────────────

    def __getattr__(self, name: str):
        """Delegate unknown attributes to region, then classification."""
        for key in ("region", "classification"):
            delegate = self.__dict__.get(key)
            if delegate is not None:
                try:
                    return getattr(delegate, name)
                except AttributeError:
                    pass
        raise AttributeError(
            f"'{type(self).__name__}' has no attribute {name!r}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# POI DECK — point-of-interest variant
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class POIDeck(BaseDeck):
    """Deck for point-of-interest cards (peaks, passes, towns, valleys, lakes).

    Extends BaseDeck with POIClassification instead of Classification.
    Templates: "Wo ist X?" and "Was ist das?"
    """

    poi_classification: POIClassification

    # ── Overrides ────────────────────────────────────────────────────────

    @property
    def _classification_name(self) -> str:
        return self.poi_classification.name

    @property
    def _classification_title(self) -> str:
        return self.poi_classification.title

    @property
    def is_poi_deck(self) -> bool:
        return True

    # ── POI convenience accessors ────────────────────────────────────────

    @property
    def pois(self) -> List[POI]:
        return self.poi_classification.pois

    @property
    def category_style(self) -> dict:
        return self.poi_classification.category_style

    def poi_by_id(self, poi_id: str) -> POI:
        return self.poi_classification.poi_by_id(poi_id)

    def pois_by_category(self, category: str) -> List[POI]:
        return self.poi_classification.pois_by_category(category)

    # ── POI-specific filenames ───────────────────────────────────────────

    def filename_poi_back(self, poi_id: str, ext: str = ".png") -> str:
        safe_id = poi_id.replace("/", "_")
        return f"{self.prefix}_poi_{safe_id}_back{ext}"

    def filename_poi_highlight(self, poi_id: str, ext: str = ".png") -> str:
        """Overlay with just the highlight circle (for 'Was ist das?' front)."""
        safe_id = poi_id.replace("/", "_")
        return f"{self.prefix}_poi_{safe_id}_highlight{ext}"

    def filename_all_pois_overlay(self, ext: str = ".png") -> str:
        """Shared overlay showing all POI markers (used as back layer)."""
        return f"{self.prefix}_all_pois{ext}"

    # ── Delegation to region + poi_classification ────────────────────────

    def __getattr__(self, name: str):
        for key in ("region", "poi_classification"):
            delegate = self.__dict__.get(key)
            if delegate is not None:
                try:
                    return getattr(delegate, name)
                except AttributeError:
                    pass
        raise AttributeError(
            f"'{type(self).__name__}' has no attribute {name!r}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# REGISTRY  —  Region × Classification → Deck
# ═══════════════════════════════════════════════════════════════════════════════

# Known regions and their default classification
REGION_DEFAULTS: Dict[str, str] = {
    "ostalpen":  "ave84",
    "westalpen": "soiusa_sz",
}

# Valid (region, system) pairs
VALID_COMBINATIONS: Dict[str, List[str]] = {
    "ostalpen":  ["ave84", "soiusa_sz", "soiusa_sts", "pois"],
    "westalpen": ["soiusa_sz", "soiusa_sts", "pois"],
}

# Subdeck merge: when building the first system, both are packed into one
# .apkg with Anki subdecks (Parent::Child naming).  The second system
# redirects to the first with a hint message.
# Format:  "region_primary_system" -> [(system, subdeck_label), ...]
SUBDECK_MERGE: Dict[str, List[Tuple[str, str]]] = {
    "ostalpen_soiusa": [
        ("soiusa_sz",  "A Gliederung"),
        ("soiusa_sts", "B Details"),
    ],
    "westalpen_soiusa": [
        ("soiusa_sz",  "A Gliederung"),
        ("soiusa_sts", "B Details"),
    ],
}


# ═══════════════════════════════════════════════════════════════════════════════
# POI MULTI-DECK — split one flat POI deck into subdecks
# ═══════════════════════════════════════════════════════════════════════════════

# Sub-regions: zoomed bbox within a parent region.
# Each sub-region reuses the parent's DEM / rivers / lakes / borders files
# but renders at its own (smaller) bounding box.

@dataclass
class SubRegion:
    """Geographic sub-region for zoomed POI decks."""
    key: str                        # e.g. "koenigsdorf"
    label: str                      # Human-readable, e.g. "Königsdorf"
    bbox_west: float
    bbox_east: float
    bbox_south: float
    bbox_north: float
    # Cities to show on the zoomed map  (name, lon, lat, dx, dy)
    cities: List[Tuple[str, float, float, float, float]]


# ── Sub-region definitions ────────────────────────────────────────────────────

SUB_REGIONS: Dict[str, List[SubRegion]] = {
    "ostalpen": [
        SubRegion(
            key="koenigsdorf",
            label="Königsdorf",
            bbox_west=11.0, bbox_east=12.0,
            bbox_south=47.23, bbox_north=47.78,
            cities=[
                ("Kochel",        11.367, 47.659,  0.05,  0.02),
                ("Bad Tölz",      11.556, 47.761,  0.05,  0.02),
                ("Garmisch-P.",   11.096, 47.492,  0.05,  0.02),
                ("Innsbruck",     11.394, 47.267,  0.05, -0.02),
            ],
        ),
        SubRegion(
            key="innsbruck",
            label="Innsbruck",
            bbox_west=10.8, bbox_east=11.9,
            bbox_south=46.9, bbox_north=47.5,
            cities=[
                ("Innsbruck",     11.394, 47.267,  0.05,  0.02),
                ("Garmisch-P.",   11.096, 47.492,  0.05, -0.02),
                ("Ehrwald",       10.918, 47.395,  0.05,  0.02),
                ("Telfs",         11.071, 47.307,  0.05,  0.02),
            ],
        ),
    ],
}


# ── Multi-deck layout ────────────────────────────────────────────────────────
# Defines how a POI deck is split into Anki subdecks.
# "sub_regions" come first (zoomed maps with thumbnail),
# "categories" follow (full map, one per POI type).

POI_MULTI_DECK: Dict[str, dict] = {
    "ostalpen_pois": {
        "parent_title": "Ostalpen Peak Soaring POIs",
        "sub_regions": [
            # (sub_region_key, subdeck_label)
            ("koenigsdorf", "A Königsdorf"),
            ("innsbruck",   "B Innsbruck"),
        ],
        "categories": [
            # (category_key, subdeck_label)
            ("peak",   "C Gipfel"),
            ("pass",   "D Pässe"),
            ("town",   "E Orte"),
            ("valley", "F Täler"),
            ("lake",   "G Seen"),
        ],
    },
}


def _get_region(name: str) -> Region:
    """Import and return a Region by name."""
    _REGION_REGISTRY = {
        "ostalpen":  "regions.ostalpen",
        "westalpen": "regions.westalpen",
    }
    module_path = _REGION_REGISTRY.get(name)
    if module_path is None:
        raise ValueError(
            f"Unknown region: {name!r}. "
            f"Valid: {list(_REGION_REGISTRY.keys())}"
        )
    from importlib import import_module
    mod = import_module(module_path)
    return mod.REGION


def _get_classification(region_name: str, system_name: str) -> Classification:
    """Import and return a Classification by region + system name."""
    _CLASSIFICATION_REGISTRY = {
        ("ostalpen",  "ave84"):      "classifications.ave84",
        ("ostalpen",  "soiusa_sz"):  "classifications.ostalpen_soiusa_sz",
        ("ostalpen",  "soiusa_sts"): "classifications.ostalpen_soiusa_sts",
        ("westalpen", "soiusa_sz"):  "classifications.westalpen_soiusa_sz",
        ("westalpen", "soiusa_sts"): "classifications.westalpen_soiusa_sts",
    }
    key = (region_name, system_name)
    if system_name == "pois":
        return None  # POI decks use _get_poi_classification instead

    module_path = _CLASSIFICATION_REGISTRY.get(key)
    if module_path is None:
        raise ValueError(
            f"Unknown combination: region={region_name!r}, system={system_name!r}. "
            f"Valid: {list(_CLASSIFICATION_REGISTRY.keys())}"
        )
    from importlib import import_module
    mod = import_module(module_path)
    return mod.CLASSIFICATION


def _get_poi_classification(region_name: str, system_name: str) -> POIClassification:
    """Import and return a POIClassification by region + system name.

    POIs are filtered by the region's bounding box, so shared POIs
    in the Ost-/Westalpen overlap zone appear in both decks.
    """
    if system_name != "pois":
        raise ValueError(f"Not a POI system: {system_name!r}")

    region = _get_region(region_name)
    from classifications.pois import pois_for_region, CATEGORY_STYLE
    filtered = pois_for_region(region)
    if not filtered:
        raise ValueError(
            f"No POIs within bbox of region {region_name!r}. "
            f"Add POIs with coordinates inside the region's bounding box."
        )
    return POIClassification(
        name="pois",
        title="Peak Soaring POIs",
        pois=filtered,
        category_style=CATEGORY_STYLE,
    )


# ── POI deck detector ────────────────────────────────────────────────────────
_POI_SYSTEMS = {"pois"}


def _make_sub_region_region(parent_region: Region, sub: SubRegion) -> Region:
    """Create a Region with the sub-region's bbox but the parent's data files.

    The sub-region bbox is symmetrically expanded so that its
    latitude-corrected aspect ratio matches the parent region's.
    This ensures that ``_corrected_figsize()`` yields identical pixel
    dimensions for all regions within the same deck.
    """
    import math

    # --- compute parent aspect ratio (latitude-corrected) ----
    p_mid = math.radians((parent_region.bbox_south + parent_region.bbox_north) / 2)
    p_lon = parent_region.bbox_east - parent_region.bbox_west
    p_lat = parent_region.bbox_north - parent_region.bbox_south
    parent_aspect = (p_lon * math.cos(p_mid)) / p_lat          # w/h

    # --- expand sub-region bbox to match parent aspect --------
    s_mid = math.radians((sub.bbox_south + sub.bbox_north) / 2)
    s_lon = sub.bbox_east - sub.bbox_west
    s_lat = sub.bbox_north - sub.bbox_south
    sub_aspect = (s_lon * math.cos(s_mid)) / s_lat

    # centre of sub-region
    cx = (sub.bbox_west + sub.bbox_east) / 2
    cy = (sub.bbox_south + sub.bbox_north) / 2

    if sub_aspect < parent_aspect:
        # sub-region is too narrow → widen (keep lat_range, increase lon_range)
        needed_lon = parent_aspect * s_lat / math.cos(s_mid)
        new_west = cx - needed_lon / 2
        new_east = cx + needed_lon / 2
        new_south = sub.bbox_south
        new_north = sub.bbox_north
    else:
        # sub-region is too wide → heighten (keep lon_range, increase lat_range)
        needed_lat = (s_lon * math.cos(s_mid)) / parent_aspect
        new_south = cy - needed_lat / 2
        new_north = cy + needed_lat / 2
        new_west = sub.bbox_west
        new_east = sub.bbox_east

    return Region(
        name=f"{parent_region.name}_{sub.key}",
        bbox_west=new_west,
        bbox_east=new_east,
        bbox_south=new_south,
        bbox_north=new_north,
        projection_params=parent_region.projection_params,
        figure_width=parent_region.figure_width,
        figure_height=parent_region.figure_height,
        cities=sub.cities,
        osm_rivers_geojson=parent_region.osm_rivers_geojson,
        osm_lakes_geojson=parent_region.osm_lakes_geojson,
        osm_valleys_geojson=parent_region.osm_valleys_geojson,
        osm_borders_geojson=parent_region.osm_borders_geojson,
        dem_tif=parent_region.dem_tif,
    )


def get_sub_region_poi_deck(
    region_name: str,
    sub_region_key: str,
) -> "POIDeck":
    """Build a POIDeck for a sub-region (zoomed bbox, filtered POIs).

    The returned deck shares output directory with the parent POI deck
    but has a unique filename prefix from the sub-region name.
    """
    parent_region = _get_region(region_name)
    subs = SUB_REGIONS.get(region_name, [])
    sub = next((s for s in subs if s.key == sub_region_key), None)
    if sub is None:
        raise ValueError(
            f"Unknown sub-region {sub_region_key!r} for {region_name!r}. "
            f"Valid: {[s.key for s in subs]}"
        )

    sub_region = _make_sub_region_region(parent_region, sub)

    from classifications.pois import pois_for_region, CATEGORY_STYLE
    filtered = pois_for_region(sub_region)
    if not filtered:
        raise ValueError(f"No POIs within sub-region {sub_region_key!r}.")

    poi_cls = POIClassification(
        name="pois",
        title=f"POIs {sub.label}",
        pois=filtered,
        category_style=CATEGORY_STYLE,
    )

    # Share output directory with parent POI deck
    output_dir = PROJECT_ROOT / "output" / f"{region_name}_pois"
    return POIDeck(
        region=sub_region,
        poi_classification=poi_cls,
        output_images_dir=output_dir / "images",
        output_csv_dir=output_dir,
        anki_csv_name=f"anki_{region_name}_pois",
    )


def _merge_key_for(region_name: str, system_name: str) -> Optional[str]:
    """Return the SUBDECK_MERGE key if this system is part of a merge, else None."""
    for key, entries in SUBDECK_MERGE.items():
        if key.startswith(f"{region_name}_"):
            if any(s == system_name for s, _ in entries):
                return key
    return None


def _make_deck(region_name: str, system_name: str):
    """Construct a Deck or POIDeck from a region + classification pair."""
    region = _get_region(region_name)
    combo_name = f"{region_name}_{system_name}"

    # Merged systems share a single output directory
    merge_key = _merge_key_for(region_name, system_name)
    output_dir = PROJECT_ROOT / "output" / (merge_key or combo_name)

    if system_name in _POI_SYSTEMS:
        poi_cls = _get_poi_classification(region_name, system_name)
        return POIDeck(
            region=region,
            poi_classification=poi_cls,
            output_images_dir=output_dir / "images",
            output_csv_dir=output_dir,
            anki_csv_name=f"anki_{merge_key or combo_name}",
        )

    classification = _get_classification(region_name, system_name)
    return Deck(
        region=region,
        classification=classification,
        osm_geojson=DATA_DIR_OSM / f"{combo_name}.geojson",
        output_images_dir=output_dir / "images",
        output_csv_dir=output_dir,
        anki_csv_name=f"anki_{merge_key or combo_name}",
    )


# Lazy singletons — constructed on first access
_decks: Dict[str, Deck] = {}


def get_deck(region: str = "ostalpen", system: Optional[str] = None) -> Deck:
    """Return a Deck instance by region + system (cached).

    If *system* is ``None``, uses the default for the region.
    """
    if region not in REGION_DEFAULTS:
        raise ValueError(
            f"Unknown region: {region!r}. Choose from: {list(REGION_DEFAULTS.keys())}"
        )
    if system is None:
        system = REGION_DEFAULTS[region]
    if system not in VALID_COMBINATIONS.get(region, []):
        raise ValueError(
            f"Unknown system {system!r} for region {region!r}. "
            f"Valid: {VALID_COMBINATIONS[region]}"
        )

    key = f"{region}_{system}"
    if key not in _decks:
        _decks[key] = _make_deck(region, system)
    return _decks[key]


def add_deck_arguments(parser) -> None:
    """Add --region and --system CLI arguments to an ArgumentParser."""
    parser.add_argument(
        "--region",
        choices=list(REGION_DEFAULTS.keys()),
        default="ostalpen",
        help="Which region to process (default: ostalpen)",
    )
    valid_systems = sorted({s for ss in VALID_COMBINATIONS.values() for s in ss})
    parser.add_argument(
        "--system",
        choices=valid_systems,
        default=None,
        help="Classification system (default: region-dependent)",
    )

