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
for _d in [DATA_DIR_OSM, DATA_DIR_DEM]:
    _d.mkdir(parents=True, exist_ok=True)

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
HILLSHADE_ALTITUDE = 45
HILLSHADE_VERT_EXAG = 0.05
HILLSHADE_BLEND_MODE = "soft"

# ─── Output format ───────────────────────────────────────────────────────────
# All images are WebP.  Two modes used internally:
#   "basemap"   - Shared basemap raster (opaque, lossy WebP)
#   "overlay"   - Vector-only overlay (transparent, lossless WebP)
OUTPUT_FORMAT = "overlay"

# ─── Rivers & Lakes ──────────────────────────────────────────────────────────
OCEAN_COLOR = "#c6ddf0"
RIVER_COLOR = "#4A7FB5"
RIVER_LINEWIDTH = 0.4
RIVER_MIN_LENGTH_KM = 20          # Minimum total river length (km) to display
LAKE_FACECOLOR = "#7FAFCF"
LAKE_EDGECOLOR = "#4A7FB5"
LAKE_LINEWIDTH = 0.3
LAKE_MIN_AREA_KM2 = 1.0           # Minimum lake area (km²) for OSM lakes

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
# DECK DATACLASS — Region × Classification with property delegation
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Deck:
    """Complete configuration for one Anki card deck.

    Combines a Region and a Classification.  Attribute access is
    automatically delegated to ``region`` and ``classification``, so
    ``d.groups``, ``d.bbox_west``, ``d.cities`` etc. all work directly.
    """

    region: Region
    classification: Classification

    # ── Deck-specific file paths (depend on region × classification) ─────────
    osm_geojson: Path
    output_images_dir: Path
    output_csv_dir: Path
    anki_csv_name: str          # e.g. "anki_ostalpen_ave84"

    def __post_init__(self):
        self.output_images_dir.mkdir(parents=True, exist_ok=True)
        self.output_csv_dir.mkdir(parents=True, exist_ok=True)

    # ── Identity ─────────────────────────────────────────────────────────────

    @property
    def name(self) -> str:
        return f"{self.region.name}_{self.classification.name}"

    @property
    def title(self) -> str:
        return f"{self.region.name.capitalize()} — {self.classification.title}"

    # ── Filename generation (with ps_ prefix for Peak Soaring) ───────────────

    @property
    def prefix(self) -> str:
        return f"ps_{self.region.name}_{self.classification.name}"

    def filename_partition(self, ext: str = ".png") -> str:
        """Generate filename for partition map (Einteilung)."""
        return f"{self.prefix}_partition{ext}"

    def filename_group_front(self, group_id: str, ext: str = ".png") -> str:
        """Generate filename for group front card (question mark)."""
        safe_id = group_id.replace("/", "_")
        return f"{self.prefix}_group_{safe_id}_front{ext}"

    def filename_group_back(self, group_id: str, ext: str = ".png") -> str:
        """Generate filename for group back card (polygon overlay)."""
        safe_id = group_id.replace("/", "_")
        return f"{self.prefix}_group_{safe_id}_back{ext}"

    def filename_context(self) -> str:
        """Generate filename for shared context overlay (borders + cities)."""
        return f"{self.prefix}_context.webp"

    def filename_basemap(self) -> str:
        """Generate filename for shared basemap WebP (hillshade + rivers + lakes)."""
        return f"{self.prefix}_basemap.webp"

    # ── Delegation ───────────────────────────────────────────────────────────

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
class POIDeck:
    """Deck for point-of-interest cards (peaks, passes, towns, valleys).

    Parallel to Deck but uses POIClassification instead of Classification.
    Templates: "Wo ist X?" and "Was ist das?"
    """

    region: Region
    poi_classification: POIClassification
    output_images_dir: Path
    output_csv_dir: Path
    anki_csv_name: str

    def __post_init__(self):
        self.output_images_dir.mkdir(parents=True, exist_ok=True)
        self.output_csv_dir.mkdir(parents=True, exist_ok=True)

    @property
    def is_poi_deck(self) -> bool:
        return True

    @property
    def name(self) -> str:
        return f"{self.region.name}_{self.poi_classification.name}"

    @property
    def title(self) -> str:
        return f"{self.region.name.capitalize()} — {self.poi_classification.title}"

    @property
    def prefix(self) -> str:
        return f"ps_{self.region.name}_{self.poi_classification.name}"

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

    def filename_partition(self, ext: str = ".png") -> str:
        return f"{self.prefix}_partition{ext}"

    def filename_context(self) -> str:
        return f"{self.prefix}_context.webp"

    def filename_basemap(self) -> str:
        return f"{self.prefix}_basemap.webp"

    def filename_poi_front(self, poi_id: str, ext: str = ".png") -> str:
        safe_id = poi_id.replace("/", "_")
        return f"{self.prefix}_poi_{safe_id}_front{ext}"

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

    # ── Delegation to region ─────────────────────────────────────────────────

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
    "westalpen": ["soiusa_sz", "soiusa_sts"],
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


def _get_region(name: str) -> Region:
    """Import and return a Region by name."""
    if name == "ostalpen":
        from regions.ostalpen import REGION
        return REGION
    elif name == "westalpen":
        from regions.westalpen import REGION
        return REGION
    else:
        raise ValueError(f"Unknown region: {name!r}")


def _get_classification(region_name: str, system_name: str) -> Classification:
    """Import and return a Classification by region + system name."""
    key = (region_name, system_name)
    if key == ("ostalpen", "ave84"):
        from classifications.ave84 import CLASSIFICATION
        return CLASSIFICATION
    elif key == ("westalpen", "soiusa_sz"):
        from classifications.westalpen_soiusa_sz import CLASSIFICATION
        return CLASSIFICATION
    elif key == ("westalpen", "soiusa_sts"):
        from classifications.westalpen_soiusa_sts import CLASSIFICATION
        return CLASSIFICATION
    elif key == ("ostalpen", "soiusa_sz"):
        from classifications.ostalpen_soiusa_sz import CLASSIFICATION
        return CLASSIFICATION
    elif key == ("ostalpen", "soiusa_sts"):
        from classifications.ostalpen_soiusa_sts import CLASSIFICATION
        return CLASSIFICATION
    elif key == ("ostalpen", "pois"):
        return None  # POI decks use _get_poi_classification instead
    else:
        raise ValueError(
            f"Unknown combination: region={region_name!r}, system={system_name!r}. "
            f"Valid: {VALID_COMBINATIONS}"
        )


def _get_poi_classification(region_name: str, system_name: str) -> POIClassification:
    """Import and return a POIClassification by region + system name."""
    key = (region_name, system_name)
    if key == ("ostalpen", "pois"):
        from classifications.pois import ALL_POIS, CATEGORY_STYLE
        return POIClassification(
            name="pois",
            title="Peak Soaring POIs",
            pois=ALL_POIS,
            category_style=CATEGORY_STYLE,
        )
    else:
        raise ValueError(f"No POI classification for {key}")


# ── POI deck detector ────────────────────────────────────────────────────────
_POI_SYSTEMS = {"pois"}


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

