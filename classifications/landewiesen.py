"""
Aussenladewiesenkatalog — Outlanding fields from streckenflug.at
================================================================
Parses the CUP waypoint data from the streckenflug.at ZIP archive
and exposes outlanding fields as POI objects.

Source: streckenflug-at_landewiesen_20260303.zip
Format: ZIP → CUPX (inner ZIP) → POINTS.CUP (CSV) + Pics/*.jpg

615 outlanding fields across the Alps:
  - 327 Kat A  (recommended)     — green markers
  - 288 Kat B  (emergency only)  — orange markers
  -  65 Airstrips (style=2)      — blue markers (subset of A/B)

Each CUPX embeds JPG images (satellite + field photos) linked via
the ``pics`` CSV field.  Python's ``zipfile`` cannot see them because
the Central Directory only lists POINTS.CUP — the images are stored
in Local File Headers preceded by a 256-byte CUPX header.  We parse
them manually with ``struct``.

CUP coordinate format: DDMM.MMMN / DDDMM.MMME → WGS84 decimal.
"""

import csv
import io
import math
import re
import struct
import zipfile
import zlib
from pathlib import Path
from typing import Dict, List, Tuple

from models import POI

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════════════════

# Flugplatz Königsdorf — reference point for sorting by distance
# Located between Geretsried and Bad Tölz, ~20 km N of Benediktenwand
_KOENIGSDORF_LAT = 47.820
_KOENIGSDORF_LON = 11.480

# Aérodrome de Puimoisson — reference for Westalpen sorting
_PUIMOISSON_LAT = 43.883
_PUIMOISSON_LON = 6.167

# Region name → reference airfield
_SORT_ORIGIN = {
    "ostalpen":  (_KOENIGSDORF_LAT, _KOENIGSDORF_LON),
    "westalpen": (_PUIMOISSON_LAT, _PUIMOISSON_LON),
}

# ZIP file containing all CUPX archives
_ZIP_FILE = Path(__file__).parent.parent / "data" / "streckenflug-at_landewiesen_20260303.zip"

# Directory where extracted CUPX images are cached
_PICS_DIR = Path(__file__).parent.parent / "data" / "landewiesen_pics"

# CUPX files relevant for Ost/Westalpen
_CUPX_FILES = [
    "zentral_und_ostalpen_de.cupx",
    "westalpen_de.cupx",
]


# ═══════════════════════════════════════════════════════════════════════════════
# RAW CUPX PARSER  (reads Local File Headers directly)
# ═══════════════════════════════════════════════════════════════════════════════

def _parse_local_file_headers(data: bytes) -> List[dict]:
    """Scan raw bytes for ZIP Local File Headers (PK\\x03\\x04).

    Returns a list of dicts with keys: name, data (decompressed bytes).
    Works around the broken Central Directory in streckenflug.at CUPX files.
    """
    entries: List[dict] = []
    pos = 0
    sig = b"PK\x03\x04"

    while pos < len(data) - 30:
        idx = data.find(sig, pos)
        if idx == -1:
            break

        header = data[idx : idx + 30]
        if len(header) < 30:
            break

        (_, _ver, _flags, method, _mt, _md,
         _crc, comp_size, uncomp_size,
         name_len, extra_len) = struct.unpack("<4sHHHHHIIIHH", header)

        name = data[idx + 30 : idx + 30 + name_len].decode("utf-8", errors="replace")
        data_start = idx + 30 + name_len + extra_len
        raw = data[data_start : data_start + comp_size]

        if method == 8:  # deflate
            payload = zlib.decompress(raw, -15)
        else:
            payload = raw

        entries.append({"name": name, "data": payload})
        pos = data_start + comp_size
        if pos <= idx:
            pos = idx + 4  # safety: advance past current header

    return entries


def _extract_cupx(cupx_bytes: bytes) -> Tuple[str, Dict[str, bytes]]:
    """Extract POINTS.CUP text and Pics/* images from raw CUPX bytes.

    Returns (cup_csv_text, {pic_filename: jpg_bytes}).
    """
    entries = _parse_local_file_headers(cupx_bytes)

    cup_text = ""
    pics: Dict[str, bytes] = {}

    for entry in entries:
        name: str = entry["name"]
        if name.upper().endswith(".CUP"):
            cup_text = entry["data"].decode("utf-8-sig")
        elif name.lower().startswith("pics/") and name.lower().endswith(".jpg"):
            # Store with just the filename (no Pics/ prefix)
            pic_name = name.split("/", 1)[1]
            pics[pic_name] = entry["data"]

    return cup_text, pics


def _ensure_pics_extracted() -> None:
    """Extract all CUPX images to _PICS_DIR (one-time, idempotent)."""
    if not _ZIP_FILE.exists():
        return

    marker = _PICS_DIR / ".extracted"
    if marker.exists():
        return  # already done

    _PICS_DIR.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(_ZIP_FILE) as outer_zip:
        for cupx_name in _CUPX_FILES:
            cupx_bytes = outer_zip.read(cupx_name)
            _cup_text, pics = _extract_cupx(cupx_bytes)
            for pic_name, jpg_data in pics.items():
                dest = _PICS_DIR / pic_name
                if not dest.exists():
                    dest.write_bytes(jpg_data)

    marker.write_text(f"extracted from {_ZIP_FILE.name}\n")
    print(f"  Extracted {len(list(_PICS_DIR.glob('*.jpg')))} images → {_PICS_DIR}")


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

        # Parse pics field: "1_165_osm.jpg;2_186.jpg" → list
        pics_raw = row.get("pics", "").strip()
        pics_list = [p.strip() for p in pics_raw.split(";") if p.strip()] if pics_raw else []

        poi = POI(
            poi_id=code,
            name=name,
            category=category,
            lat=lat,
            lon=lon,
            elevation=elev,
            subtitle=subtitle,
            tags=[row.get("country", "").strip()],
            pics=pics_list,
        )
        pois.append(poi)

    return pois


# ═══════════════════════════════════════════════════════════════════════════════
# LOAD ALL WAYPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

def _load_all_landewiesen() -> List[POI]:
    """Read all outlanding waypoints from the streckenflug.at ZIP.

    Uses raw Local File Header parsing to access both POINTS.CUP and
    the embedded Pics/*.jpg images that Python's zipfile cannot see.
    """
    if not _ZIP_FILE.exists():
        raise FileNotFoundError(
            f"Landewiesen ZIP not found: {_ZIP_FILE}\n"
            "Download from streckenflug.at and place in data/"
        )

    # Extract images to disk (idempotent)
    _ensure_pics_extracted()

    seen_codes: set = set()
    all_pois: List[POI] = []

    with zipfile.ZipFile(_ZIP_FILE) as outer_zip:
        for cupx_name in _CUPX_FILES:
            cupx_bytes = outer_zip.read(cupx_name)
            cup_text, _pics = _extract_cupx(cupx_bytes)
            pois = _parse_cup_rows(cup_text)
            for p in pois:
                if p.poi_id not in seen_codes:
                    seen_codes.add(p.poi_id)
                    all_pois.append(p)

    # Sort by code for deterministic ordering
    all_pois.sort(key=lambda p: p.poi_id)
    return all_pois


# Module-level cache
ALL_LANDEWIESEN: List[POI] = _load_all_landewiesen()


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in km between two WGS84 points."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def landewiesen_for_region(region) -> List[POI]:
    """Return outlanding fields within the region's bounding box,
    sorted by distance to the region's reference airfield (nearest first).

    Ostalpen  → Flugplatz Königsdorf
    Westalpen → Aérodrome de Puimoisson
    """
    filtered = [
        p for p in ALL_LANDEWIESEN
        if region.bbox_south <= p.lat <= region.bbox_north
        and region.bbox_west <= p.lon <= region.bbox_east
    ]
    origin = _SORT_ORIGIN.get(region.name, (_KOENIGSDORF_LAT, _KOENIGSDORF_LON))
    filtered.sort(key=lambda p: _haversine_km(origin[0], origin[1], p.lat, p.lon))
    return filtered


def pic_path(filename: str) -> Path:
    """Return the absolute path to an extracted CUPX image."""
    return _PICS_DIR / filename


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
