"""
download_soiusa_umap.py — Download SOIUSA Sezioni polygons from uMap
=====================================================================
Downloads the 14 Western Alps Sezioni (SZ.1–SZ.14) from the uMap
"SOIUSA" (https://umap.openstreetmap.fr/de/map/soiusa_954288),
originally created by Capleymar based on homoalpinus.com data.

Converts them into the standard GeoJSON format expected by the
card generation pipeline (matching on ``ref:soiusa`` property).

Usage:
    python scripts/download_soiusa_umap.py          # download + convert
    python scripts/download_soiusa_umap.py --force   # overwrite existing
"""

import argparse
import json
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from deck import DATA_DIR_OSM

OUTPUT_FILE = DATA_DIR_OSM / "westalpen_soiusa.geojson"

# uMap datalayer UUIDs for the two Western Alps sectors
LAYERS = {
    "SR.I/A": "54af742b-a4e6-41bd-a7c9-db8e3ecd33cb",  # SZ.1–6
    "SR.I/B": "9577af2a-89dc-41fe-8616-9dd9f773abf4",  # SZ.7–14
}

UMAP_BASE = "https://umap.openstreetmap.fr/de/datalayer/954288"


def _strip_z(coords):
    """Recursively strip the Z coordinate (always 0) from coordinate arrays."""
    if isinstance(coords[0], (int, float)):
        return coords[:2]
    return [_strip_z(c) for c in coords]


def download_layer(uuid: str, label: str) -> list:
    """Download a single uMap datalayer and return its features."""
    url = f"{UMAP_BASE}/{uuid}/"
    print(f"[SOIUSA] Downloading {label} from {url} …")
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    features = data.get("features", [])
    print(f"[SOIUSA]   → {len(features)} features")
    return features


def convert_feature(feat: dict) -> dict:
    """Convert a uMap feature into our standard GeoJSON format.

    - Strips Z coordinates
    - Extracts SZ number as ``ref:soiusa`` property
    - Preserves multilingual names and peak info
    """
    props = feat.get("properties", {})
    code = props.get("code", "")  # e.g. "SZ.1"

    # Extract the numeric part: "SZ.1" → "1", "SZ.14" → "14"
    sz_num = code.replace("SZ.", "") if code.startswith("SZ.") else code

    new_props = {
        "ref:soiusa": sz_num,
        "code": code,
        "name:de": props.get("name-de", ""),
        "name:fr": props.get("name-fr", ""),
        "name:it": props.get("name-it", ""),
        "name:en": props.get("name-en", ""),
        "point_culminant": props.get("point_culminant", ""),
        "point_culminant_hauteur": props.get("point_culminant_hauteur", ""),
    }

    geom = feat.get("geometry", {})
    geom_stripped = {
        "type": geom["type"],
        "coordinates": _strip_z(geom["coordinates"]),
    }

    return {
        "type": "Feature",
        "properties": new_props,
        "geometry": geom_stripped,
    }


def main():
    parser = argparse.ArgumentParser(description="Download SOIUSA polygons from uMap")
    parser.add_argument("--force", action="store_true", help="Overwrite existing file")
    args = parser.parse_args()

    if OUTPUT_FILE.exists() and not args.force:
        print(f"[SOIUSA] Already exists: {OUTPUT_FILE}")
        print(f"[SOIUSA] Use --force to overwrite.")
        return

    all_features = []
    for label, uuid in LAYERS.items():
        raw_features = download_layer(uuid, label)
        for feat in raw_features:
            converted = convert_feature(feat)
            all_features.append(converted)

    # Sort by SZ number
    all_features.sort(key=lambda f: int(f["properties"]["ref:soiusa"]))

    geojson = {
        "type": "FeatureCollection",
        "features": all_features,
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)

    print(f"[SOIUSA] Saved {len(all_features)} features → {OUTPUT_FILE}")

    # Summary
    for feat in all_features:
        p = feat["properties"]
        print(f"  SZ.{p['ref:soiusa']:>2}  {p['name:de']:<35}  {p['point_culminant']} ({p['point_culminant_hauteur']} m)")


if __name__ == "__main__":
    main()
