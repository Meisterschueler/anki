"""
prepare_einzugsgebiete.py — Prepare drainage basin polygons from HydroBASINS
=============================================================================
Downloads HydroBASINS Level 8 data for Europe, clips to the Ostalpen bbox,
groups sub-basins into ~10 major river systems, and exports a GeoJSON file
ready for the rendering pipeline.

Data source:
    HydroBASINS (HydroSHEDS project)
    https://www.hydrosheds.org/products/hydrobasins
    License: free for scientific, educational, and commercial use.
    Citation: Lehner, B., Grill G. (2013). Hydrological Processes, 27(15).

Output:
    data/osm/ostalpen_einzugsgebiete.geojson

Usage:
    python tools/prepare_einzugsgebiete.py [--force]
"""

import argparse
import json
import sys
import zipfile
from pathlib import Path

import geopandas as gpd
import requests
from shapely.geometry import box, mapping

# ─── project imports ──────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent.parent))
from deck import DATA_DIR_OSM

# ─── constants ────────────────────────────────────────────────────────────────

# HydroBASINS Europe (standard, all levels) — direct download link
HYDROBASINS_URL = (
    "https://data.hydrosheds.org/file/HydroBASINS/standard/"
    "hybas_eu_lev01-12_v1c.zip"
)

# We use Level 8 — fine enough to distinguish individual river systems in the Alps
HYDROBASINS_LEVEL = 8
HYDROBASINS_SHAPEFILE = "hybas_eu_lev08_v1c.shp"

# Ostalpen bounding box (matches regions/ostalpen.py)
BBOX_WEST = 9.05
BBOX_EAST = 16.82
BBOX_SOUTH = 45.2
BBOX_NORTH = 48.62

OUTPUT_FILE = DATA_DIR_OSM / "ostalpen_einzugsgebiete.geojson"

# ─── River system mapping ────────────────────────────────────────────────────
# HydroBASINS Level 8 Pfafstetter IDs for the major river systems in
# the Eastern Alps.  Each basin at Level 8 has a PFAF_ID that encodes
# its position in the drainage hierarchy.  We map them to our basin IDs
# using MAIN_BAS (for non-Danube rivers) and PFAF prefix (for Danube
# tributaries), then dissolve all sub-basins that drain into the same
# major river.  The assignment is done via spatial intersection with
# known river mouth / confluence points, using the MAIN_BAS (main basin
# ID) and NEXT_DOWN (downstream basin) attributes from HydroBASINS.

# Major rivers and representative coordinates (lon, lat) within
# their alpine catchment, used for initial assignment.  Multiple
# points per system improve matching accuracy.
RIVER_SYSTEMS = {
    "E01": {
        "name": "Rhein",
        "rivers": ["Rhein", "Ill"],
        "sample_points": [
            (9.6, 47.2), (9.8, 47.1), (9.5, 47.3),  # Vorarlberg Rheintal
            (9.75, 47.05), (9.85, 47.25), (9.4, 47.15),  # Ill / Montafon
            (9.55, 47.4), (9.65, 47.35),  # Bregenzerwald
        ],
    },
    "E02": {
        "name": "Inn",
        "rivers": ["Inn"],
        "sample_points": [
            (10.3, 46.9), (10.5, 47.0), (10.7, 47.1),  # Oberinntal
            (11.0, 47.25), (11.4, 47.26), (11.8, 47.3),  # Inntal Innsbruck-Schwaz
            (12.0, 47.4), (12.2, 47.5), (12.4, 47.45),  # Unterinntal
            (10.8, 47.0), (10.9, 46.95),  # Stubaital / Ötztal
            (11.5, 47.15), (11.3, 47.1),  # Wipptal
            (10.4, 47.3), (11.1, 47.35),  # Inntal extra
        ],
    },
    "E03": {
        "name": "Salzach / Saalach",
        "rivers": ["Salzach", "Saalach"],
        "sample_points": [
            (12.7, 47.2), (12.8, 47.3), (12.9, 47.35),  # Oberpinzgau
            (13.0, 47.4), (13.05, 47.5), (13.0, 47.7),  # Salzachtal Richtung Salzburg
            (13.05, 47.8), (12.95, 47.6),  # Salzburg Stadt
            (12.8, 47.5), (12.6, 47.15),  # Saalach / Glemmtal
            (12.75, 47.45), (13.1, 47.3),  # Gasteinertal
        ],
    },
    "E04": {
        "name": "Traun",
        "rivers": ["Traun", "Ager"],
        "sample_points": [
            (13.6, 47.7), (13.7, 47.7), (13.8, 47.8),  # Traunsee
            (13.9, 47.85), (13.65, 47.75),  # Gmunden / Bad Ischl
            (13.5, 47.55), (13.6, 47.6),  # Gosautal
            (13.8, 47.65), (14.0, 47.9),  # Traun-Unterlauf
        ],
    },
    "E05": {
        "name": "Enns",
        "rivers": ["Enns"],
        "sample_points": [
            (13.4, 47.4), (13.5, 47.45), (13.6, 47.5),  # Oberes Ennstal
            (13.8, 47.5), (14.0, 47.5), (14.2, 47.55),  # Mittleres Ennstal
            (14.4, 47.6), (14.5, 47.6),  # Unteres Ennstal/Gesäuse
            (13.7, 47.45), (14.3, 47.55),  # extra
        ],
    },
    "E06": {
        "name": "Mur",
        "rivers": ["Mur"],
        "sample_points": [
            (13.5, 47.1), (13.6, 47.15), (13.8, 47.2),  # Oberes Murtal / Lungau
            (14.0, 47.15), (14.3, 47.1), (14.5, 47.1),  # Mittleres Murtal
            (15.0, 47.0), (15.3, 47.05), (15.4, 47.07),  # Graz
            (15.5, 46.9), (15.0, 46.85),  # Mur Süd
            (14.7, 47.1), (15.2, 47.0),  # extra
        ],
    },
    "E07": {
        "name": "Drau",
        "rivers": ["Drau", "Gail"],
        "sample_points": [
            (12.3, 46.75), (12.5, 46.75), (12.8, 46.7),  # Oberes Drautal
            (13.0, 46.65), (13.3, 46.63), (13.5, 46.62),  # Drautal Lienz-Villach
            (13.8, 46.6), (14.0, 46.6), (14.3, 46.62),  # Villach-Klagenfurt
            (14.5, 46.65), (14.8, 46.6),  # Klagenfurt Becken
            (13.2, 46.58), (13.6, 46.55),  # Gailtal
            (12.7, 46.8), (13.0, 46.7),  # Iseltal / Mölltal
        ],
    },
    "E08": {
        "name": "Etsch (Adige)",
        "rivers": ["Etsch", "Adige", "Eisack", "Isarco"],
        "sample_points": [
            (10.6, 46.7), (10.8, 46.65), (10.5, 46.6),  # Vinschgau
            (11.0, 46.5), (11.1, 46.6), (11.2, 46.4),  # Bozen
            (11.3, 46.7), (11.4, 46.8), (11.5, 46.9),  # Eisacktal / Brenner
            (11.0, 46.3), (11.1, 46.15),  # Etsch Süd Richtung Trient
            (10.9, 46.45), (11.3, 46.5),  # extra
        ],
    },
    "E09": {
        "name": "Brenta / Sarca",
        "rivers": ["Brenta", "Sarca"],
        "sample_points": [
            (10.85, 45.85), (10.9, 45.9), (10.95, 46.0),  # Gardasee Norden / Sarca
            (11.0, 46.05), (11.1, 46.1),  # Sarca Oberlauf
            (11.5, 46.0), (11.6, 45.9), (11.7, 45.85),  # Brenta Tal
            (11.4, 45.95), (11.3, 46.0),  # extra
        ],
    },
    "E10": {
        "name": "Tagliamento / Piave",
        "rivers": ["Tagliamento", "Piave"],
        "sample_points": [
            (12.5, 46.4), (12.6, 46.35), (12.7, 46.3),  # Piave Oberlauf (Cortina)
            (12.3, 46.5), (12.4, 46.45),  # Pustertal Ost → Piave
            (12.8, 46.25), (12.5, 46.2),  # Piave Mitte
            (13.0, 46.4), (13.1, 46.35), (13.2, 46.3),  # Tagliamento
            (13.0, 46.25), (12.9, 46.2),  # Tagliamento Mitte
        ],
    },
}


def download_hydrobasins(cache_dir: Path) -> Path:
    """Download HydroBASINS Europe zip if not cached; return shapefile path."""
    zip_path = cache_dir / "hybas_eu_lev01-12_v1c.zip"
    shp_path = cache_dir / HYDROBASINS_SHAPEFILE

    if shp_path.exists():
        print(f"[HydroBASINS] Using cached: {shp_path}")
        return shp_path

    if not zip_path.exists():
        print(f"[HydroBASINS] Downloading Level 1-12 Europe (~100 MB)...")
        print(f"  URL: {HYDROBASINS_URL}")
        resp = requests.get(HYDROBASINS_URL, stream=True, timeout=300)
        resp.raise_for_status()

        total = int(resp.headers.get("content-length", 0))
        downloaded = 0
        with open(zip_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)
                downloaded += len(chunk)
                if total:
                    pct = downloaded / total * 100
                    print(f"\r  {downloaded / 1e6:.1f} / {total / 1e6:.1f} MB "
                          f"({pct:.0f}%)", end="", flush=True)
        print()

    print(f"[HydroBASINS] Extracting Level {HYDROBASINS_LEVEL}...")
    with zipfile.ZipFile(zip_path) as zf:
        # Extract only the files for our level
        prefix = HYDROBASINS_SHAPEFILE.replace(".shp", "")
        for name in zf.namelist():
            if name.startswith(prefix):
                zf.extract(name, cache_dir)

    if not shp_path.exists():
        raise FileNotFoundError(
            f"Expected {shp_path} after extraction. "
            f"Available: {[n for n in (cache_dir).iterdir()]}"
        )
    return shp_path


def clip_to_bbox(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Clip GeoDataFrame to Ostalpen bounding box."""
    bbox_poly = box(BBOX_WEST, BBOX_SOUTH, BBOX_EAST, BBOX_NORTH)
    clipped = gdf.clip(bbox_poly)
    # Keep only polygons with meaningful area after clipping
    clipped = clipped[~clipped.geometry.is_empty]
    return clipped


def assign_basin_ids(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Assign each sub-basin polygon to a major river system (E01–E10).

    Uses a two-phase strategy for maximum accuracy:
    1. MAIN_BAS attribute for non-Danube river systems (Rhein, Etsch, Brenta, etc.)
    2. PFAF_ID hierarchical coding to split the Danube system into individual rivers
    3. Sample point + network tracing fallback for ambiguous basins
    4. Nearest centroid for anything remaining
    """
    from shapely.geometry import Point

    gdf = gdf.copy()
    gdf["basin_id"] = ""

    # ── Phase 1: MAIN_BAS for non-Danube systems ──
    # Each non-Danube river has a unique MAIN_BAS in HydroBASINS
    MAIN_BAS_DANUBE = 2080008490

    # Rhein system
    gdf.loc[gdf["MAIN_BAS"] == 2080023010, "basin_id"] = "E01"

    # Etsch / Adige system
    gdf.loc[gdf["MAIN_BAS"] == 2080012980, "basin_id"] = "E08"

    # Brenta / Sarca system
    gdf.loc[gdf["MAIN_BAS"] == 2080013010, "basin_id"] = "E09"

    # Tagliamento / Piave system (multiple small outlet basins)
    adriatic_main_bas = {
        2080012800,  # Tagliamento
        2080012870,  # Piave
        2080012960,  # Livenza
        2080012690,  # Isonzo / Soča
        2080024170,  # Natisone
    }
    for mb in adriatic_main_bas:
        gdf.loc[(gdf["MAIN_BAS"] == mb) & (gdf["basin_id"] == ""), "basin_id"] = "E10"

    # Small coastal basins along the Adriatic (assign to nearest major system later)
    # These typically have MAIN_BAS == HYBAS_ID (terminal basins)

    assigned_phase1 = (gdf["basin_id"] != "").sum()
    print(f"  Phase 1 (MAIN_BAS): {assigned_phase1} / {len(gdf)} assigned")

    # ── Phase 2: PFAF_ID prefix for Danube sub-rivers ──
    # Within the Danube basin, the Pfafstetter coding hierarchy distinguishes
    # major tributaries.  Mapping determined by checking key locations:
    #   Inn: 227980{7-9}x  Salzach: 2279804x  Traun: 2279708x
    #   Enns: 2279706x     Mur: 22780{4-5}x   Drau: 22780{6-9}x
    danube_mask = (gdf["MAIN_BAS"] == MAIN_BAS_DANUBE) & (gdf["basin_id"] == "")
    danube_pfaf = gdf.loc[danube_mask, "PFAF_ID"].astype(str)

    # Inn: PFAF 227980{5,6,7,8,9}xxx — upper/central Inn (Note: 2279804=Salzach)
    inn_mask = danube_mask & danube_pfaf.str.match(r"^22798(?:0[5-9]|[1-9]).*$")
    gdf.loc[inn_mask, "basin_id"] = "E02"

    # Salzach / Saalach: PFAF 2279804xxx
    salzach_mask = danube_mask & danube_pfaf.str.startswith("2279804")
    gdf.loc[salzach_mask, "basin_id"] = "E03"

    # Traun: PFAF 2279708xxx and 2279709xxx
    traun_mask = danube_mask & (danube_pfaf.str.startswith("2279708") |
                                danube_pfaf.str.startswith("2279709") |
                                danube_pfaf.str.startswith("2279700"))
    gdf.loc[traun_mask, "basin_id"] = "E04"

    # Enns: PFAF 2279706xxx and 2279707xxx
    enns_mask = danube_mask & (danube_pfaf.str.startswith("2279706") |
                               danube_pfaf.str.startswith("2279707"))
    gdf.loc[enns_mask, "basin_id"] = "E05"

    # Mur: PFAF 22780{3,4,5}xxx
    mur_mask = danube_mask & danube_pfaf.str.match(r"^22780[345].*$")
    gdf.loc[mur_mask, "basin_id"] = "E06"

    # Drau (incl. Gail): PFAF 22780{6,7,8,9}xxx
    drau_mask = danube_mask & danube_pfaf.str.match(r"^22780[6789].*$")
    gdf.loc[drau_mask, "basin_id"] = "E07"

    assigned_phase2 = (gdf["basin_id"] != "").sum()
    print(f"  Phase 2 (PFAF prefix): {assigned_phase2} / {len(gdf)} assigned")

    # ── Phase 3: sample point containment for remaining Danube basins ──
    # Some PFAF ranges don't cleanly map — use sample points to assign
    remaining = gdf["basin_id"] == ""
    if remaining.any():
        for basin_id, info in RIVER_SYSTEMS.items():
            for lon, lat in info["sample_points"]:
                pt = Point(lon, lat)
                mask = gdf.geometry.contains(pt) & (gdf["basin_id"] == "")
                gdf.loc[mask, "basin_id"] = basin_id

        assigned_phase3 = (gdf["basin_id"] != "").sum()
        print(f"  Phase 3 (sample points): {assigned_phase3} / {len(gdf)} assigned")

    # ── Phase 4: network tracing (both directions) ──
    if "NEXT_DOWN" in gdf.columns and "HYBAS_ID" in gdf.columns:
        id_to_idx = {row["HYBAS_ID"]: idx for idx, row in gdf.iterrows()}
        upstream_map: dict = {}
        for idx, row in gdf.iterrows():
            nd = row["NEXT_DOWN"]
            if nd in id_to_idx:
                upstream_map.setdefault(nd, []).append(idx)

        changed = True
        iterations = 0
        while changed and iterations < 100:
            changed = False
            iterations += 1
            for idx, row in gdf[gdf["basin_id"] == ""].iterrows():
                next_down = row["NEXT_DOWN"]
                if next_down in id_to_idx:
                    down_basin = gdf.loc[id_to_idx[next_down], "basin_id"]
                    if down_basin != "":
                        gdf.loc[idx, "basin_id"] = down_basin
                        changed = True
                        continue
            for idx, row in gdf[gdf["basin_id"] != ""].iterrows():
                hid = row["HYBAS_ID"]
                for up_idx in upstream_map.get(hid, []):
                    if gdf.loc[up_idx, "basin_id"] == "":
                        gdf.loc[up_idx, "basin_id"] = row["basin_id"]
                        changed = True
        assigned_phase4 = (gdf["basin_id"] != "").sum()
        print(f"  Phase 4 (topology, {iterations} iters): "
              f"{assigned_phase4} / {len(gdf)} assigned")

    # ── Phase 5: nearest centroid for any stragglers ──
    unassigned = gdf[gdf["basin_id"] == ""]
    if len(unassigned) > 0:
        assigned_proj = gdf[gdf["basin_id"] != ""].to_crs(epsg=3035)
        print(f"  Phase 5 (nearest centroid): {len(unassigned)} remaining")

        for idx in unassigned.index:
            centroid = gpd.GeoSeries(
                [gdf.loc[idx, "geometry"].centroid], crs=gdf.crs
            ).to_crs(epsg=3035).iloc[0]
            distances = assigned_proj.geometry.centroid.distance(centroid)
            nearest_idx = distances.idxmin()
            gdf.loc[idx, "basin_id"] = gdf.loc[nearest_idx, "basin_id"]

    return gdf


def dissolve_and_export(gdf: gpd.GeoDataFrame, output: Path) -> None:
    """Dissolve sub-basins by basin_id and export as GeoJSON."""
    from shapely.validation import make_valid

    print(f"[Dissolve] Merging {len(gdf)} sub-basins into river systems...")

    dissolved = gdf.dissolve(by="basin_id").reset_index()

    # Build clean GeoJSON FeatureCollection
    features = []
    for _, row in dissolved.iterrows():
        basin_id = row["basin_id"]
        info = RIVER_SYSTEMS.get(basin_id, {})
        geom = make_valid(row.geometry)

        feature = {
            "type": "Feature",
            "properties": {
                "basin_id": basin_id,
                "name": info.get("name", basin_id),
            },
            "geometry": mapping(geom),
        }
        features.append(feature)

    geojson = {
        "type": "FeatureCollection",
        "features": sorted(features, key=lambda f: f["properties"]["basin_id"]),
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)

    print(f"[Done] {len(features)} basins → {output}")
    for feat in geojson["features"]:
        p = feat["properties"]
        print(f"  {p['basin_id']}: {p['name']}")


def main():
    parser = argparse.ArgumentParser(
        description="Prepare Ostalpen drainage basin polygons from HydroBASINS"
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Overwrite existing output file"
    )
    args = parser.parse_args()

    if OUTPUT_FILE.exists() and not args.force:
        print(f"[Skip] Already exists: {OUTPUT_FILE}")
        print(f"  Use --force to regenerate.")
        return

    # Use data/dem as cache for downloaded HydroBASINS files
    cache_dir = Path(__file__).parent.parent / "data" / "hydrobasins"
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Download / extract
    shp_path = download_hydrobasins(cache_dir)

    # Step 2: Load full dataset (need intact NEXT_DOWN network for tracing)
    print(f"[Load] Reading {shp_path}...")
    gdf_full = gpd.read_file(shp_path)
    print(f"  {len(gdf_full)} sub-basins in Europe")

    # Step 3: Assign to river systems on the FULL network (unbroken topology)
    # Only sample points within the bbox will match, but NEXT_DOWN tracing
    # works correctly because the full network is intact.
    print("[Assign] Mapping sub-basins to river systems (full network)...")
    gdf_full = assign_basin_ids(gdf_full)

    # Step 4: Clip to bbox AFTER assignment
    gdf = clip_to_bbox(gdf_full)
    print(f"  {len(gdf)} sub-basins after clipping to Ostalpen bbox")

    if len(gdf) == 0:
        print("[ERROR] No basins found in bbox. Check coordinates / shapefile.")
        sys.exit(1)

    # Report
    for basin_id in sorted(RIVER_SYSTEMS.keys()):
        count = (gdf["basin_id"] == basin_id).sum()
        name = RIVER_SYSTEMS[basin_id]["name"]
        print(f"  {basin_id} {name}: {count} sub-basins")

    # Step 5: Dissolve and export
    dissolve_and_export(gdf, OUTPUT_FILE)


if __name__ == "__main__":
    main()
