"""
Aussenladewiesenkatalog — Outlanding fields from streckenflug.at
================================================================
Parses the CUP waypoint data from the streckenflug.at ZIP archive
and exposes outlanding fields as POI objects.

Source: streckenflug-at_landewiesen_20260303.zip
Format: ZIP → CUPX (inner ZIP) → POINTS.CUP (CSV)

615 outlanding fields across the Alps:
  - 327 Kat A  (recommended)     — green markers
  - 288 Kat B  (emergency only)  — orange markers
  -  65 Airstrips (style=2)      — blue markers (subset of A/B)

CUP coordinate format: DDMM.MMMN / DDDMM.MMME → WGS84 decimal.
"""

import csv
import io
import re
import zipfile
from pathlib import Path
from typing import List

from models import POI

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════════════════

# ZIP file containing all CUPX archives
_ZIP_FILE = Path(__file__).parent.parent / "data" / "streckenflug-at_landewiesen_20260303.zip"

# CUPX files relevant for Ost/Westalpen
_CUPX_FILES = [
    "zentral_und_ostalpen_de.cupx",
    "westalpen_de.cupx",
]


# ═══════════════════════════════════════════════════════════════════════════════
# CUP PARSER
# ═══════════════════════════════════════════════════════════════════════════════

def _cup_lat_to_decimal(lat_str: str) -> float:
    """Convert CUP latitude 'DDMM.MMMN/S' to decimal degrees."""
    m = re.match(r"(\d{2})(\d{2}\.\d+)([NS])", lat_str)
    if not m:
        raise ValueError(f"Invalid CUP latitude: {lat_str!r}")
    deg = int(m.group(1)) + float(m.group(2)) / 60.0
    return -deg if m.group(3) == "S" else deg


def _cup_lon_to_decimal(lon_str: str) -> float:
    """Convert CUP longitude 'DDDMM.MMME/W' to decimal degrees."""
    m = re.match(r"(\d{3})(\d{2}\.\d+)([EW])", lon_str)
    if not m:
        raise ValueError(f"Invalid CUP longitude: {lon_str!r}")
    deg = int(m.group(1)) + float(m.group(2)) / 60.0
    return -deg if m.group(3) == "W" else deg


def _parse_name_and_kat(raw_name: str) -> tuple:
    """Extract clean name and Kat category from CUP name field.

    'Admont (Kat A 2024)' → ('Admont', 'A', 2024)
    """
    m = re.match(r"^(.+?)\s*\(Kat\s+([AB])\s+(\d{4})\)$", raw_name)
    if m:
        return m.group(1).strip(), m.group(2), int(m.group(3))
    return raw_name.strip(), None, None


def _build_subtitle(row: dict) -> str:
    """Build a compact subtitle from CUP fields.

    Format: '350m × 100m, Richtung 060° · Wiese, Leitung(en)'
    """
    parts = []

    # Runway dimensions
    rwlen = row.get("rwlen", "").strip()
    rwwidth = row.get("rwwidth", "").strip()
    if rwlen and rwlen != "0m":
        dim = rwlen
        if rwwidth and rwwidth != "0m":
            dim += f" × {rwwidth}"
        parts.append(dim)

    # Runway direction
    rwdir = row.get("rwdir", "").strip()
    if rwdir and rwdir != "0" and rwdir != "000":
        parts.append(f"Richtung {rwdir}°")

    dim_str = ", ".join(parts)

    # Description
    desc = row.get("desc", "").strip()

    if dim_str and desc:
        return f"{dim_str} · {desc}"
    return dim_str or desc


def _parse_cup_rows(cup_csv: str) -> List[POI]:
    """Parse CUP CSV text into POI objects."""
    reader = csv.DictReader(io.StringIO(cup_csv))
    pois = []

    for row in reader:
        raw_name = row.get("name", "").strip()
        code = row.get("code", "").strip()
        if not raw_name or not code:
            continue

        name, kat, _year = _parse_name_and_kat(raw_name)

        lat = _cup_lat_to_decimal(row["lat"])
        lon = _cup_lon_to_decimal(row["lon"])

        elev_str = row.get("elev", "").replace("m", "").strip()
        elev = int(float(elev_str)) if elev_str else None

        style = row.get("style", "").strip()

        # Category: airstrip (style=2) vs. outlanding (Kat A/B)
        if style == "2":
            category = "airstrip"
        elif kat == "A":
            category = "landefeld_a"
        elif kat == "B":
            category = "landefeld_b"
        else:
            category = "landefeld_a"  # fallback

        subtitle = _build_subtitle(row)

        poi = POI(
            poi_id=code,
            name=name,
            category=category,
            lat=lat,
            lon=lon,
            elevation=elev,
            subtitle=subtitle,
            tags=[row.get("country", "").strip()],
        )
        pois.append(poi)

    return pois


# ═══════════════════════════════════════════════════════════════════════════════
# LOAD ALL WAYPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

def _load_all_landewiesen() -> List[POI]:
    """Read all outlanding waypoints from the streckenflug.at ZIP."""
    if not _ZIP_FILE.exists():
        raise FileNotFoundError(
            f"Landewiesen ZIP not found: {_ZIP_FILE}\n"
            "Download from streckenflug.at and place in data/"
        )

    seen_codes: set = set()
    all_pois: List[POI] = []

    with zipfile.ZipFile(_ZIP_FILE) as outer_zip:
        for cupx_name in _CUPX_FILES:
            cupx_bytes = outer_zip.read(cupx_name)
            with zipfile.ZipFile(io.BytesIO(cupx_bytes)) as cupx_zip:
                cup_data = cupx_zip.read("POINTS.CUP").decode("utf-8-sig")
                pois = _parse_cup_rows(cup_data)
                for p in pois:
                    if p.poi_id not in seen_codes:
                        seen_codes.add(p.poi_id)
                        all_pois.append(p)

    # Sort by code for deterministic ordering
    all_pois.sort(key=lambda p: p.poi_id)
    return all_pois


# Module-level cache
ALL_LANDEWIESEN: List[POI] = _load_all_landewiesen()


def landewiesen_for_region(region) -> List[POI]:
    """Return outlanding fields within the region's bounding box."""
    return [
        p for p in ALL_LANDEWIESEN
        if region.bbox_south <= p.lat <= region.bbox_north
        and region.bbox_west <= p.lon <= region.bbox_east
    ]


# ── Category display properties ──────────────────────────────────────────────
CATEGORY_STYLE = {
    "landefeld_a": {
        "marker": "^",
        "color": "#27AE60",
        "size": 6,
        "label": "Kat A",
    },
    "landefeld_b": {
        "marker": "v",
        "color": "#E67E22",
        "size": 6,
        "label": "Kat B",
    },
    "airstrip": {
        "marker": "s",
        "color": "#2E86C1",
        "size": 5,
        "label": "Airstrip",
    },
}
