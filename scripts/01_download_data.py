"""
01_download_data.py — Download all required geodata
=====================================================
Downloads AVE polygons, OSM rivers/lakes/borders, and DEM tiles.
Parameterised by ``--deck`` so the same script works for both decks.

Usage:
    python scripts/01_download_data.py --region ostalpen
    python scripts/01_download_data.py --region westalpen
    python scripts/01_download_data.py --region ostalpen --system ave84 --skip-dem
"""

import argparse
import json
import sys
import time
import zipfile
from pathlib import Path

import requests
from tqdm import tqdm

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
import deck as D
from deck import Deck


# ═══════════════════════════════════════════════════════════════════════════════
# 1.  DOWNLOAD MOUNTAIN GROUP POLYGONS
# ═══════════════════════════════════════════════════════════════════════════════

def _overpass_query(query):
    """Run an Overpass query with retries. Returns parsed JSON."""
    for attempt in range(3):
        try:
            print(f"[OSM] Attempt {attempt + 1}/3 …")
            resp = requests.post(D.OVERPASS_API_URL,
                                 data={"data": query},
                                 timeout=D.OVERPASS_TIMEOUT + 60)
            resp.raise_for_status()
            return resp.json()
        except (requests.exceptions.Timeout, requests.exceptions.HTTPError) as e:
            if attempt < 2:
                print(f"[OSM]   failed: {e}. Retrying …")
                time.sleep(10)
            else:
                raise


def download_polygons(d: Deck):
    """Query Overpass for OSM tag relations + fallback by relation ID."""
    if d.osm_geojson.exists():
        print(f"[OSM] Already exists: {d.osm_geojson}")
        return

    osm_tag = d.osm_tag
    print(f"[OSM] Downloading polygons for {d.title} (tag: {osm_tag}) …")

    # ── Step 1: Query for tagged relations ───────────────────────────────────
    query = (
        f"[out:json][timeout:{D.OVERPASS_TIMEOUT}];\n"
        f"(\n"
        f"  relation[\"{osm_tag}\"]"
        f"({d.bbox_south},{d.bbox_west},{d.bbox_north},{d.bbox_east});\n"
        f");\n"
        f"out body;\n>;\nout skel qt;\n"
    )

    osm_data = _overpass_query(query)
    print(f"[OSM] Received {len(osm_data['elements'])} elements")

    geojson = _osm_json_to_geojson(osm_data, osm_tag)

    # Keep only the groups defined in the deck
    valid = d.valid_osm_refs
    kept, skipped = [], []
    for feat in geojson["features"]:
        ref = feat["properties"].get(osm_tag, "")
        if ref in valid:
            kept.append(feat)
        else:
            skipped.append(ref)

    found_refs = {f["properties"][osm_tag] for f in kept}
    print(f"[OSM] Found {len(kept)} groups via {osm_tag}")

    # ── Step 2: Fetch missing groups by relation ID (fallback) ───────────────
    missing_refs = valid - found_refs
    fallback = d.osm_fallback_ids
    fetchable = {ref: fallback[ref] for ref in missing_refs if ref in fallback}

    if fetchable:
        print(f"[OSM] Fetching {len(fetchable)} groups by relation ID …")
        rel_ids = list(fetchable.values())
        id_union = "".join(f"  relation({rid});\n" for rid in rel_ids)
        fb_query = (
            f"[out:json][timeout:{D.OVERPASS_TIMEOUT}];\n"
            f"(\n{id_union});\n"
            f"out body;\n>;\nout skel qt;\n"
        )

        fb_data = _overpass_query(fb_query)
        print(f"[OSM] Received {len(fb_data['elements'])} fallback elements")

        # Build ref→relation_id reverse lookup
        relid_to_ref = {rid: ref for ref, rid in fetchable.items()}

        fb_geojson = _osm_json_to_geojson_by_id(fb_data, relid_to_ref, osm_tag)
        kept.extend(fb_geojson)
        found_refs.update(f["properties"][osm_tag] for f in fb_geojson)
        print(f"[OSM] Added {len(fb_geojson)} fallback groups")

    geojson["features"] = kept
    print(f"[OSM] Total: {len(kept)} groups (expected {len(d.groups)})")

    still_missing = valid - found_refs
    if still_missing:
        print(f"[OSM] WARNING — still missing: {sorted(still_missing)}")
        for ref in sorted(still_missing):
            g = d.group_by_osm_ref(ref)
            print(f"       {ref} = {g.name}")

    d.osm_geojson.parent.mkdir(parents=True, exist_ok=True)
    with open(d.osm_geojson, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)
    print(f"[OSM] Saved → {d.osm_geojson}")


# ─── OSM → GeoJSON conversion ────────────────────────────────────────────────

def _osm_json_to_geojson(osm_data, osm_tag="ref:aveo"):
    elements = osm_data["elements"]
    nodes, ways, relations = {}, {}, []
    for el in elements:
        if el["type"] == "node":
            nodes[el["id"]] = (el["lon"], el["lat"])
        elif el["type"] == "way":
            ways[el["id"]] = el.get("nodes", [])
        elif el["type"] == "relation":
            relations.append(el)

    features = []
    for rel in relations:
        tags = rel.get("tags", {})
        if osm_tag not in tags:
            continue
        outer_ways, inner_ways = [], []
        for m in rel.get("members", []):
            if m["type"] == "way" and m["ref"] in ways:
                (inner_ways if m.get("role") == "inner" else outer_ways).append(m["ref"])

        outer_rings = _assemble_rings(outer_ways, ways, nodes)
        inner_rings = _assemble_rings(inner_ways, ways, nodes)
        if not outer_rings:
            print(f"  [OSM] Could not build polygon for {osm_tag}={tags.get(osm_tag)}")
            continue

        if len(outer_rings) == 1:
            geometry = {"type": "Polygon", "coordinates": [outer_rings[0]] + inner_rings}
        else:
            polys = [[r] for r in outer_rings]
            if inner_rings:
                polys[0].extend(inner_rings)
            geometry = {"type": "MultiPolygon", "coordinates": polys}

        features.append({"type": "Feature", "properties": tags,
                         "geometry": geometry, "id": rel["id"]})
    return {"type": "FeatureCollection", "features": features}


def _osm_json_to_geojson_by_id(osm_data, relid_to_ref, osm_tag="ref:aveo"):
    """Convert OSM JSON to GeoJSON features, assigning the OSM tag from a
    relation-ID → ref mapping (for groups that lack the tag)."""
    elements = osm_data["elements"]
    nodes, ways, relations = {}, {}, []
    for el in elements:
        if el["type"] == "node":
            nodes[el["id"]] = (el["lon"], el["lat"])
        elif el["type"] == "way":
            ways[el["id"]] = el.get("nodes", [])
        elif el["type"] == "relation":
            relations.append(el)

    features = []
    for rel in relations:
        rid = rel["id"]
        ref = relid_to_ref.get(rid)
        if ref is None:
            continue
        tags = dict(rel.get("tags", {}))
        tags[osm_tag] = ref  # inject the missing tag

        outer_ways, inner_ways = [], []
        for m in rel.get("members", []):
            if m["type"] == "way" and m["ref"] in ways:
                (inner_ways if m.get("role") == "inner" else outer_ways).append(m["ref"])

        outer_rings = _assemble_rings(outer_ways, ways, nodes)
        inner_rings = _assemble_rings(inner_ways, ways, nodes)
        if not outer_rings:
            print(f"  [OSM] Could not build polygon for {ref} (relation {rid})")
            continue

        if len(outer_rings) == 1:
            geometry = {"type": "Polygon", "coordinates": [outer_rings[0]] + inner_rings}
        else:
            polys = [[r] for r in outer_rings]
            if inner_rings:
                polys[0].extend(inner_rings)
            geometry = {"type": "MultiPolygon", "coordinates": polys}

        features.append({"type": "Feature", "properties": tags,
                         "geometry": geometry, "id": rid})
        print(f"  [OSM] Built polygon for ref {ref}: {tags.get('name', tags.get('name:de', '?'))}")
    return features


def _assemble_rings(way_ids, ways, nodes):
    if not way_ids:
        return []
    segments = []
    for wid in way_ids:
        coords = [nodes[n] for n in ways.get(wid, []) if n in nodes]
        if coords:
            segments.append(coords)
    if not segments:
        return []

    rings, used = [], [False] * len(segments)
    while True:
        start = next((i for i, u in enumerate(used) if not u), None)
        if start is None:
            break
        ring = list(segments[start])
        used[start] = True
        changed = True
        while changed:
            changed = False
            for i, seg in enumerate(segments):
                if used[i] or not seg:
                    continue
                re, rs = ring[-1], ring[0]
                se, ss = seg[-1], seg[0]
                if _close(re, ss):
                    ring.extend(seg[1:]); used[i] = changed = True
                elif _close(re, se):
                    ring.extend(reversed(seg[:-1])); used[i] = changed = True
                elif _close(rs, se):
                    ring = seg[:-1] + ring; used[i] = changed = True
                elif _close(rs, ss):
                    ring = list(reversed(seg[1:])) + ring; used[i] = changed = True
        if ring and not _close(ring[0], ring[-1]):
            ring.append(ring[0])
        if len(ring) >= 4:
            rings.append([list(c) for c in ring])
    return rings


def _close(a, b, tol=1e-7):
    return abs(a[0] - b[0]) < tol and abs(a[1] - b[1]) < tol


def _assemble_ring_coords(segments):
    """Assemble raw coordinate segments into closed polygon rings.

    Like ``_assemble_rings`` but works directly with coordinate lists
    (used for Overpass ``out geom`` output where geometry is inline).
    """
    if not segments:
        return []

    rings, used = [], [False] * len(segments)
    while True:
        start = next((i for i, u in enumerate(used) if not u), None)
        if start is None:
            break
        ring = list(segments[start])
        used[start] = True
        changed = True
        while changed:
            changed = False
            for i, seg in enumerate(segments):
                if used[i] or len(seg) < 2:
                    continue
                if _close(ring[-1], seg[0]):
                    ring.extend(seg[1:]); used[i] = changed = True
                elif _close(ring[-1], seg[-1]):
                    ring.extend(list(reversed(seg))[1:]); used[i] = changed = True
                elif _close(ring[0], seg[-1]):
                    ring = seg[:-1] + ring; used[i] = changed = True
                elif _close(ring[0], seg[0]):
                    ring = list(reversed(seg))[:-1] + ring; used[i] = changed = True
        if ring and not _close(ring[0], ring[-1]):
            ring.append(ring[0])
        if len(ring) >= 4:
            rings.append(ring)
    return rings


# ═══════════════════════════════════════════════════════════════════════════════
# 2.  OSM COUNTRY BORDERS
# ═══════════════════════════════════════════════════════════════════════════════

def download_osm_borders(d: Deck):
    """Download admin_level=2 boundary ways from OSM (country borders)."""
    out = d.osm_borders_geojson
    if out.exists():
        print(f"[OSM-BORDERS] Already exists: {out}")
        return

    print(f"[OSM-BORDERS] Downloading country borders for {d.title} ...")

    query = (
        f"[out:json][timeout:{D.OVERPASS_TIMEOUT}];\n"
        f"(\n"
        f'  way["boundary"="administrative"]["admin_level"="2"]'
        f"({d.bbox_south},{d.bbox_west},{d.bbox_north},{d.bbox_east});\n"
        f");\n"
        f"out geom;\n"
    )

    for attempt in range(3):
        try:
            print(f"  Attempt {attempt + 1}/3 ...")
            resp = requests.post(D.OVERPASS_API_URL,
                                 data={"data": query},
                                 timeout=D.OVERPASS_TIMEOUT + 30)
            resp.raise_for_status()
            data = resp.json()
            break
        except Exception as e:
            print(f"  failed: {e}")
            if attempt == 2:
                print("[OSM-BORDERS] Giving up.")
                return
            time.sleep(10)

    from shapely.geometry import LineString
    features = []
    for el in data.get("elements", []):
        if el.get("type") == "way" and "geometry" in el:
            coords = [(pt["lon"], pt["lat"]) for pt in el["geometry"]]
            if len(coords) >= 2:
                features.append({
                    "type": "Feature",
                    "geometry": LineString(coords).__geo_interface__,
                    "properties": {
                        "name": el.get("tags", {}).get("name", ""),
                    },
                })

    if features:
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump({"type": "FeatureCollection", "features": features}, f)
        print(f"[OSM-BORDERS] Saved {len(features)} border segments -> {out}")
    else:
        print("[OSM-BORDERS] No border segments found.")


# ═══════════════════════════════════════════════════════════════════════════════
# 3.  DEM
# ═══════════════════════════════════════════════════════════════════════════════

def download_dem(d: Deck):
    if d.dem_tif.exists():
        print(f"[DEM] Already exists: {d.dem_tif}")
        return

    print(f"[DEM] Downloading SRTM DEM for {d.title} …")

    try:
        import elevation
        d.dem_tif.parent.mkdir(parents=True, exist_ok=True)
        elevation.clip(
            bounds=(d.dem_bbox_west, d.dem_bbox_south,
                    d.dem_bbox_east, d.dem_bbox_north),
            output=str(d.dem_tif), product="SRTM3",
        )
        return
    except ImportError:
        pass

    # Fallback: CGIAR-CSI 5×5° tiles
    _download_dem_cgiar(d)


def _download_dem_cgiar(d: Deck):
    import math
    tile_dir = D.DATA_DIR_DEM / "tiles"
    tile_dir.mkdir(parents=True, exist_ok=True)
    d.dem_tif.parent.mkdir(parents=True, exist_ok=True)

    base_url = "https://srtm.csi.cgiar.org/wp-content/uploads/files/srtm_5x5/TIFF/"
    tiles = []
    for lon_t in range(int((d.dem_bbox_west + 180) / 5) + 1,
                       int((d.dem_bbox_east + 180) / 5) + 2):
        for lat_t in range(int((60 - d.dem_bbox_north) / 5) + 1,
                           int((60 - d.dem_bbox_south) / 5) + 2):
            tiles.append(f"srtm_{lon_t:02d}_{lat_t:02d}")

    print(f"[DEM] Tiles needed: {tiles}")
    downloaded = []
    for tn in tiles:
        tif = tile_dir / f"{tn}.tif"
        if tif.exists():
            print(f"[DEM]   Have: {tn}.tif")
            downloaded.append(tif)
            continue
        zp = tile_dir / f"{tn}.zip"
        try:
            _download_file(f"{base_url}{tn}.zip", zp)
            with zipfile.ZipFile(zp) as zf:
                names = [n for n in zf.namelist() if n.endswith(".tif")]
                if names:
                    with open(tif, "wb") as out:
                        out.write(zf.read(names[0]))
                    downloaded.append(tif)
            zp.unlink(missing_ok=True)
        except Exception as e:
            print(f"[DEM]   Failed {tn}: {e}")
            zp.unlink(missing_ok=True)

    if downloaded:
        _merge_dem(downloaded, d.dem_tif)
    else:
        print("[DEM] ERROR: no tiles downloaded.")


def _merge_dem(tile_paths, output):
    import rasterio
    from rasterio.merge import merge

    datasets = [rasterio.open(str(p)) for p in tile_paths]
    mosaic, out_transform = merge(datasets)
    meta = datasets[0].meta.copy()
    meta.update(driver="GTiff", height=mosaic.shape[1], width=mosaic.shape[2],
                transform=out_transform, compress="lzw")
    for ds in datasets:
        ds.close()
    with rasterio.open(str(output), "w", **meta) as dest:
        dest.write(mosaic)
    print(f"[DEM] Merged → {output}  shape={mosaic.shape}")


# ═══════════════════════════════════════════════════════════════════════════════
# 4.  OSM RIVERS
# ═══════════════════════════════════════════════════════════════════════════════

def download_osm_rivers(d: Deck):
    out = d.osm_rivers_geojson
    if out.exists():
        print(f"[OSM-RIVERS] Already exists: {out}")
        return

    print(f"[OSM-RIVERS] Downloading rivers for {d.title} …")

    query = (
        f"[out:json][timeout:{D.OVERPASS_TIMEOUT}];\n"
        f"(\n"
        f'  way["waterway"="river"]'
        f"({d.bbox_south},{d.bbox_west},{d.bbox_north},{d.bbox_east});\n"
        f'  relation["waterway"="river"]'
        f"({d.bbox_south},{d.bbox_west},{d.bbox_north},{d.bbox_east});\n"
        f");\n"
        f"out geom;\n"
    )

    for attempt in range(3):
        try:
            resp = requests.post(D.OVERPASS_API_URL,
                                 data={"data": query},
                                 timeout=D.OVERPASS_TIMEOUT + 30)
            resp.raise_for_status()
            data = resp.json()
            break
        except Exception as e:
            print(f"  Attempt {attempt + 1} failed: {e}")
            if attempt == 2:
                print("[OSM-RIVERS] Giving up.")
                return
            time.sleep(10)

    from shapely.geometry import LineString
    features = []
    for el in data.get("elements", []):
        if el.get("type") == "way" and "geometry" in el:
            coords = [(pt["lon"], pt["lat"]) for pt in el["geometry"]]
            if len(coords) >= 2:
                features.append({
                    "type": "Feature",
                    "geometry": LineString(coords).__geo_interface__,
                    "properties": {"name": el.get("tags", {}).get("name", "")},
                })
        elif el.get("type") == "relation":
            # Extract way members from river relations
            for member in el.get("members", []):
                if member.get("type") == "way" and "geometry" in member:
                    coords = [(pt["lon"], pt["lat"]) for pt in member["geometry"]]
                    if len(coords) >= 2:
                        features.append({
                            "type": "Feature",
                            "geometry": LineString(coords).__geo_interface__,
                            "properties": {"name": el.get("tags", {}).get("name", "")},
                        })

    if features:
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump({"type": "FeatureCollection", "features": features}, f)
        print(f"[OSM-RIVERS] Saved {len(features)} segments → {out}")
    else:
        print("[OSM-RIVERS] No rivers found.")


# ═══════════════════════════════════════════════════════════════════════════════
# 5.  OSM LAKES
# ═══════════════════════════════════════════════════════════════════════════════

def download_osm_lakes(d: Deck):
    """Download lake and reservoir polygons from OSM via Overpass."""
    out = d.osm_lakes_geojson
    if out.exists():
        print(f"[OSM-LAKES] Already exists: {out}")
        return

    print(f"[OSM-LAKES] Downloading lakes for {d.title} …")

    query = (
        f"[out:json][timeout:{D.OVERPASS_TIMEOUT}];\n"
        f"(\n"
        f'  way["natural"="water"]["water"~"^(lake|reservoir)$"]'
        f"({d.bbox_south},{d.bbox_west},{d.bbox_north},{d.bbox_east});\n"
        f'  relation["natural"="water"]["water"~"^(lake|reservoir)$"]'
        f"({d.bbox_south},{d.bbox_west},{d.bbox_north},{d.bbox_east});\n"
        f");\n"
        f"out geom;\n"
    )

    for attempt in range(3):
        try:
            print(f"  Attempt {attempt + 1}/3 …")
            resp = requests.post(D.OVERPASS_API_URL,
                                 data={"data": query},
                                 timeout=D.OVERPASS_TIMEOUT + 30)
            resp.raise_for_status()
            data = resp.json()
            break
        except Exception as e:
            print(f"  failed: {e}")
            if attempt == 2:
                print("[OSM-LAKES] Giving up.")
                return
            time.sleep(10)

    from shapely.geometry import Polygon, MultiPolygon
    from shapely.validation import make_valid

    features = []
    for el in data.get("elements", []):
        name = el.get("tags", {}).get("name", "")

        if el["type"] == "way" and "geometry" in el:
            coords = [(pt["lon"], pt["lat"]) for pt in el["geometry"]]
            if len(coords) >= 4:
                try:
                    poly = Polygon(coords)
                    if not poly.is_valid:
                        poly = make_valid(poly)
                    if not poly.is_empty and poly.geom_type in ("Polygon", "MultiPolygon"):
                        features.append({
                            "type": "Feature",
                            "geometry": poly.__geo_interface__,
                            "properties": {"name": name},
                        })
                except Exception:
                    pass

        elif el["type"] == "relation":
            outer_segs, inner_segs = [], []
            for member in el.get("members", []):
                if member.get("type") != "way" or "geometry" not in member:
                    continue
                coords = [(pt["lon"], pt["lat"]) for pt in member["geometry"]]
                if len(coords) < 2:
                    continue
                if member.get("role") == "inner":
                    inner_segs.append(coords)
                else:
                    outer_segs.append(coords)

            outer_rings = _assemble_ring_coords(outer_segs)
            inner_rings = _assemble_ring_coords(inner_segs)

            if not outer_rings:
                continue

            try:
                if len(outer_rings) == 1:
                    poly = Polygon(outer_rings[0], inner_rings)
                else:
                    polys = [Polygon(r) for r in outer_rings]
                    poly = MultiPolygon(
                        [(p.exterior.coords[:], []) for p in polys
                         if not p.is_empty and p.is_valid]
                    )
                if not poly.is_valid:
                    poly = make_valid(poly)
                if not poly.is_empty:
                    features.append({
                        "type": "Feature",
                        "geometry": poly.__geo_interface__,
                        "properties": {"name": name},
                    })
            except Exception:
                pass

    if features:
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump({"type": "FeatureCollection", "features": features}, f)
        print(f"[OSM-LAKES] Saved {len(features)} lakes → {out}")
    else:
        print("[OSM-LAKES] No lakes found.")


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITY
# ═══════════════════════════════════════════════════════════════════════════════

def _download_file(url, filepath, chunk_size=8192):
    resp = requests.get(url, stream=True, timeout=120)
    resp.raise_for_status()
    total = int(resp.headers.get("content-length", 0))
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "wb") as f:
        with tqdm(total=total, unit="B", unit_scale=True, desc=filepath.name) as pbar:
            for chunk in resp.iter_content(chunk_size):
                f.write(chunk)
                pbar.update(len(chunk))


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Download geodata for Anki deck")
    D.add_deck_arguments(parser)
    parser.add_argument("--skip-osm", action="store_true")
    parser.add_argument("--skip-dem", action="store_true")
    args = parser.parse_args()

    d = D.get_deck(args.region, args.system)
    print(f"=== Downloading data for: {d.title} ===\n")

    if not args.skip_osm:
        if d.classification.name == "soiusa_sz" and not d.osm_geojson.exists():
            print(f"[OSM] {d.title} polygons are not from OSM.")
            print(f"[OSM] Run: python scripts/download_soiusa_umap.py")
        else:
            download_polygons(d)
        download_osm_rivers(d)
        download_osm_lakes(d)
        download_osm_borders(d)

    if not args.skip_dem:
        download_dem(d)

    print(f"\n[DONE] All data for {d.title} downloaded.")


if __name__ == "__main__":
    main()
