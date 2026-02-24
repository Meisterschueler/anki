"""
download_soiusa_arpa.py — Download SOIUSA polygons from ARPA Piemonte
======================================================================
Downloads SOIUSA orographic classification polygons from the ARPA
Piemonte FeatureServer.  Supports all six hierarchical levels:

    PT   Parte               (2 features)
    SR   Grande Settore      (5 features)
    SZ   Sezione             (36 features)
    STS  Sottosezione        (~130 features)
    SPG  Supergruppo         (~200 features)
    GR   Gruppo              (~870 features)

The FeatureServer stores all data at the Gruppo (GR) level.  Higher
levels (STS, SZ, …) are obtained by dissolving Gruppo polygons on
the requested attribute using Shapely.

The service covers the **entire Alps**, not just the Western Alps.
Use ``--filter`` to limit by PT value (e.g. ``"Alpi Occidentali"``).

Source:
    https://webgis.arpa.piemonte.it/ags/rest/services/topografia_dati_di_base/SOIUSA/FeatureServer

Copyright:
    Massimo Accorsi (digitalizzazione), Sergio Marazzi et al.
    (autori della suddivisione), Arpa Piemonte (geoservizio).
    Free use with mandatory attribution.

Usage:
    python scripts/download_soiusa_arpa.py --level SZ
    python scripts/download_soiusa_arpa.py --level STS --filter "Alpi Occidentali"
    python scripts/download_soiusa_arpa.py --level GR --output data/osm/alpen_soiusa_gr.geojson
"""

import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlencode

import requests
from shapely.geometry import mapping, shape
from shapely.ops import unary_union

# ─── project imports ──────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent.parent))
from deck import DATA_DIR_OSM

# ─── constants ────────────────────────────────────────────────────────────────

BASE_URL = (
    "https://webgis.arpa.piemonte.it/ags/rest/services/"
    "topografia_dati_di_base/SOIUSA/FeatureServer"
)

# All polygon layers contain the same ~873 Gruppo-level features.
# We always query the GR layer (11) and dissolve to the requested level.
QUERY_LAYER_ID = 11

# Valid SOIUSA hierarchy levels (ordered coarse → fine)
VALID_LEVELS = ["PT", "SR", "SZ", "STS", "SPG", "GR", "STG"]

MAX_RECORD_COUNT = 2000  # Server-side limit per request

# Mapping from region short name → PT attribute value
REGION_FILTER = {
    "westalpen":  "Alpi Occidentali",
    "ostalpen":   "Alpi Orientali",
    "zentralalpen": "Alpi Centrali",
}


def _build_query_url() -> str:
    """Return the query endpoint URL for the GR layer."""
    return f"{BASE_URL}/{QUERY_LAYER_ID}/query"


def _fetch_page(
    where: str = "1=1",
    offset: int = 0,
    max_retries: int = 3,
) -> dict:
    """Fetch one page of GeoJSON features from the FeatureServer."""
    params = {
        "where": where,
        "outFields": "*",
        "outSR": "4326",           # WGS84
        "f": "geojson",
        "resultOffset": str(offset),
        "resultRecordCount": str(MAX_RECORD_COUNT),
    }
    url = _build_query_url()

    for attempt in range(1, max_retries + 1):
        try:
            print(f"[ARPA] Fetching offset={offset}  (attempt {attempt}/{max_retries}) …")
            resp = requests.get(
                url,
                params=params,
                timeout=120,
            )
            resp.raise_for_status()
            return resp.json()
        except (requests.exceptions.Timeout, requests.exceptions.HTTPError) as exc:
            if attempt < max_retries:
                wait = 5 * attempt
                print(f"[ARPA]   failed: {exc}.  Retrying in {wait}s …")
                time.sleep(wait)
            else:
                raise


def fetch_all_features(
    where: str = "1=1",
) -> list[dict]:
    """Download all Gruppo-level features, handling pagination."""
    all_features: list[dict] = []
    offset = 0

    while True:
        data = _fetch_page(where=where, offset=offset)
        features = data.get("features", [])
        if not features:
            break
        all_features.extend(features)
        print(f"[ARPA]   → received {len(features)} features (total so far: {len(all_features)})")

        # If we got fewer than the max, we've reached the last page
        if len(features) < MAX_RECORD_COUNT:
            break
        offset += len(features)

    return all_features


def dissolve_to_level(features: list[dict], level: str) -> list[dict]:
    """Group Gruppo-level features by the requested level and dissolve geometries.

    For level ``GR`` no dissolve is needed — each feature is already one Gruppo.
    For coarser levels (STS, SZ, …) polygons sharing the same attribute value
    are merged using Shapely's ``unary_union``.
    """
    if level == "GR":
        # No dissolve needed, just normalise properties
        return _normalise_gr_features(features)

    # Determine which hierarchy fields are parents of the requested level
    level_idx = VALID_LEVELS.index(level)
    parent_fields = VALID_LEVELS[: level_idx + 1]

    # Group features by the requested level's name
    groups: dict[str, dict] = defaultdict(lambda: {"geometries": [], "props": {}})

    for feat in features:
        props = feat.get("properties", {})
        key = (props.get(level) or "").strip()
        if not key:
            continue

        geom = feat.get("geometry")
        if geom:
            try:
                groups[key]["geometries"].append(shape(geom))
            except Exception:
                pass  # skip invalid geometries

        # Store parent attributes (first occurrence wins)
        if not groups[key]["props"]:
            groups[key]["props"] = {
                field: (props.get(field) or "").strip()
                for field in parent_fields
                if (props.get(field) or "").strip()
            }

    # Dissolve and build output features
    dissolved = []
    for name, group in groups.items():
        if not group["geometries"]:
            continue

        merged = unary_union(group["geometries"])
        new_props = {
            "name": name,
            **group["props"],
        }
        dissolved.append({
            "type": "Feature",
            "properties": new_props,
            "geometry": mapping(merged),
        })

    # Sort by name for reproducible output
    dissolved.sort(key=lambda f: f["properties"]["name"])
    return dissolved


def _normalise_gr_features(features: list[dict]) -> list[dict]:
    """Normalise Gruppo-level features without dissolving."""
    result = []
    for feat in features:
        props = feat.get("properties", {})
        new_props = {
            "name": (props.get("GR") or "").strip(),
            "ref:soiusa": (props.get("CODICE") or "").strip(),
        }
        # Add all hierarchy fields
        for field in VALID_LEVELS:
            value = (props.get(field) or "").strip()
            if value:
                new_props[field] = value

        result.append({
            "type": "Feature",
            "properties": new_props,
            "geometry": feat.get("geometry"),
        })

    result.sort(key=lambda f: f["properties"].get("ref:soiusa", ""))
    return result


def build_where_clause(
    filter_pt: str | None = None,
    region: str | None = None,
) -> str:
    """Build the SQL WHERE clause for the query.

    ``--filter`` takes precedence and is used as a raw PT filter.
    ``--region`` is a convenience shortcut for common regions.
    """
    pt_value = None
    if filter_pt:
        pt_value = filter_pt
    elif region and region in REGION_FILTER:
        pt_value = REGION_FILTER[region]

    if pt_value:
        # Escape single quotes in the value
        safe = pt_value.replace("'", "''")
        return f"PT = '{safe}'"

    return "1=1"


def default_output_path(level: str, region: str | None, filter_pt: str | None) -> Path:
    """Compute a sensible default output filename."""
    parts = []
    if region:
        parts.append(region)
    elif filter_pt:
        # Derive a slug from the filter value
        slug = filter_pt.lower().replace(" ", "_").replace("'", "")
        parts.append(slug)
    else:
        parts.append("alpen")
    parts.append(f"soiusa_{level.lower()}")
    filename = "_".join(parts) + ".geojson"
    return DATA_DIR_OSM / filename


def main():
    parser = argparse.ArgumentParser(
        description="Download SOIUSA polygons from ARPA Piemonte FeatureServer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --level SZ                           # All Sezioni (entire Alps)
  %(prog)s --level STS --region westalpen       # Western Alps Sottosezioni
  %(prog)s --level GR  --filter "Alpi Orientali" --output gr_east.geojson
  %(prog)s --level PT                           # Just the 2 Parti

Available levels: PT, SR, SZ, STS, SPG, GR
        """,
    )
    parser.add_argument(
        "--level",
        required=True,
        choices=[l for l in VALID_LEVELS if l != "STG"],
        help="SOIUSA hierarchy level to download",
    )
    parser.add_argument(
        "--region",
        choices=list(REGION_FILTER.keys()),
        default=None,
        help="Pre-defined region filter (shortcut for --filter)",
    )
    parser.add_argument(
        "--filter",
        dest="filter_pt",
        default=None,
        help="Filter by PT value (e.g. 'Alpi Occidentali')",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=None,
        help="Output GeoJSON file path (default: data/osm/<region>_soiusa_<level>.geojson)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing output file",
    )
    args = parser.parse_args()

    # Determine output path
    output = args.output or default_output_path(args.level, args.region, args.filter_pt)
    if output.exists() and not args.force:
        print(f"[ARPA] Already exists: {output}")
        print(f"[ARPA] Use --force to overwrite.")
        return

    # Build WHERE clause
    where = build_where_clause(args.filter_pt, args.region)
    region_label = args.region or args.filter_pt or "alle Alpen"
    print(f"[ARPA] Downloading SOIUSA level {args.level} for {region_label}")
    print(f"[ARPA] WHERE: {where}")

    # Download all Gruppo-level features
    raw_features = fetch_all_features(where=where)
    if not raw_features:
        print("[ARPA] No features returned. Check your filter.")
        sys.exit(1)

    print(f"[ARPA] Downloaded {len(raw_features)} Gruppo-level features")

    # Dissolve to requested level
    if args.level != "GR":
        print(f"[ARPA] Dissolving to {args.level} level …")
    features = dissolve_to_level(raw_features, args.level)
    geojson = {
        "type": "FeatureCollection",
        "features": features,
    }

    # Save
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)

    print(f"[ARPA] Saved {len(features)} features → {output}")

    # Summary
    print(f"\n{'#':<5} {'Name'}")
    print("─" * 60)
    for i, feat in enumerate(features, 1):
        p = feat["properties"]
        print(f"  {i:<3}  {p.get('name', '')}")


if __name__ == "__main__":
    main()
