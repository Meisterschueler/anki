"""
02_generate_basemap.py -- Shared map-rendering functions
========================================================
All rendering functions are parameterised by a ``Deck`` instance so they
work for both Ostalpen and Westalpen (and any future deck).

The **basemap** (hillshade + ocean + rivers + lakes) is rendered as a pure
raster with numpy / rasterio / Pillow for speed.  Vector overlays (polygons,
cities, borders, question marks) are still rendered with Matplotlib + Cartopy.

Usage (standalone test):
    python scripts/02_generate_basemap.py --region ostalpen
    python scripts/02_generate_basemap.py --region westalpen
"""

import argparse
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib.patheffects as pe
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
matplotlib.rcParams["font.family"] = "Segoe UI"
import numpy as np
from matplotlib.colors import LightSource, LinearSegmentedColormap
from shapely.geometry import box, Point
from shapely.ops import unary_union

import cartopy.crs as ccrs

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
import deck as D
from deck import Deck


# ===========================================================================
# PROJECTION / EXTENT
# ===========================================================================

def get_projection(d: Deck) -> ccrs.Projection:
    """Return the map projection for *d*.

    Uses PlateCarree (equirectangular / WGS 84) so the DEM raster can be
    displayed directly without an expensive regrid step.
    """
    return ccrs.PlateCarree()


# ===========================================================================
# HILLSHADE COLORMAP
# ===========================================================================

# Hypsometric terrain colormap (green lowlands -> brown mountains -> white peaks)
_TERRAIN_CMAP = LinearSegmentedColormap.from_list("alpen_terrain", [
    (0.00, (0.56, 0.70, 0.47)),
    (0.15, (0.67, 0.78, 0.52)),
    (0.30, (0.80, 0.78, 0.55)),
    (0.45, (0.82, 0.72, 0.50)),
    (0.60, (0.74, 0.60, 0.44)),
    (0.75, (0.65, 0.52, 0.42)),
    (0.88, (0.78, 0.75, 0.73)),
    (1.00, (0.95, 0.95, 0.97)),
], N=256)


# ===========================================================================
# RASTER BASEMAP  (numpy / rasterio / Pillow -- no matplotlib)
# ===========================================================================

def _hex_to_rgb(h: str) -> tuple:
    """'#RRGGBB' -> (R, G, B) in 0-255."""
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _corrected_figsize(d: Deck) -> tuple:
    """Return (width_inches, height_inches) with cos(mid_lat) correction.

    The image is scaled to fit inside the 8K UHD box: the longest side
    may not exceed ``BASEMAP_LONG_EDGE`` and the shortest side may not
    exceed ``BASEMAP_SHORT_EDGE``, regardless of orientation.
    """
    import math
    mid_lat = math.radians((d.bbox_south + d.bbox_north) / 2)
    lon_range = d.bbox_east - d.bbox_west
    lat_range = d.bbox_north - d.bbox_south
    # geographic aspect ratio corrected for latitude
    aspect = (lon_range * math.cos(mid_lat)) / lat_range  # w / h

    # start with the long side at max
    if aspect >= 1:                       # landscape
        w_px = D.BASEMAP_LONG_EDGE
        h_px = D.BASEMAP_LONG_EDGE / aspect
    else:                                 # portrait
        h_px = D.BASEMAP_LONG_EDGE
        w_px = D.BASEMAP_LONG_EDGE * aspect
    # shrink if the short side still exceeds the limit
    short = min(w_px, h_px)
    if short > D.BASEMAP_SHORT_EDGE:
        s = D.BASEMAP_SHORT_EDGE / short
        w_px *= s
        h_px *= s
    return w_px / D.FIGURE_DPI, h_px / D.FIGURE_DPI


def _compute_pixel_dims(d: Deck) -> tuple:
    """Return (width_px, height_px) for the basemap raster."""
    w_in, h_in = _corrected_figsize(d)
    return int(w_in * D.FIGURE_DPI), int(h_in * D.FIGURE_DPI)


def _geo_transform(d: Deck, w_px: int, h_px: int):
    """Return a rasterio-style Affine transform from extent -> pixel coords.

    Maps the bbox [west, east, south, north] to a (w_px x h_px) image.
    Returns a rasterio ``Affine`` transform object.
    """
    from rasterio.transform import from_bounds
    transform = from_bounds(
        d.bbox_west, d.bbox_south, d.bbox_east, d.bbox_north,
        w_px, h_px,
    )
    return transform


def _layer_dir(d: Deck) -> Path:
    """Return the basemap layer cache directory for *d*.

    Each deck gets its own subdirectory so that sub-region decks
    (which share ``output_images_dir`` with their parent) cache
    their own hillshade/lakes/rivers layers independently.
    """
    p = d.output_images_dir / "_basemap_layers" / d.prefix
    p.mkdir(parents=True, exist_ok=True)
    return p


# ---------------------------------------------------------------------------
# Layer cache helpers: sidecar .deps.json for content-based invalidation
# ---------------------------------------------------------------------------

def _read_deps(path: Path) -> "dict | None":
    """Read the sidecar deps file for *path*, or None if absent/corrupt."""
    import json
    dep = path.with_suffix(path.suffix + ".deps.json")
    if dep.exists():
        try:
            return json.loads(dep.read_text())
        except Exception:
            return None
    return None


def _write_deps(path: Path, deps: dict) -> None:
    """Write *deps* as a sidecar .deps.json next to *path*."""
    import json
    dep = path.with_suffix(path.suffix + ".deps.json")
    dep.write_text(json.dumps(deps))


def _is_stale(path: Path, current_deps: dict) -> bool:
    """Return True if *path* is missing or its stored deps differ from *current_deps*."""
    if not path.exists():
        return True
    return _read_deps(path) != current_deps


# ---------------------------------------------------------------------------
# Layer 1: Hillshade + ocean mask  (RGB PNG, opaque)
# ---------------------------------------------------------------------------

def _render_hillshade_layer(
    d: Deck, layer_path: Path, force: bool = False,
    *, azimuth: float = D.HILLSHADE_AZIMUTH,
) -> None:
    """Windowed DEM read -> hillshade -> ocean mask -> save RGB PNG."""
    import rasterio
    from rasterio.enums import Resampling
    from rasterio.windows import from_bounds as window_from_bounds
    from PIL import Image

    if not d.dem_tif.exists():
        print("[WARN] DEM not found. Run 01_download_data.py first.")
        return

    w_px, h_px = _compute_pixel_dims(d)
    current_deps = {
        "dem_mtime": d.dem_tif.stat().st_mtime,
        "azimuth":   round(azimuth, 4),
        "bbox":      [d.bbox_west, d.bbox_east, d.bbox_south, d.bbox_north],
        "w_px": w_px, "h_px": h_px,
    }
    if not force and not _is_stale(layer_path, current_deps):
        print(f"[HILLSHADE] cached: {layer_path.name}")
        return

    HS_BUF = 4  # extra pixels for hillshade edge gradients

    with rasterio.open(str(d.dem_tif)) as src:
        win = window_from_bounds(
            d.bbox_west, d.bbox_south, d.bbox_east, d.bbox_north,
            transform=src.transform,
        )
        sx = win.width / w_px
        sy = win.height / h_px
        buf_src_x = int(HS_BUF * sx + 1)
        buf_src_y = int(HS_BUF * sy + 1)

        row_off = max(0, int(win.row_off) - buf_src_y)
        col_off = max(0, int(win.col_off) - buf_src_x)
        row_end = min(src.height, int(win.row_off + win.height) + buf_src_y)
        col_end = min(src.width, int(win.col_off + win.width) + buf_src_x)

        read_win = rasterio.windows.Window(
            col_off, row_off, col_end - col_off, row_end - row_off,
        )
        buf_top = min(HS_BUF, int((int(win.row_off) - row_off) / sy))
        buf_left = min(HS_BUF, int((int(win.col_off) - col_off) / sx))
        read_h = h_px + buf_top + HS_BUF
        read_w = w_px + buf_left + HS_BUF

        dem = src.read(1, window=read_win,
                       out_shape=(read_h, read_w),
                       resampling=Resampling.cubic).astype(np.float32)
        src_w, src_h = src.width, src.height

    dem[dem < -100] = 0
    print(f"[HILLSHADE] DEM read: {dem.shape[1]}x{dem.shape[0]} "
          f"(from {src_w}x{src_h}, buf={HS_BUF}px)")

    ls = LightSource(azdeg=azimuth, altdeg=D.HILLSHADE_ALTITUDE)
    rgb_buf = ls.shade(
        np.clip(dem, 0, D.MAX_HILLSHADE_ELEVATION),
        cmap=_TERRAIN_CMAP,
        vert_exag=D.HILLSHADE_VERT_EXAG,
        blend_mode=D.HILLSHADE_BLEND_MODE,
    )  # (read_h, read_w, 4) RGBA float 0-1

    # Ocean mask
    ocean_mask = dem <= 0
    ocean_rgb = _hex_to_rgb(D.OCEAN_COLOR)
    for c in range(3):
        rgb_buf[:, :, c] = np.where(ocean_mask,
                                     ocean_rgb[c] / 255.0,
                                     rgb_buf[:, :, c])

    # Crop buffer -> exact output size, convert to uint8 RGB
    rgb_cropped = rgb_buf[buf_top:buf_top + h_px, buf_left:buf_left + w_px, :3]
    out_rgb = (np.clip(rgb_cropped, 0, 1) * 255).astype(np.uint8)

    Image.fromarray(out_rgb, "RGB").save(str(layer_path), "PNG")

    # Save ocean mask (used to clip rivers at the coastline)
    ocean_cropped = ocean_mask[buf_top:buf_top + h_px, buf_left:buf_left + w_px]
    ocean_path = layer_path.with_name("ocean_mask.png")
    Image.fromarray((ocean_cropped * 255).astype(np.uint8), "L").save(
        str(ocean_path), "PNG")

    _write_deps(layer_path, current_deps)
    print(f"[HILLSHADE] saved: {layer_path.name}")


# ---------------------------------------------------------------------------
# Layer 2: Lakes  (RGBA PNG, transparent background)
# ---------------------------------------------------------------------------

def _render_lakes_layer(d: Deck, layer_path: Path, force: bool = False) -> None:
    """Rasterize lake polygons onto a transparent RGBA image."""
    from rasterio.transform import from_bounds
    from rasterio import features as rio_features
    from PIL import Image

    osm_fp = _resolve_osm_file(d.osm_lakes_geojson)
    if not osm_fp.exists():
        print(f"[LAKES-L] ERROR: OSM source missing: {d.osm_lakes_geojson}")
        return

    w_px, h_px = _compute_pixel_dims(d)
    current_deps = {
        "osm_mtime": osm_fp.stat().st_mtime,
        "bbox":      [d.bbox_west, d.bbox_east, d.bbox_south, d.bbox_north],
        "w_px": w_px, "h_px": h_px,
    }
    if not force and not _is_stale(layer_path, current_deps):
        print(f"[LAKES-L] cached: {layer_path.name}")
        return

    out_transform = from_bounds(
        d.bbox_west, d.bbox_south, d.bbox_east, d.bbox_north,
        w_px, h_px,
    )

    lakes = _load_osm_lakes(d)
    # Start with fully transparent RGBA
    rgba = np.zeros((h_px, w_px, 4), dtype=np.uint8)

    if not lakes.empty:
        lake_fc = _hex_to_rgb(D.LAKE_FACECOLOR)
        lake_shapes = [(geom, 1) for geom in lakes.geometry if not geom.is_empty]
        if lake_shapes:
            lake_mask = rio_features.rasterize(
                lake_shapes,
                out_shape=(h_px, w_px),
                transform=out_transform,
                fill=0, default_value=1, dtype=np.uint8,
            )
            rgba[:, :, 0] = np.where(lake_mask, lake_fc[0], 0)
            rgba[:, :, 1] = np.where(lake_mask, lake_fc[1], 0)
            rgba[:, :, 2] = np.where(lake_mask, lake_fc[2], 0)
            rgba[:, :, 3] = np.where(lake_mask, 255, 0)
            print(f"[LAKES-L] rasterized {len(lake_shapes)} lakes")

    Image.fromarray(rgba, "RGBA").save(str(layer_path), "PNG")
    _write_deps(layer_path, current_deps)
    print(f"[LAKES-L] saved: {layer_path.name}")


# ---------------------------------------------------------------------------
# Layer 3: Rivers  (RGBA PNG, transparent, 2x supersampled anti-aliasing)
# ---------------------------------------------------------------------------

def _render_rivers_layer(d: Deck, layer_path: Path, force: bool = False) -> None:
    """Rasterize river lines onto a transparent RGBA image (anti-aliased)."""
    from rasterio.transform import from_bounds
    from PIL import Image, ImageDraw

    osm_fp = _resolve_osm_file(d.osm_rivers_geojson)
    if not osm_fp.exists():
        print(f"[RIVERS-L] ERROR: OSM source missing: {d.osm_rivers_geojson}")
        return

    w_px, h_px = _compute_pixel_dims(d)
    current_deps = {
        "osm_mtime": osm_fp.stat().st_mtime,
        "bbox":      [d.bbox_west, d.bbox_east, d.bbox_south, d.bbox_north],
        "w_px": w_px, "h_px": h_px,
    }
    if not force and not _is_stale(layer_path, current_deps):
        print(f"[RIVERS-L] cached: {layer_path.name}")
        return

    rivers = _load_osm_rivers(d)

    # Start with fully transparent RGBA
    rgba = np.zeros((h_px, w_px, 4), dtype=np.uint8)

    if not rivers.empty:
        river_rgb = _hex_to_rgb(D.RIVER_COLOR)
        ss = 2  # supersampling factor
        ss_w, ss_h = w_px * ss, h_px * ss
        ss_transform = from_bounds(
            d.bbox_west, d.bbox_south, d.bbox_east, d.bbox_north,
            ss_w, ss_h,
        )
        lw_px = max(1, int(D.RIVER_LINEWIDTH * D.FIGURE_DPI / 72 * ss + 0.5))

        river_alpha = Image.new("L", (ss_w, ss_h), 0)
        draw = ImageDraw.Draw(river_alpha)

        # Precompute inverse affine coefficients for vectorised coord transform
        inv = ~ss_transform
        a, b, c_coeff, d_coeff, e, f = (
            inv.a, inv.b, inv.c, inv.d, inv.e, inv.f
        )

        for geom in rivers.geometry:
            if geom.is_empty:
                continue
            lines = geom.geoms if geom.geom_type == "MultiLineString" else [geom]
            for line in lines:
                if line.is_empty or len(line.coords) < 2:
                    continue
                # Vectorised geo -> pixel conversion (numpy)
                coords = np.array(line.coords)  # (N, 2)
                px_x = a * coords[:, 0] + b * coords[:, 1] + c_coeff
                px_y = d_coeff * coords[:, 0] + e * coords[:, 1] + f
                px_coords = list(zip(px_x.tolist(), px_y.tolist()))
                draw.line(px_coords, fill=255, width=lw_px)

        # Downsample 2x2 blocks for anti-aliasing
        alpha_arr = np.array(river_alpha, dtype=np.float32)
        alpha_aa = alpha_arr.reshape(h_px, ss, w_px, ss).mean(axis=(1, 3))
        alpha_u8 = np.clip(alpha_aa, 0, 255).astype(np.uint8)

        # Write RGBA: river colour in RGB, anti-aliased alpha
        rgba[:, :, 0] = river_rgb[0]
        rgba[:, :, 1] = river_rgb[1]
        rgba[:, :, 2] = river_rgb[2]
        rgba[:, :, 3] = alpha_u8

        print(f"[RIVERS-L] rasterized {len(rivers)} rivers (AA {ss}x)")

    Image.fromarray(rgba, "RGBA").save(str(layer_path), "PNG")
    _write_deps(layer_path, current_deps)
    print(f"[RIVERS-L] saved: {layer_path.name}")


# ---------------------------------------------------------------------------
# Compass needle  (burned into basemap & thumbnail)
# ---------------------------------------------------------------------------

def _draw_compass_needle(img, north_up: bool = True):
    """Draw a compass needle in the top-right corner of a Pillow Image.

    Args:
        img: PIL Image (RGB or RGBA). Modified in-place AND returned.
        north_up: True → red tip points up (N ↑).
                  False → red tip points down (N ↓), for south-up basemaps.

    Returns the modified Image.
    """
    import math
    from PIL import Image, ImageDraw, ImageFont

    w, h = img.size
    short = min(w, h)

    # Needle radius and position
    r = max(18, int(short * D.COMPASS_RADIUS_RATIO))
    margin = max(10, int(short * D.COMPASS_MARGIN_RATIO))
    cx = w - margin - r          # center x (from right edge)
    cy = margin + r              # center y (from top edge)

    # --- Background circle (semi-transparent white) ---
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    bg_r = int(r * 1.45)        # background circle slightly larger
    odraw.ellipse(
        [cx - bg_r, cy - bg_r, cx + bg_r, cy + bg_r],
        fill=(255, 255, 255, D.COMPASS_BG_ALPHA),
        outline=D.COMPASS_OUTLINE_COLOR,
        width=max(1, r // 12),
    )

    # --- Needle (two triangles: north half = red, south half = white) ---
    # needle_len = distance from center to tip
    needle_len = int(r * 0.92)
    half_w = max(2, int(r * 0.28))    # half-width at center

    if north_up:
        # Red triangle: tip at top
        north_tri = [(cx, cy - needle_len),
                     (cx - half_w, cy),
                     (cx + half_w, cy)]
        # White triangle: tip at bottom
        south_tri = [(cx, cy + needle_len),
                     (cx - half_w, cy),
                     (cx + half_w, cy)]
    else:
        # South-up: red tip points down
        north_tri = [(cx, cy + needle_len),
                     (cx - half_w, cy),
                     (cx + half_w, cy)]
        south_tri = [(cx, cy - needle_len),
                     (cx - half_w, cy),
                     (cx + half_w, cy)]

    n_col = tuple(int(D.COMPASS_NORTH_COLOR.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
    s_col = tuple(int(D.COMPASS_SOUTH_COLOR.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
    ol_col = D.COMPASS_OUTLINE_COLOR
    ol_w = max(1, r // 15)

    odraw.polygon(north_tri, fill=(*n_col, 255), outline=ol_col, width=ol_w)
    odraw.polygon(south_tri, fill=(*s_col, 255), outline=ol_col, width=ol_w)

    # --- "N" label ---
    font_size = max(8, int(r * 0.55))
    try:
        font = ImageFont.truetype(D.COMPASS_FONT, font_size)
    except OSError:
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except OSError:
            font = ImageFont.load_default()

    label_y = cy - needle_len - font_size - max(1, r // 8) if north_up \
        else cy + needle_len + max(1, r // 8)
    # Center the "N" horizontally
    bbox_n = odraw.textbbox((0, 0), "N", font=font)
    tw = bbox_n[2] - bbox_n[0]
    label_x = cx - tw // 2
    odraw.text((label_x, label_y), "N", fill=(*n_col, 255), font=font,
               stroke_width=max(1, font_size // 10),
               stroke_fill=(255, 255, 255, 220))

    # Composite overlay onto image
    if img.mode != "RGBA":
        img = img.convert("RGBA")
        result = Image.alpha_composite(img, overlay)
        return result.convert("RGB")
    else:
        return Image.alpha_composite(img, overlay)


# ---------------------------------------------------------------------------
# Sub-region fallback: crop parent basemap when DEM is unavailable
# ---------------------------------------------------------------------------

def crop_basemap_from_parent(
    parent_basemap_path: Path,
    parent_extent: tuple,
    sub_extent: tuple,
    output_path: Path,
    target_w: int,
    target_h: int,
    north_up: bool = True,
    force: bool = False,
) -> bool:
    """Crop the parent basemap to *sub_extent* and resize to target dims.

    Uses approximate linear geo-to-pixel mapping (adequate for small
    sub-regions within the same basemap).  Returns True on success.

    When *north_up* is False the parent image is assumed to be stored
    south-up (rotated 180°).  Pixel coordinates are flipped accordingly
    so the crop region maps to the correct geography.

    A compass needle is burned into the result (north-up or south-up
    depending on *north_up*).

    Args:
        parent_basemap_path: Path to the full-region basemap WebP.
        parent_extent: (west, east, south, north) of the parent.
        sub_extent: (west, east, south, north) of the sub-region.
        output_path: Where to save the cropped basemap WebP.
        target_w: Target pixel width.
        target_h: Target pixel height.
        north_up: True for normal basemap, False for south-up rotated.
        force: Overwrite even if deps are up to date.
    """
    from PIL import Image

    if not parent_basemap_path.exists():
        print(f"[BASEMAP-CROP] ERROR: Parent basemap not found: "
              f"{parent_basemap_path}")
        return False

    current_deps = {
        "parent_mtime": parent_basemap_path.stat().st_mtime,
        "sub_extent":   list(sub_extent),
        "target_w": target_w, "target_h": target_h,
        "north_up": north_up,
    }
    if not force and not _is_stale(output_path, current_deps):
        size_kb = output_path.stat().st_size / 1024
        print(f"[BASEMAP-CROP] cached: {output_path.name} ({size_kb:,.0f} KB)")
        return True

    img = Image.open(str(parent_basemap_path))
    pw, ph = img.size
    p_w, p_e, p_s, p_n = parent_extent
    s_w, s_e, s_s, s_n = sub_extent

    # Geo → pixel (linear mapping)
    x0 = int((s_w - p_w) / (p_e - p_w) * pw)
    x1 = int((s_e - p_w) / (p_e - p_w) * pw)
    y0 = int((p_n - s_n) / (p_n - p_s) * ph)  # north = top = y=0
    y1 = int((p_n - s_s) / (p_n - p_s) * ph)

    # Clamp to image bounds
    x0 = max(0, min(pw, x0))
    x1 = max(0, min(pw, x1))
    y0 = max(0, min(ph, y0))
    y1 = max(0, min(ph, y1))

    if x1 <= x0 or y1 <= y0:
        print(f"[BASEMAP-CROP] ERROR: Crop region is empty "
              f"({x0},{y0})-({x1},{y1})")
        return False

    # For south-up source images the pixel grid is flipped 180°
    if not north_up:
        x0, x1 = pw - x1, pw - x0
        y0, y1 = ph - y1, ph - y0
        x0 = max(0, min(pw, x0))
        x1 = max(0, min(pw, x1))
        y0 = max(0, min(ph, y0))
        y1 = max(0, min(ph, y1))

    if x1 <= x0 or y1 <= y0:
        print(f"[BASEMAP-CROP] ERROR: Crop region is empty "
              f"({x0},{y0})-({x1},{y1})")
        return False

    cropped = img.crop((x0, y0, x1, y1))
    resized = cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    resized.save(str(output_path), "WEBP",
                 quality=D.BASEMAP_WEBP_QUALITY, method=6)

    _write_deps(output_path, current_deps)
    size_kb = output_path.stat().st_size / 1024
    print(f"[BASEMAP-CROP] Cropped from parent: {output_path.name} "
          f"({size_kb:,.0f} KB, {target_w}x{target_h} px)")
    return True


# ---------------------------------------------------------------------------
# Composite:  hillshade + lakes + rivers  ->  final basemap PNG
# ---------------------------------------------------------------------------

def generate_raster_basemap(
    d: Deck,
    output_path: Path,
    force: bool = False,
    force_hillshade: bool = False,
    force_lakes: bool = False,
    force_rivers: bool = False,
) -> None:
    """Render the basemap as three cached layers and composite them.

    Each layer is an independent PNG that is only re-rendered when missing
    or when the corresponding ``force_*`` flag is set.  The final composite
    (alpha-blend) is fast (~0.1 s) and always runs unless the output
    already exists and *force* is ``False``.

    Layers:
      1. ``hillshade.png``  -- RGB, opaque  (DEM + hillshade + ocean mask)
      2. ``lakes.png``      -- RGBA, transparent  (lake polygons)
      3. ``rivers.png``     -- RGBA, transparent  (river lines, anti-aliased)
    """
    from PIL import Image

    output_path.parent.mkdir(parents=True, exist_ok=True)
    layers = _layer_dir(d)

    hs_path = layers / "hillshade.png"
    lk_path = layers / "lakes.png"
    rv_path = layers / "rivers.png"

    # Render individual layers (each manages its own deps-based cache)
    _render_hillshade_layer(d, hs_path, force=force or force_hillshade)
    _render_lakes_layer(d, lk_path, force=force or force_lakes)
    _render_rivers_layer(d, rv_path, force=force or force_rivers)

    # Abort cleanly if any required layer is missing (DEM or OSM not yet downloaded)
    missing = [p.name for p in (hs_path, lk_path, rv_path) if not p.exists()]
    if missing:
        print(f"[BASEMAP] Cannot composite — missing layers: {', '.join(missing)}")
        return

    # Deps-based composite cache check (only depends on the layer files themselves)
    current_deps = {
        "hs_mtime": hs_path.stat().st_mtime,
        "lk_mtime": lk_path.stat().st_mtime,
        "rv_mtime": rv_path.stat().st_mtime,
    }
    if not force and not _is_stale(output_path, current_deps):
        size_kb = output_path.stat().st_size / 1024
        print(f"[BASEMAP] Already exists: {output_path.name} ({size_kb:,.0f} KB)")
        return

    # Composite: hillshade (RGB) + lakes (RGBA) + rivers (RGBA)
    #   Rivers under lakes are erased at pixel level (much faster than
    #   shapely geometry difference on hundreds of MultiLineStrings).
    base = Image.open(str(hs_path)).convert("RGBA")
    lake_layer = Image.open(str(lk_path))     # RGBA
    river_layer = Image.open(str(rv_path))    # RGBA

    # Erase river alpha where lakes are opaque
    lake_a = np.array(lake_layer)[:, :, 3]    # uint8
    river_arr = np.array(river_layer)         # (H, W, 4)
    river_arr[:, :, 3] = np.where(lake_a > 0, 0, river_arr[:, :, 3])

    # Erase river alpha where ocean (DEM <= 0) — clip rivers at coastline
    ocean_mask_path = layers / "ocean_mask.png"
    if ocean_mask_path.exists():
        ocean_mask = np.array(Image.open(str(ocean_mask_path)))  # 0 or 255
        river_arr[:, :, 3] = np.where(ocean_mask > 0, 0, river_arr[:, :, 3])

    river_layer = Image.fromarray(river_arr, "RGBA")

    base = Image.alpha_composite(base, lake_layer)
    base = Image.alpha_composite(base, river_layer)

    final = base.convert("RGB")
    final.save(str(output_path), "WEBP", quality=D.BASEMAP_WEBP_QUALITY, method=6)

    _write_deps(output_path, current_deps)
    size_kb = output_path.stat().st_size / 1024
    w_px, h_px = _compute_pixel_dims(d)
    print(f"[BASEMAP] Done: {output_path.name} ({size_kb:,.0f} KB, {w_px}x{h_px} px)")


def generate_raster_basemap_rot(
    d: Deck,
    output_path: Path,
    force: bool = False,
) -> None:
    """Render a basemap with hillshade azimuth 135° (for 180° map rotation).

    Reuses the cached lakes/rivers/ocean-mask layers from the normal
    basemap build — only the hillshade is re-rendered with the rotated
    azimuth.  The image is stored **north-up** (no pre-rotation).
    CSS ``transform: rotate(180deg)`` in the Anki template handles the
    visual rotation.
    """
    from PIL import Image

    output_path.parent.mkdir(parents=True, exist_ok=True)
    layers = _layer_dir(d)

    # Rotated hillshade gets its own cached file
    hs_rot_path = layers / "hillshade_rot.png"
    _render_hillshade_layer(d, hs_rot_path, force=force,
                            azimuth=D.HILLSHADE_AZIMUTH_ROT)

    # Reuse lakes and rivers from the normal basemap build (same layer dir)
    lk_path = layers / "lakes.png"
    rv_path = layers / "rivers.png"

    # Abort cleanly if any required layer is missing
    missing = [p.name for p in (hs_rot_path, lk_path, rv_path) if not p.exists()]
    if missing:
        print(f"[BASEMAP-ROT] Cannot composite — missing layers: {', '.join(missing)}")
        return

    # Deps-based composite cache check
    current_deps = {
        "hs_rot_mtime": hs_rot_path.stat().st_mtime,
        "lk_mtime":     lk_path.stat().st_mtime,
        "rv_mtime":     rv_path.stat().st_mtime,
    }
    if not force and not _is_stale(output_path, current_deps):
        size_kb = output_path.stat().st_size / 1024
        print(f"[BASEMAP-ROT] Already exists: {output_path.name} ({size_kb:,.0f} KB)")
        return

    # Composite (same logic as generate_raster_basemap)
    base = Image.open(str(hs_rot_path)).convert("RGBA")
    lake_layer = Image.open(str(lk_path))
    river_layer = Image.open(str(rv_path))

    lake_a = np.array(lake_layer)[:, :, 3]
    river_arr = np.array(river_layer)
    river_arr[:, :, 3] = np.where(lake_a > 0, 0, river_arr[:, :, 3])

    ocean_mask_path = layers / "ocean_mask.png"
    if ocean_mask_path.exists():
        ocean_mask = np.array(Image.open(str(ocean_mask_path)))
        river_arr[:, :, 3] = np.where(ocean_mask > 0, 0, river_arr[:, :, 3])

    river_layer = Image.fromarray(river_arr, "RGBA")

    base = Image.alpha_composite(base, lake_layer)
    base = Image.alpha_composite(base, river_layer)

    final = base.convert("RGB")
    final.save(str(output_path), "WEBP", quality=D.BASEMAP_WEBP_QUALITY, method=6)

    _write_deps(output_path, current_deps)
    size_kb = output_path.stat().st_size / 1024
    w_px, h_px = _compute_pixel_dims(d)
    print(f"[BASEMAP-ROT] Done: {output_path.name} "
          f"({size_kb:,.0f} KB, {w_px}x{h_px} px)")



# ===========================================================================
# COUNTRY BORDERS (OSM)
# ===========================================================================

def _resolve_osm_file(path: Path) -> Path:
    """Return *path* if it exists, otherwise try ``output/data/osm/`` mirror.

    The canonical location configured in ``DATA_DIR_OSM`` is ``data/osm/``,
    but older runs may have stored the GeoJSON files under
    ``output/data/osm/``.  This helper keeps both locations working.
    """
    if path.exists():
        return path
    alt = D.PROJECT_ROOT / "output" / "data" / "osm" / path.name
    if alt.exists():
        print(f"[OSM] Fallback: {path.name} found in output/data/osm/")
        return alt
    return path          # let callers handle the missing-file warning


_osm_border_cache: dict = {}


def _load_osm_borders(d: Deck) -> gpd.GeoDataFrame:
    """Load OSM admin_level=2 border LineStrings, clipped to render area."""
    key = str(d.osm_borders_geojson)
    if key in _osm_border_cache:
        return _osm_border_cache[key]

    fp = _resolve_osm_file(d.osm_borders_geojson)
    if not fp.exists():
        print(f"[WARN] OSM borders not found: {d.osm_borders_geojson}")
        _osm_border_cache[key] = gpd.GeoDataFrame()
        return _osm_border_cache[key]

    gdf = gpd.read_file(str(fp))
    # Clip to render area
    render_box = box(
        d.bbox_west - D.RENDER_BUFFER, d.bbox_south - D.RENDER_BUFFER,
        d.bbox_east + D.RENDER_BUFFER, d.bbox_north + D.RENDER_BUFFER,
    )
    gdf = gdf[gdf.intersects(render_box)]
    if not gdf.empty:
        gdf = gdf.clip(render_box)
        gdf = gdf[~gdf.geometry.is_empty]

    print(f"[BORDERS] Loaded {len(gdf)} OSM border segments from {fp.name}")
    _osm_border_cache[key] = gdf
    return gdf


_osm_river_cache: dict = {}
_osm_lake_cache: dict = {}


def _load_osm_lakes(d: Deck) -> gpd.GeoDataFrame:
    """Load OSM lake polygons, filtered by minimum area."""
    key = str(d.osm_lakes_geojson)
    if key in _osm_lake_cache:
        return _osm_lake_cache[key]

    fp = _resolve_osm_file(d.osm_lakes_geojson)
    if not fp.exists():
        print(f"[WARN] OSM lakes not found: {d.osm_lakes_geojson}")
        _osm_lake_cache[key] = gpd.GeoDataFrame()
        return _osm_lake_cache[key]

    gdf = gpd.read_file(str(fp))
    # Clip to render area
    render_box = box(
        d.bbox_west - D.RENDER_BUFFER, d.bbox_south - D.RENDER_BUFFER,
        d.bbox_east + D.RENDER_BUFFER, d.bbox_north + D.RENDER_BUFFER,
    )
    gdf = gdf[gdf.intersects(render_box)]
    if not gdf.empty:
        gdf = gdf.clip(render_box)

    # Filter by minimum area (metric CRS for accurate measurement)
    if D.LAKE_MIN_AREA_KM2 > 0 and not gdf.empty:
        gdf_metric = gdf.to_crs(epsg=3035)  # ETRS89/LAEA Europe
        min_area_m2 = D.LAKE_MIN_AREA_KM2 * 1e6
        mask = gdf_metric.geometry.area >= min_area_m2
        gdf = gdf[mask.values]

    print(f"[LAKES] Loaded {len(gdf)} OSM lakes from {fp.name} (>={D.LAKE_MIN_AREA_KM2} km2)")
    _osm_lake_cache[key] = gdf
    return gdf


def _load_osm_rivers(d: Deck) -> gpd.GeoDataFrame:
    """Load OSM rivers: named only -> dissolve by name -> filter by length -> clip lakes."""
    import time as _t
    key = str(d.osm_rivers_geojson)
    if key in _osm_river_cache:
        return _osm_river_cache[key]

    fp = _resolve_osm_file(d.osm_rivers_geojson)
    if not fp.exists():
        print(f"[WARN] OSM rivers not found: {d.osm_rivers_geojson}")
        _osm_river_cache[key] = gpd.GeoDataFrame()
        return _osm_river_cache[key]

    t0 = _t.perf_counter()
    gdf = gpd.read_file(str(fp))
    total_raw = len(gdf)
    print(f"[RIVERS]  read GeoJSON: {_t.perf_counter()-t0:.1f}s ({total_raw} segments)")

    # 1) Drop unnamed segments
    t1 = _t.perf_counter()
    if "name" in gdf.columns:
        gdf = gdf[gdf["name"].fillna("").str.strip() != ""]
    named_count = len(gdf)
    print(f"[RIVERS]  drop unnamed: {_t.perf_counter()-t1:.1f}s ({named_count} named)")

    # 2) Clip to render area
    t2 = _t.perf_counter()
    render_box = box(
        d.bbox_west - D.RENDER_BUFFER, d.bbox_south - D.RENDER_BUFFER,
        d.bbox_east + D.RENDER_BUFFER, d.bbox_north + D.RENDER_BUFFER,
    )
    gdf = gdf[gdf.intersects(render_box)]
    gdf = gdf.clip(render_box)
    gdf = gdf[~gdf.geometry.is_empty]
    print(f"[RIVERS]  clip bbox: {_t.perf_counter()-t2:.1f}s ({len(gdf)} clipped)")

    # 3) Dissolve segments by name -> one MultiLineString per river
    t3 = _t.perf_counter()
    if "name" in gdf.columns and not gdf.empty:
        gdf = gdf.dissolve(by="name", as_index=False)
    dissolved_count = len(gdf)
    print(f"[RIVERS]  dissolve: {_t.perf_counter()-t3:.1f}s ({dissolved_count} rivers)")

    # 4) Filter by total river length (metric CRS)
    t4 = _t.perf_counter()
    if D.RIVER_MIN_LENGTH_KM > 0 and not gdf.empty:
        gdf_metric = gdf.to_crs(epsg=3035)
        min_len_m = D.RIVER_MIN_LENGTH_KM * 1000
        mask = gdf_metric.geometry.length >= min_len_m
        gdf = gdf[mask.values]
    kept_count = len(gdf)
    print(f"[RIVERS]  length filter: {_t.perf_counter()-t4:.1f}s ({kept_count} kept)")

    # Lake-clipping is done at pixel level in the composite step
    # (erase river alpha where lakes are opaque) -- much faster than
    # shapely difference() on hundreds of MultiLineStrings.

    print(f"[RIVERS] Total: {_t.perf_counter()-t0:.1f}s  "
          f"{total_raw} raw -> {named_count} named -> "
          f"{dissolved_count} dissolved -> {kept_count} >={D.RIVER_MIN_LENGTH_KM} km")
    _osm_river_cache[key] = gdf
    return gdf


def render_country_borders(ax, d: Deck) -> None:
    borders = _load_osm_borders(d)
    if borders.empty:
        return
    ax.add_geometries(
        borders.geometry, crs=ccrs.PlateCarree(),
        facecolor="none", edgecolor=D.COUNTRY_BORDER_COLOR,
        linewidth=D.COUNTRY_BORDER_WIDTH, linestyle=D.COUNTRY_BORDER_STYLE,
        zorder=4,
    )


# ===========================================================================
# AVE POLYGONS
# ===========================================================================

_gdf_cache: dict = {}


def load_polygons(d: Deck) -> gpd.GeoDataFrame:
    """Load the deck's mountain-group polygons from GeoJSON."""
    key = str(d.osm_geojson)
    if key in _gdf_cache:
        return _gdf_cache[key]
    fp = _resolve_osm_file(d.osm_geojson)
    if not fp.exists():
        print(f"[WARN] GeoJSON not found: {d.osm_geojson}")
        return gpd.GeoDataFrame()
    gdf = gpd.read_file(str(fp))
    _gdf_cache[key] = gdf
    return gdf


def _label_point(polygon) -> Point:
    """Optimal interior label placement (negative-buffer technique).

    Uses progressively smaller shrink fractions to find a suitable interior point.
    """
    minx, miny, maxx, maxy = polygon.bounds
    diag = ((maxx - minx) ** 2 + (maxy - miny) ** 2) ** 0.5
    for frac in D.LABEL_SHRINK_FRACTIONS:
        shrunk = polygon.buffer(-diag * frac)
        if shrunk.is_empty or shrunk.area <= 0:
            continue
        if shrunk.geom_type == "MultiPolygon":
            shrunk = max(shrunk.geoms, key=lambda g: g.area)
        return shrunk.centroid
    return polygon.representative_point()


def _get_ref(row, d: Deck) -> str:
    """Extract the group ref value from a GeoDataFrame row."""
    tag = d.osm_tag
    tag_col = tag.replace(":", "_")
    ref = row.get(tag, row.get(tag_col, ""))
    return str(ref) if ref else ""


def render_polygons_colored(ax, d: Deck, *, alpha: float = None, show_ids: bool = True) -> list:
    """
    Render all polygons coloured by Hauptgruppe.

    Borders are drawn as a single unified layer via ``unary_union`` so
    shared edges have equal width everywhere.
    """
    gdf = load_polygons(d)
    if gdf.empty:
        return

    label_texts = []
    all_geoms = []
    labeled_groups = set()  # Track which group_ids already got a label

    for _, row in gdf.iterrows():
        ref = _get_ref(row, d)
        if not d.has_osm_ref(ref):
            continue

        group = d.group_by_osm_ref(ref)
        ci = d.colors[group.hauptgruppe]
        geom = row.geometry

        fc = ci["fill"]
        fa = alpha if alpha is not None else D.POLYGON_ALPHA

        ax.add_geometries([geom], crs=ccrs.PlateCarree(),
                          facecolor=fc, edgecolor="none", alpha=fa, zorder=5)
        all_geoms.append(geom)

        if show_ids and group.group_id not in labeled_groups:
            labeled_groups.add(group.group_id)
            lp = _label_point(geom)
            t = ax.text(lp.x, lp.y, group.group_id,
                        transform=ccrs.PlateCarree(),
                        fontsize=D.LABEL_FONTSIZE_ID, fontweight="bold",
                        color="white", ha="center", va="center", zorder=7)
            label_texts.append(t)

    # Unified border layer
    if all_geoms:
        merged = unary_union([g.boundary for g in all_geoms])
        geom_list = [merged] if merged.geom_type != "MultiLineString" else list(merged.geoms)
        ax.add_geometries(geom_list, crs=ccrs.PlateCarree(),
                          facecolor="none", edgecolor=D.POLYGON_BORDER_COLOR,
                          linewidth=D.POLYGON_BORDER_WIDTH, alpha=1.0, zorder=6)
    return label_texts


def render_single_polygon(ax, d: Deck, ref) -> None:
    """Render one polygon with a red outline (no fill, no label)."""
    gdf = load_polygons(d)
    if gdf.empty:
        return

    for _, row in gdf.iterrows():
        if _get_ref(row, d) != ref:
            continue

        geom = row.geometry

        ax.add_geometries([geom], crs=ccrs.PlateCarree(),
                          facecolor="none", edgecolor="#cc0000",
                          linewidth=2.0, alpha=1.0, zorder=6)
        break


def render_parent_polygon(ax, d: Deck, ref) -> None:
    """Render the dissolved parent region with internal dashed boundaries.

    1. Dissolves all sibling polygons (same parent, e.g. SZ) into one
       unified shape and draws it with a light Hauptgruppe fill + solid
       outline.
    2. Computes internal boundaries between siblings and draws them as
       thin dashed lines so the individual Sottosezioni remain visible.

    Only active when ``d.classification.parent_osm_tag`` is set.
    """
    parent_tag = d.classification.parent_osm_tag
    if not parent_tag:
        return

    gdf = load_polygons(d)
    if gdf.empty:
        return

    # Find the parent value for the target group
    parent_value = None
    for _, row in gdf.iterrows():
        if _get_ref(row, d) == ref:
            parent_value = row.get(parent_tag, "")
            break
    if not parent_value:
        return

    # Collect sibling geometries (same parent, excluding target)
    sibling_geoms = []
    for _, row in gdf.iterrows():
        if row.get(parent_tag, "") == parent_value:
            r = _get_ref(row, d)
            if r != ref:
                sibling_geoms.append(row.geometry)
    if not sibling_geoms:
        return

    # Look up the Hauptgruppe colour for this group
    group = d.group_by_osm_ref(ref)
    ci = d.colors.get(group.hauptgruppe, {})
    fill_color = ci.get("fill", "#888888")

    # 1) Dissolved union of all siblings → solid outline + light fill
    dissolved = unary_union(sibling_geoms)
    ax.add_geometries([dissolved], crs=ccrs.PlateCarree(),
                      facecolor=fill_color, edgecolor=fill_color,
                      linewidth=1.4, alpha=0.25, zorder=4)

    # 2) Internal boundaries: individual edges minus dissolved outer boundary
    all_boundaries = unary_union([g.boundary for g in sibling_geoms])
    dissolved_boundary = dissolved.boundary
    internal_edges = all_boundaries.difference(dissolved_boundary.buffer(1e-6))
    if not internal_edges.is_empty:
        # Convert to list of geometries for add_geometries
        from shapely.geometry import MultiLineString, LineString
        if isinstance(internal_edges, (LineString, MultiLineString)):
            lines = [internal_edges] if isinstance(internal_edges, LineString) \
                    else list(internal_edges.geoms)
        else:
            # GeometryCollection — extract line-like parts
            lines = [g for g in internal_edges.geoms
                     if isinstance(g, (LineString, MultiLineString))]
        if lines:
            merged_internal = unary_union(lines)
            ax.add_geometries([merged_internal], crs=ccrs.PlateCarree(),
                              facecolor="none", edgecolor=fill_color,
                              linewidth=0.8, alpha=0.45, zorder=4.5,
                              linestyle="--")


def render_question_mark(ax, d: Deck, ref) -> None:
    """Render question marks via greedy circle-packing.

    Algorithm:
    1. Find the largest inscribed circle (polylabel) of the polygon.
    2. Subtract that circle from the polygon.
    3. Repeat on the largest remaining fragment until the next circle's
       radius drops below ``QMARK_MIN_RADIUS_RATIO * r_max``.
    4. Each circle becomes a '?' whose fontsize is proportional to
       its radius relative to the largest circle.
    """
    from shapely.ops import polylabel

    gdf = load_polygons(d)
    if gdf.empty:
        return

    for _, row in gdf.iterrows():
        if _get_ref(row, d) != ref:
            continue

        geom = row.geometry

        # ── Greedy circle packing ──────────────────────────────────────
        circles = []            # list of (x, y, radius)
        remaining = geom
        r_max = None

        for _ in range(20):     # safety cap
            if remaining.is_empty or remaining.area < 1e-10:
                break

            # Pick the largest remaining fragment
            if remaining.geom_type == "MultiPolygon":
                target = max(remaining.geoms, key=lambda g: g.area)
            else:
                target = remaining
            if target.area < 1e-10:
                break

            # Largest inscribed circle centre + radius
            pole = polylabel(target, tolerance=D.QMARK_POLYLABEL_TOL)
            r = pole.distance(geom.boundary)
            if r < D.QMARK_MIN_RADIUS_ABS:
                break

            if r_max is None:
                r_max = r
            else:
                ratio_ok = r / r_max >= D.QMARK_MIN_RADIUS_RATIO
                rest_pct = remaining.area / geom.area
                if not ratio_ok and rest_pct <= D.QMARK_MAX_REST_AREA:
                    break

            circles.append((pole.x, pole.y, r))
            remaining = remaining.difference(pole.buffer(r))

        if not circles:
            break

        # ── Convert circle radius (degrees) to fontsize (points) ───────
        #    fig height in points = fig_height_inches * 72
        #    lat extent in degrees = bbox_north - bbox_south
        #    → pts_per_deg = (fig_height_in * 72) / lat_range
        fig = ax.get_figure()
        fig_h_in = fig.get_figheight()
        lat_range = d.bbox_north - d.bbox_south
        pts_per_deg = (fig_h_in * 72.0) / lat_range

        for cx, cy, r in circles:
            diameter_pts = 2.0 * r * pts_per_deg
            fontsize = int(diameter_pts * D.QMARK_FILL_FACTOR)
            fontsize = max(fontsize, D.QMARK_FONTSIZE_MIN)
            ax.text(cx, cy, "?",
                    transform=ccrs.PlateCarree(),
                    fontsize=fontsize, fontweight="bold",
                    color="#cc0000", ha="center", va="center",
                    zorder=10)
        break


# ===========================================================================
# NEIGHBOR OVERLAY — for "B Nachbarn" deck
# ===========================================================================

def compute_neighbors(d: Deck) -> dict:
    """Return {osm_ref: [neighbor_osm_ref, …]} for every group in *d*.

    Two groups are considered neighbours when their GeoJSON polygons
    touch or share a boundary.  A tiny buffer (1e-5°, ≈1 m) is applied
    before the intersection test to tolerate GeoJSON digitisation gaps.
    """
    gdf = load_polygons(d)
    if gdf.empty:
        return {}

    # Collect (ref, geometry) for valid groups
    items = []
    for _, row in gdf.iterrows():
        ref = _get_ref(row, d)
        if d.has_osm_ref(ref):
            items.append((ref, row.geometry))

    neighbors: dict = {ref: [] for ref, _ in items}
    for i, (ref_a, geom_a) in enumerate(items):
        for j in range(i + 1, len(items)):
            ref_b, geom_b = items[j]
            if geom_a.intersects(geom_b.buffer(1e-5)):
                neighbors[ref_a].append(ref_b)
                neighbors[ref_b].append(ref_a)
    return neighbors


def _wrap_label(name: str) -> str:
    """Insert newline in long group names at natural break points."""
    if len(name) <= 25:
        return name
    if "(" in name:
        return name.replace("(", "\n(")
    if " und " in name:
        return name.replace(" und ", "\nund ")
    mid = len(name) // 2
    best = -1
    for i, ch in enumerate(name):
        if ch == " " and (best < 0 or abs(i - mid) < abs(best - mid)):
            best = i
    if best > 0:
        return name[:best] + "\n" + name[best + 1:]
    return name


def render_neighbor_overlay(ax, d: Deck, ref, neighbor_refs) -> None:
    """Draw the target group (red) + its neighbours (black) with name labels.

    Target:    red outline (#cc0000, lw=2.0), no label.
    Neighbors: black outline (#000000, lw=1.5) + black "Name (ID)" label
               with white stroke outline for readability.
    """
    gdf = load_polygons(d)
    if gdf.empty:
        return

    target_geom = None
    nb_geoms = []  # (geom, group)

    for _, row in gdf.iterrows():
        r = _get_ref(row, d)
        if r == ref:
            target_geom = row.geometry
        elif r in neighbor_refs:
            nb_geoms.append((row.geometry, d.group_by_osm_ref(r)))

    # Draw neighbour polygons first (lower zorder)
    for geom, group in nb_geoms:
        ax.add_geometries([geom], crs=ccrs.PlateCarree(),
                          facecolor="none", edgecolor="#000000",
                          linewidth=1.5, alpha=1.0, zorder=6)
        lp = _label_point(geom)
        ax.text(lp.x, lp.y, f"{_wrap_label(group.name)}\n({group.group_id})",
                transform=ccrs.PlateCarree(),
                fontsize=8, fontweight="bold",
                color="black", ha="center", va="center", zorder=7,
                path_effects=[pe.withStroke(linewidth=3, foreground="white")])

    # Draw target polygon on top (no label)
    if target_geom is not None:
        ax.add_geometries([target_geom], crs=ccrs.PlateCarree(),
                          facecolor="none", edgecolor="#cc0000",
                          linewidth=2.0, alpha=1.0, zorder=6)


# ===========================================================================
# CITIES
# ===========================================================================

def render_cities(ax, d: Deck) -> None:
    # Scale label offsets proportionally to the map extent so that
    # sub-region (zoomed-in) maps get the same visual label distance
    # as the parent region.  The raw dx/dy values are authored for
    # the reference extents (~7.8° wide, ~3.4° tall for ostalpen);
    # here we normalise to a fixed fraction of the actual extent.
    map_w = d.bbox_east - d.bbox_west
    map_h = d.bbox_north - d.bbox_south
    off_x = 0.0065 * map_w          # ~0.65 % of width
    off_y = 0.006  * map_h           # ~0.60 % of height

    for name, lon, lat, dx, dy in d.cities:
        ax.plot(lon, lat, marker="o", markersize=3.5,
                color="black", markeredgecolor="black",
                transform=ccrs.PlateCarree(), zorder=9)
        # Use sign of dx/dy for direction, but fixed magnitude
        sdx = off_x if dx >= 0 else -off_x
        sdy = off_y if dy >= 0 else -off_y
        ha = "left" if dx >= 0 else "right"
        ax.text(lon + sdx, lat + sdy, name,
                transform=ccrs.PlateCarree(), fontsize=8,
                color="black", ha=ha, va="bottom", zorder=9)


# ===========================================================================
# COMPLETE MAP ASSEMBLY
# ===========================================================================

def create_figure(d: Deck):
    """New figure with correct projection, extent, and background.

    Figure size uses the cos(mid_lat)-corrected aspect ratio so the
    map has realistic proportions in PlateCarree.  The axes fill the
    entire figure (no margins) so that all exported PNGs have identical
    pixel dimensions — a requirement for the CSS overlay in Anki.
    """
    proj = get_projection(d)
    w, h = _corrected_figsize(d)
    fig = plt.figure(figsize=(w, h))
    ax = fig.add_axes([0, 0, 1, 1], projection=proj)
    ax.set_extent(d.extent, crs=ccrs.PlateCarree())
    # The figure size already includes cos(mid_lat) correction, so we must
    # allow the data to stretch to fill the figure.  The default 'equal'
    # aspect keeps 1°lon == 1°lat in display space, which leaves vertical
    # padding and makes overlays smaller than the raster basemap.
    ax.set_aspect('auto')
    ax.set_facecolor("#dde8f0")
    # Remove the black frame (spines) — they show through transparent overlays
    if hasattr(ax, 'outline_patch'):
        ax.outline_patch.set_visible(False)
    for spine in ax.spines.values():
        spine.set_visible(False)
    return fig, ax


def render_full_basemap(ax, d: Deck, *, cities: bool = True, borders: bool = True,
                        rivers: bool = True, lakes: bool = True,
                        svg_mode: bool = False, overlay_mode: bool = False) -> None:
    """
    Render the complete basemap into a matplotlib Axes.

    In normal mode the pre-rendered raster basemap PNG (hillshade + ocean +
    rivers + lakes) is loaded and drawn with ``ax.imshow()``.  Vector
    overlays (borders, cities) are still drawn on top via Cartopy.

    Args:
        ax: Axes to render into
        d: Deck configuration
        cities: Include city markers and labels
        borders: Include country border lines
        rivers / lakes: ignored (included in raster basemap)
        svg_mode: If True, rasterise low zorders to keep SVG small.
        overlay_mode: If True, skip basemap entirely and set transparent
                      background.  Borders/cities still controlled by flags.
    """
    if overlay_mode:
        ax.set_facecolor("none")
        ax.patch.set_alpha(0.0)
    else:
        if svg_mode:
            ax.set_rasterization_zorder(2.5)
        # Load the pre-rendered raster basemap
        basemap_path = d.output_images_dir / d.filename_basemap()
        if not basemap_path.exists():
            # Auto-generate if missing
            generate_raster_basemap(d, basemap_path)
        from PIL import Image as _PILImage
        basemap_img = np.array(_PILImage.open(str(basemap_path)))
        extent = [d.bbox_west, d.bbox_east, d.bbox_south, d.bbox_north]
        ax.imshow(basemap_img, origin="upper", extent=extent,
                  transform=ccrs.PlateCarree(),
                  interpolation="bilinear", zorder=1)
    if borders:
        render_country_borders(ax, d)
    if cities:
        render_cities(ax, d)


# ===========================================================================
# STANDALONE TEST
# ===========================================================================

def main():
    parser = argparse.ArgumentParser(description="Render a test basemap")
    D.add_deck_arguments(parser)
    parser.add_argument("--force", action="store_true",
                        help="Re-generate all layers")
    parser.add_argument("--force-hillshade", action="store_true",
                        help="Re-generate only the hillshade layer")
    parser.add_argument("--force-lakes", action="store_true",
                        help="Re-generate only the lakes layer")
    parser.add_argument("--force-rivers", action="store_true",
                        help="Re-generate only the rivers layer")
    args = parser.parse_args()
    d = D.get_deck(args.region, args.system)

    out = d.output_images_dir / "_test_basemap.webp"
    print(f"[BASEMAP] Generating test basemap for {d.title}...")
    generate_raster_basemap(
        d, out,
        force=args.force,
        force_hillshade=args.force_hillshade,
        force_lakes=args.force_lakes,
        force_rivers=args.force_rivers,
    )
    print(f"[BASEMAP] Saved: {out}")


if __name__ == "__main__":
    main()
