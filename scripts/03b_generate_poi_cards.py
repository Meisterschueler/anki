"""
03b_generate_poi_cards.py — Generate card images for POI decks
===============================================================
Creates WebP map images for point-of-interest (peaks, passes, towns, valleys).

All images are WebP.  Two modes:
  basemap  — opaque, lossy  (shared raster background)
  overlay  — transparent, lossless  (all vector layers above the basemap)

Images generated per deck:
  1. Partition map (Einteilung) — all POIs coloured by category  [overlay]
  2. Context layer — borders + cities                             [overlay]
  3. All-POIs overlay — all POI markers + small labels           [overlay]
  4. Per-POI highlight — red circle around target                 [overlay]
  5. Per-POI back — red circle (label shown via Anki HTML)        [overlay]

Templates:
  "Wo ist X?" — front: basemap + question label → back: basemap + all POIs + highlight
  "Was ist das?" — front: basemap + all POIs + highlight → back: target name

Usage:
    python scripts/03b_generate_poi_cards.py --region ostalpen --system pois [--force]
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.path as mpath
import cartopy.crs as ccrs
import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
import deck as D
from deck import POIDeck
from models import POI

# Import basemap module
sys.path.insert(0, str(Path(__file__).parent))
from importlib import import_module
_bm = import_module("02_generate_basemap")

create_figure = _bm.create_figure
render_full_basemap = _bm.render_full_basemap
generate_raster_basemap = _bm.generate_raster_basemap
generate_raster_basemap_rot = _bm.generate_raster_basemap_rot
crop_basemap_from_parent = _bm.crop_basemap_from_parent
_compute_pixel_dims = _bm._compute_pixel_dims
_draw_compass_needle = _bm._draw_compass_needle
_resolve_osm_file = _bm._resolve_osm_file
render_country_borders = _bm.render_country_borders
render_cities = _bm.render_cities

# Shared save + context helpers (lives in render_utils, NOT in 03)
from render_utils import save_figure, generate_context


def _generate_basemap(d, force: bool = False) -> None:
    """Generate basemap + rotated basemap for POI decks.

    basemap_rot uses a different hillshade azimuth so that the terrain
    lighting always appears consistent regardless of map orientation.
    """
    basemap_path = d.output_images_dir / d.filename_basemap()
    generate_raster_basemap(d, basemap_path, force=force)
    basemap_rot_path = d.output_images_dir / d.filename_basemap_rot()
    generate_raster_basemap_rot(d, basemap_rot_path, force=force)


# ─── Custom path markers ──────────────────────────────────────────────────────

def _bracket_outward(arm_h=0.40, arm_w=0.20, gap=0.10, lw=0.09):
    """'][ ' shape: two outward-facing brackets (Pass symbol)."""
    def _rect(x0, y0, w, h):
        return ([(x0, y0), (x0+w, y0), (x0+w, y0+h), (x0, y0+h), (x0, y0)],
                [mpath.Path.MOVETO, mpath.Path.LINETO, mpath.Path.LINETO,
                 mpath.Path.LINETO, mpath.Path.CLOSEPOLY])
    all_v, all_c = [], []
    for sign in (+1, -1):
        x = sign * gap
        v, c = _rect(x - lw/2, -arm_h, lw, arm_h * 2)
        all_v += v; all_c += c
        arm_x0 = x if sign > 0 else x - arm_w
        for ay in (arm_h - lw, -arm_h):
            v, c = _rect(arm_x0, ay, arm_w, lw)
            all_v += v; all_c += c
    return mpath.Path(all_v, all_c)


def _v_notch_circle(v_half_angle_deg=25, tip_y=-0.15):
    """Filled circle with V-notch cutout at top (Tal/Valley symbol)."""
    theta_left  = np.radians(90 + v_half_angle_deg)
    theta_right = np.radians(90 - v_half_angle_deg)
    n_arc = 80
    arc_angles = np.linspace(theta_right, theta_left - 2 * np.pi, n_arc)
    arc_x = np.cos(arc_angles)
    arc_y = np.sin(arc_angles)
    verts = (list(zip(arc_x, arc_y))
             + [(0.0, tip_y), (arc_x[0], arc_y[0])])
    codes = ([mpath.Path.MOVETO]
             + [mpath.Path.LINETO] * (n_arc - 1)
             + [mpath.Path.LINETO, mpath.Path.CLOSEPOLY])
    return mpath.Path(verts, codes)


def _lake_two_waves(n=60, x_extent=0.80, periods=2.5, amp=0.18, dy=0.22):
    """Two parallel sine waves inside a unit circle (See/Lake symbol, Variant B).

    Returns an open-polyline Path (no fill) to be rendered as edge strokes.
    Boundary MOVETO points at ±1.0 anchor the bounding box to match the
    'o' circle marker so both markers stay the same visual size.
    """
    t = np.linspace(-x_extent, x_extent, n)
    wave1_y =  dy + np.sin(t / x_extent * periods * np.pi) * amp
    wave2_y = -dy + np.sin(t / x_extent * periods * np.pi) * amp
    # Invisible boundary points force bounding-box to [-1,1]×[-1,1]
    bounds = [(-1.0, -1.0), (1.0, -1.0), (-1.0, 1.0), (1.0, 1.0)]
    verts = (bounds
             + list(zip(t, wave1_y))
             + list(zip(t, wave2_y)))
    codes = ([mpath.Path.MOVETO] * 4
             + [mpath.Path.MOVETO] + [mpath.Path.LINETO] * (n - 1)
             + [mpath.Path.MOVETO] + [mpath.Path.LINETO] * (n - 1))
    return mpath.Path(verts, codes)


def _airstrip_bar(r=1.0, extend_frac=0.25, bar_w=0.09):
    """Thin vertical rectangle representing a runway bar (Flugplatz symbol).

    Extends *extend_frac* × r beyond the circle edge on each side, so total
    half-length = r * (1 + extend_frac).  Rendered as pass 1; a white circle
    with black edge is drawn on top as pass 2.
    """
    y_ext = r * (1 + extend_frac)
    xl, xr = -bar_w / 2, bar_w / 2
    verts = [(xl, -y_ext), (xr, -y_ext), (xr, y_ext), (xl, y_ext), (xl, -y_ext)]
    codes = [mpath.Path.MOVETO, mpath.Path.LINETO, mpath.Path.LINETO,
             mpath.Path.LINETO, mpath.Path.CLOSEPOLY]
    return mpath.Path(verts, codes)


# Pre-built path markers (module-level, created once)
_PASS_PATH     = _bracket_outward(arm_h=0.40, arm_w=0.20, gap=0.10, lw=0.09)
_VALLEY_PATH   = _v_notch_circle(v_half_angle_deg=25, tip_y=-0.15)
_LAKE_PATH     = _lake_two_waves()
_AIRSTRIP_BAR  = _airstrip_bar(r=1.0, extend_frac=0.5, bar_w=0.5)


# ─── Valley polygon cache ─────────────────────────────────────────────────────

_VALLEY_POLY_CACHE: dict = {}          # geojson-path → {name: shapely polygon}
_VALLEY_BUFFER_M = 1000                # 1 km buffer around line geometries


def _get_valley_polygons(d: POIDeck) -> dict:
    """Load and cache 1 km–buffered valley polygons for *d*'s region."""
    key = str(d.region.osm_valleys_geojson)
    if key not in _VALLEY_POLY_CACHE:
        polygons: dict = {}
        path = _resolve_osm_file(d.region.osm_valleys_geojson)
        if path.exists():
            import geopandas as gpd
            gdf = gpd.read_file(path)
            gdf_metric = gdf.to_crs(epsg=3035)
            gdf_metric["geometry"] = gdf_metric.geometry.buffer(_VALLEY_BUFFER_M)
            gdf_buf = gdf_metric.to_crs(epsg=4326)
            for _, row in gdf_buf.iterrows():
                name = row.get("name", "")
                if name:
                    polygons[name] = row.geometry
            print(f"[VALLEY] Loaded {len(polygons)} buffered valley polygons")
        else:
            print(f"[VALLEY] WARN: Valleys GeoJSON not found: {key}")
        _VALLEY_POLY_CACHE[key] = polygons
    return _VALLEY_POLY_CACHE[key]


def _match_valley_polygon(poi: POI, valley_polys: dict):
    """Find the buffered polygon for a valley POI (exact → word-boundary match)."""
    if poi.name in valley_polys:
        return valley_polys[poi.name]
    # Word-boundary fallback (e.g. "Vinschgau" matches "Vinschgau - Val Venosta")
    import re
    pattern = re.compile(r'\b' + re.escape(poi.name), re.IGNORECASE)
    for name, poly in valley_polys.items():
        if pattern.search(name):
            return poly
    return None


def _render_valley_area(ax, polygon, color: str, alpha: float = 0.35,
                        linewidth: float = 1.0, zorder: int = 10):
    """Render a valley polygon as a semi-transparent filled area."""
    import matplotlib.colors as mcolors
    r, g, b, _ = mcolors.to_rgba(color)
    ax.add_geometries(
        [polygon], crs=ccrs.PlateCarree(),
        facecolor=(r, g, b, alpha),
        edgecolor=(r, g, b, min(1.0, alpha + 0.4)),
        linewidth=linewidth,
        zorder=zorder,
    )


# ─── POI Rendering ───────────────────────────────────────────────────────────

def _render_poi_marker(ax, poi: POI, style: dict, zorder: int = 10,
                       size_scale: float = 1.0, alpha: float = 1.0,
                       valley_polygon=None):
    """Render a single POI marker on the map.

    If *valley_polygon* is given (and the POI is a valley), the polygon
    is drawn as a filled area instead of a point marker.
    Airstrips with a heading get a circle + rotated line marker.
    """
    if valley_polygon is not None and poi.category == "valley":
        _render_valley_area(ax, valley_polygon, style["color"],
                            alpha=0.35 * alpha, zorder=zorder)
        return

    # Letter-badge: white circle with thin black border + bold category letter
    letter = style.get("letter")
    if letter:
        sz = style["size"] * size_scale
        ax.plot(
            poi.lon, poi.lat,
            marker="o",
            color="white",
            markeredgecolor="black",
            markeredgewidth=0.5 * size_scale,
            markersize=sz,
            transform=ccrs.PlateCarree(),
            zorder=zorder,
            alpha=alpha,
        )
        ax.text(
            poi.lon, poi.lat,
            letter,
            color=style["color"],
            fontsize=sz * 0.52,
            fontweight="bold",
            fontstyle="normal",
            ha="center", va="center_baseline",
            transform=ccrs.PlateCarree(),
            zorder=zorder + 1,
            alpha=alpha,
        )
        return

    # Pass: outward-bracket '][ ' path marker
    if poi.category == "pass":
        ax.plot(
            poi.lon, poi.lat,
            marker=_PASS_PATH,
            color=style["color"],
            markersize=style["size"] * size_scale,
            markeredgewidth=0,
            transform=ccrs.PlateCarree(),
            zorder=zorder,
            alpha=alpha,
        )
        return

    # Valley (no polygon): V-notch circle path marker
    if poi.category == "valley":
        ax.plot(
            poi.lon, poi.lat,
            marker=_VALLEY_PATH,
            color=style["color"],
            markersize=style["size"] * size_scale,
            markeredgewidth=0,
            transform=ccrs.PlateCarree(),
            zorder=zorder,
            alpha=alpha,
        )
        return

    # Lake: white circle with black edge + two parallel blue waves (Variant B)
    if poi.category == "lake":
        sz = style["size"] * size_scale
        # Pass 1 – white circle with black edge (same as cat A/B base)
        ax.plot(
            poi.lon, poi.lat,
            marker="o",
            color="white",
            markersize=sz,
            markeredgecolor="black",
            markeredgewidth=0.5 * size_scale,
            transform=ccrs.PlateCarree(),
            zorder=zorder,
            alpha=alpha,
        )
        # Pass 2 – two blue wave lines (open path, no fill)
        ax.plot(
            poi.lon, poi.lat,
            marker=_LAKE_PATH,
            color="none",
            markersize=sz,
            markeredgecolor=style["color"],
            markeredgewidth=0.7 * size_scale,
            transform=ccrs.PlateCarree(),
            zorder=zorder + 1,
            alpha=alpha,
        )
        return

    # Airstrip: black runway bar (rotated to heading) + white circle with black edge on top
    if poi.category == "airstrip":
        from matplotlib.markers import MarkerStyle
        from matplotlib.transforms import Affine2D
        heading = getattr(poi, 'heading', None) or 0
        # heading 0° = North → bar is vertical; rotate_deg is CCW so negate
        t = Affine2D().rotate_deg(-heading)
        bar_marker = MarkerStyle(_AIRSTRIP_BAR, transform=t)
        sz = style["size"] * size_scale
        # Pass 1 – black runway bar (markersize 1.5× so bar protrudes r/2 beyond circle)
        ax.plot(
            poi.lon, poi.lat,
            marker=bar_marker,
            color="black",
            markersize=sz * 1.5,
            markeredgewidth=0,
            transform=ccrs.PlateCarree(),
            zorder=zorder,
            alpha=alpha,
        )
        # Pass 2 – white circle with black edge (sz matches cat A/B circle size)
        ax.plot(
            poi.lon, poi.lat,
            marker="o",
            color="white",
            markeredgecolor="black",
            markeredgewidth=0.5 * size_scale,
            markersize=sz,
            transform=ccrs.PlateCarree(),
            zorder=zorder + 1,
            alpha=alpha,
        )
        return

    ax.plot(
        poi.lon, poi.lat,
        marker=style["marker"],
        color=style["color"],
        markersize=style["size"] * size_scale,
        markeredgecolor="white",
        markeredgewidth=0.3 * size_scale,
        transform=ccrs.PlateCarree(),
        zorder=zorder,
        alpha=alpha,
    )


def render_all_pois(ax, d: POIDeck, label_fontsize: float = 4.0,
                    label_alpha: float = 0.7, skip_poi_id: Optional[str] = None,
                    pois=None):
    """Render all POI markers with optional small labels."""
    valley_polys = _get_valley_polygons(d)
    for poi in (pois if pois is not None else d.pois):
        if poi.poi_id == skip_poi_id:
            continue
        style = d.category_style.get(poi.category, {})
        vpoly = _match_valley_polygon(poi, valley_polys) if poi.category == "valley" else None
        _render_poi_marker(ax, poi, style, zorder=10, valley_polygon=vpoly)

        # Small label (visible when zoomed in)
        display_name = poi.name
        if poi.elevation:
            display_name += f"\n{poi.elevation}m"

        ax.text(
            poi.lon + 0.03, poi.lat + 0.02,
            display_name,
            fontsize=label_fontsize,
            fontweight="normal",
            color=style.get("color", "#333333"),
            alpha=label_alpha,
            ha="left", va="bottom",
            transform=ccrs.PlateCarree(),
            zorder=11,
            bbox=dict(boxstyle="round,pad=0.15", facecolor="white",
                      edgecolor="none", alpha=0.5 * label_alpha),
        )


# Fraction of latitude-span used as highlight circle radius.
# Calibrated on the ostalpen full region (0.08° / 3.42° extent).
_HIGHLIGHT_RADIUS_FRAC = 0.08 / 3.42


def render_poi_highlight(ax, poi: POI, d: POIDeck):
    """Render a red highlight around a target POI.

    For valleys with a GeoJSON polygon the buffered polygon is drawn.
    For all other POIs an extent-scaled Ellipse is drawn so that the
    highlight circle has the same *pixel* size regardless of zoom level
    (full region vs sub-region).
    """
    # ── Valley: polygon highlight ─────────────────────────────────────
    if poi.category == "valley":
        valley_polys = _get_valley_polygons(d)
        vpoly = _match_valley_polygon(poi, valley_polys)
        if vpoly is not None:
            ax.add_geometries(
                [vpoly], crs=ccrs.PlateCarree(),
                facecolor=(0.8, 0.0, 0.0, 0.15),
                edgecolor="#CC0000",
                linewidth=2.5,
                zorder=15,
            )
            return

    # ── Circle: scaled to map extent ──────────────────────────────────
    import math
    lat_span = d.bbox_north - d.bbox_south
    radius_deg = _HIGHLIGHT_RADIUS_FRAC * lat_span
    lat_correction = 1.0 / math.cos(math.radians(poi.lat))
    circle = mpatches.Ellipse(
        (poi.lon, poi.lat),
        width=radius_deg * 2 * lat_correction,
        height=radius_deg * 2,
        transform=ccrs.PlateCarree(),
        facecolor="none",
        edgecolor="#CC0000",
        linewidth=2.5,
        linestyle="-",
        zorder=15,
    )
    ax.add_patch(circle)


def render_poi_label(ax, poi: POI, style: dict, fontsize: float = 10):
    """Render a prominent label for the target POI."""
    # Marker (larger)
    _render_poi_marker(ax, poi, style, zorder=16, size_scale=1.8)

    # Label text
    name_line = poi.name
    if poi.subtitle:
        name_line += f" ({poi.subtitle})"
    info_parts = []
    if poi.elevation:
        info_parts.append(f"{poi.elevation} m")
    info_line = " · ".join(info_parts)

    label = name_line
    if info_line:
        label += f"\n{info_line}"

    ax.text(
        poi.lon + 0.05, poi.lat + 0.04,
        label,
        fontsize=fontsize,
        fontweight="bold",
        color="#CC0000",
        ha="left", va="bottom",
        transform=ccrs.PlateCarree(),
        zorder=17,
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                  edgecolor="#CC0000", linewidth=1.0, alpha=0.9),
    )


def render_poi_question(ax, poi: POI, d: POIDeck, fontsize: float = 11):
    """Render a question label for 'Wo ist X?' template."""
    style = d.category_style.get(poi.category, {})
    cat_label = style.get("label", poi.category)

    name_line = poi.name
    if poi.subtitle:
        name_line += f" ({poi.subtitle})"
    info_parts = [cat_label]
    if poi.elevation:
        info_parts.append(f"{poi.elevation} m")
    info_line = " · ".join(info_parts)

    # Render as title box at top
    ax.text(
        0.5, 0.96,
        f"Wo ist: {name_line}?",
        transform=ax.transAxes,
        ha="center", va="top",
        fontsize=fontsize,
        fontweight="bold",
        color="#CC0000",
        zorder=21,
        bbox=dict(boxstyle="round,pad=0.4", facecolor="white",
                  edgecolor="#CC0000", linewidth=1.2, alpha=0.95),
    )
    ax.text(
        0.5, 0.96,
        f"\n{info_line}",
        transform=ax.transAxes,
        ha="center", va="top",
        fontsize=8,
        fontweight="normal",
        color="#666666",
        zorder=21,
        linespacing=2.5,
    )


# Preferred ordering of categories in the map legend.
_CATEGORY_LEGEND_ORDER = [
    "peak", "pass", "town", "valley", "lake",
    "landefeld_a", "landefeld_b", "airstrip",
]


def render_legend(ax, d: POIDeck):
    """Render a small legend showing category symbols."""
    handles = []
    for cat in _CATEGORY_LEGEND_ORDER:
        style = d.category_style.get(cat)
        if not style:
            continue
        count = len(d.pois_by_category(cat))
        if count == 0:
            continue
        if style.get("letter"):
            handles.append(plt.Line2D(
                [0], [0],
                marker="o",
                color="w",
                markerfacecolor="white",
                markeredgecolor="black",
                markeredgewidth=0.5,
                markersize=style["size"],
                label=f"{style['letter']}  {style.get('label', cat)} ({count})",
            ))
        else:
            handles.append(plt.Line2D(
                [0], [0],
                marker=style["marker"],
                color="w",
                markerfacecolor=style["color"],
                markeredgecolor="white",
                markersize=style["size"],
                label=f"{style.get('label', cat)} ({count})",
            ))
    if handles:
        ax.legend(
            handles=handles,
            loc="lower right",
            fontsize=6,
            framealpha=0.85,
            edgecolor="#cccccc",
            borderpad=0.5,
        )


# ─── Card Generation Functions ───────────────────────────────────────────────

def generate_partition(d: POIDeck, output_path) -> None:
    """Partition map (Einteilung): all POIs coloured by category with legend."""
    fig, ax = create_figure(d)
    render_full_basemap(ax, d, svg_mode=False, overlay_mode=True,
                        rivers=False, lakes=False)
    render_all_pois(ax, d, label_fontsize=4.0, label_alpha=0.6)
    render_legend(ax, d)
    save_figure(fig, output_path, overlay=True)
    plt.close(fig)


def generate_all_pois_overlay(d: POIDeck, output_path, pois=None) -> None:
    """Shared overlay with all POI markers + small labels (transparent bg)."""
    fig, ax = create_figure(d)
    ax.set_facecolor("none")
    ax.patch.set_alpha(0.0)
    render_all_pois(ax, d, label_fontsize=3.5, label_alpha=0.5, pois=pois)
    save_figure(fig, output_path, overlay=True)
    plt.close(fig)


# ─── Fast PIL-based overlay helpers ─────────────────────────────────────────
#
# Bypasses matplotlib figure rendering for highlight/back overlays.
# Each overlay is just a red ellipse + optionally a small marker sprite on a
# transparent RGBA canvas.  Saving the canvas as lossless WebP is still the
# primary cost (~0.25 s) but the matplotlib savefig step (~0.40 s) is avoided.
#
# Speedup: ~3× vs the matplotlib-per-POI approach.

def _poi_geo_to_px(d: POIDeck, lon: float, lat: float):
    """Convert geographic coordinates to pixel position for the deck's canvas."""
    import math
    w, h = _compute_pixel_dims(d)
    x = (lon - d.bbox_west)  / (d.bbox_east  - d.bbox_west)  * w
    y = (d.bbox_north - lat) / (d.bbox_north - d.bbox_south) * h
    return x, y, w, h


def _highlight_ellipse_params(d: POIDeck, poi: POI):
    """Return (cx, cy, rx, ry, lw_px, canvas_w, canvas_h) for the red circle.

    rx and ry are derived so that the ellipse appears as a circle when the
    basemap is displayed at its natural (cos-corrected) aspect ratio.

    The basemap width covers lon_span degrees at w pixels, so:
        rx = radius_deg * w / (lon_span * cos(lat))
    The basemap height covers lat_span degrees at h pixels, so:
        ry = radius_deg * h / lat_span
    These are equal at mid_lat (where w/h = lon_span*cos(mid_lat)/lat_span),
    giving a visual circle for POIs near the map centre.
    """
    import math
    cx, cy, w, h = _poi_geo_to_px(d, poi.lon, poi.lat)
    lon_span   = d.bbox_east  - d.bbox_west
    lat_span   = d.bbox_north - d.bbox_south
    radius_deg = _HIGHLIGHT_RADIUS_FRAC * lat_span
    ry = radius_deg / lat_span * h
    rx = radius_deg * w / (lon_span * math.cos(math.radians(poi.lat)))
    lw = max(2, int(ry * 0.09))
    return cx, cy, rx, ry, lw, w, h


# Cache of pre-rendered marker sprites: category_key → PIL RGBA Image
_MARKER_SPRITE_CACHE: dict = {}

def _get_marker_sprite(d: POIDeck, category: str) -> "PIL.Image.Image | None":
    """Return a small RGBA PIL sprite of the POI marker for *category*.

    Rendered once per (deck-title, category) pair and cached in memory.
    """
    import io as _io
    from PIL import Image as _PIL

    key = (id(d.category_style), category)
    if key in _MARKER_SPRITE_CACHE:
        return _MARKER_SPRITE_CACHE[key]

    style = d.category_style.get(category)
    if not style:
        _MARKER_SPRITE_CACHE[key] = None
        return None

    # Sprite size: markersize in pt × (DPI/72) pixels, plus padding
    import deck as _D
    sz_pt = style.get("size", 10)
    sz_px = int(sz_pt * (_D.FIGURE_DPI / 72) * 1.6)
    sz_px = max(sz_px, 10)

    # Build a tiny figure with a single marker centred on (0.5, 0.5).
    # Use add_axes([0,0,1,1]) so the axes fills the figure with zero margins —
    # plt.subplots() leaves default subplot padding (~12 % on each side) which
    # shifts the marker ~1 px off-centre in the saved sprite.
    fig_s = plt.figure(figsize=(sz_px / _D.FIGURE_DPI, sz_px / _D.FIGURE_DPI),
                       dpi=_D.FIGURE_DPI)
    ax_s = fig_s.add_axes([0, 0, 1, 1])
    ax_s.set_xlim(0, 1); ax_s.set_ylim(0, 1)
    ax_s.set_aspect("equal"); ax_s.axis("off")
    ax_s.set_facecolor("none"); fig_s.patch.set_alpha(0.0)

    # Create a dummy POI at (0.5, 0.5) in data coords
    from types import SimpleNamespace
    fake_poi = SimpleNamespace(lon=0.5, lat=0.5, heading=None,
                               category=category, subtitle=None)

    # Render using plain ax.plot (not _render_poi_marker which uses PlateCarree)
    letter = style.get("letter")
    if letter:
        ax_s.plot(0.5, 0.5, marker="o", color="white",
                  markeredgecolor="black", markeredgewidth=0.5,
                  markersize=sz_pt, linewidth=0)
        ax_s.text(0.5, 0.5, letter, color=style["color"],
                  fontsize=sz_pt * 0.52, fontweight="bold",
                  ha="center", va="center_baseline")
    elif category == "pass":
        ax_s.plot(0.5, 0.5, marker=_PASS_PATH, color=style["color"],
                  markersize=sz_pt, markeredgewidth=0, linewidth=0)
    elif category == "valley":
        ax_s.plot(0.5, 0.5, marker=_VALLEY_PATH, color=style["color"],
                  markersize=sz_pt, markeredgewidth=0, linewidth=0)
    elif category == "lake":
        # Pass 1 – white circle with black edge
        ax_s.plot(0.5, 0.5, marker="o", color="white",
                  markeredgecolor="black", markeredgewidth=0.5,
                  markersize=sz_pt, linewidth=0)
        # Pass 2 – two blue wave lines (open path, no fill)
        ax_s.plot(0.5, 0.5, marker=_LAKE_PATH, color="none",
                  markeredgecolor=style["color"], markeredgewidth=0.7,
                  markersize=sz_pt, linewidth=0)
    elif category == "airstrip":
        # Pass 1 – black runway bar (1.5× markersize so bar protrudes r/2 beyond circle)
        ax_s.plot(0.5, 0.5, marker=_AIRSTRIP_BAR, color="black",
                  markersize=sz_pt * 1.5, markeredgewidth=0, linewidth=0)
        # Pass 2 – white circle with black edge (sz matches cat A/B)
        ax_s.plot(0.5, 0.5, marker="o", color="white",
                  markeredgecolor="black", markeredgewidth=0.5,
                  markersize=sz_pt, linewidth=0)
    else:
        ax_s.plot(0.5, 0.5, marker=style.get("marker", "o"),
                  color=style["color"],
                  markersize=sz_pt,
                  markeredgecolor="white", markeredgewidth=0.3,
                  linewidth=0)

    buf = _io.BytesIO()
    fig_s.savefig(buf, format="png", dpi=_D.FIGURE_DPI,
                  pad_inches=0, transparent=True)
    plt.close(fig_s)
    buf.seek(0)
    sprite = _PIL.open(buf).copy()
    _MARKER_SPRITE_CACHE[key] = sprite
    return sprite


def _save_pil_overlay(img, output_path) -> None:
    """Save PIL RGBA image as lossless WebP."""
    from pathlib import Path as _Path
    out = _Path(output_path).with_suffix(".webp")
    img.save(str(out), "WEBP", lossless=True)


def _draw_highlight_on_image(img, d: POIDeck, poi: POI) -> None:
    """Draw red highlight ellipse directly onto a PIL RGBA image."""
    from PIL import ImageDraw as _Draw
    cx, cy, rx, ry, lw, _w, _h = _highlight_ellipse_params(d, poi)
    draw = _Draw.Draw(img)
    draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry],
                 outline=(204, 0, 0, 255), width=lw)


def _make_highlight_image_pil(d: POIDeck, poi: POI):
    """Create a blank transparent RGBA canvas with the red highlight circle."""
    from PIL import Image as _PIL
    _, _, _rx, _ry, _lw, w, h = _highlight_ellipse_params(d, poi)
    img = _PIL.new("RGBA", (w, h), (0, 0, 0, 0))
    _draw_highlight_on_image(img, d, poi)
    return img


def _make_highlight_sprite(d: POIDeck, poi: POI, with_symbol: bool = False):
    """Create a small RGBA sprite containing only the highlight ellipse area.

    Much faster to save than a full-canvas image (~17ms vs ~250ms).

    Returns:
        (sprite_img, left_pct, top_pct, width_pct, height_pct) where the CSS
        percentages describe where to position the sprite over the full map canvas.
    """
    from PIL import Image as _PIL, ImageDraw as _Draw

    cx, cy, rx, ry, lw, w, h = _highlight_ellipse_params(d, poi)

    # Padding around ellipse (at least lw*2 so the stroke is fully included)
    pad = max(int(lw * 2), 6)

    # Sprite bounding box in canvas coordinates (clamped to canvas)
    x0 = max(0, int(cx - rx) - pad)
    y0 = max(0, int(cy - ry) - pad)
    x1 = min(w, int(cx + rx) + pad + 1)
    y1 = min(h, int(cy + ry) + pad + 1)
    sw = x1 - x0
    sh = y1 - y0

    # Draw ellipse on sprite canvas (coordinates offset by top-left corner)
    img = _PIL.new("RGBA", (sw, sh), (0, 0, 0, 0))
    draw = _Draw.Draw(img)
    draw.ellipse(
        [cx - rx - x0, cy - ry - y0, cx + rx - x0, cy + ry - y0],
        outline=(204, 0, 0, 255), width=lw,
    )

    # Optionally paste the category marker sprite in the centre
    if with_symbol:
        marker = _get_marker_sprite(d, poi.category)
        if marker is not None:
            ox = int(cx - marker.width  / 2) - x0
            oy = int(cy - marker.height / 2) - y0
            img.paste(marker, (ox, oy), marker)

    # CSS percentage position relative to the full canvas
    left_pct   = x0 / w * 100
    top_pct    = y0 / h * 100
    width_pct  = sw / w * 100
    height_pct = sh / h * 100

    return img, left_pct, top_pct, width_pct, height_pct


def _save_sprite_overlay(img, output_path, left_pct, top_pct, width_pct, height_pct) -> None:
    """Save sprite as lossless WebP and write a JSON sidecar with CSS position.

    The JSON is read by 04_build_deck.py to generate positioned <img> tags
    without requiring extra Anki note fields.
    """
    import json as _json
    from pathlib import Path as _Path

    out = _Path(output_path).with_suffix(".webp")
    img.save(str(out), "WEBP", lossless=True)

    meta = {
        "left_pct":   round(left_pct,   6),
        "top_pct":    round(top_pct,    6),
        "width_pct":  round(width_pct,  6),
        "height_pct": round(height_pct, 6),
    }
    _Path(out).with_suffix(".json").write_text(_json.dumps(meta))


def _highlight_sprite_position(d: "POIDeck", poi) -> tuple:
    """Compute highlight sprite CSS position without rendering any image.

    Returns (left_pct, top_pct, width_pct, height_pct) — the bounding box
    of the highlight ellipse as percentages of the full canvas.
    """
    cx, cy, rx, ry, lw, w, h = _highlight_ellipse_params(d, poi)
    pad = max(int(lw * 2), 6)
    x0 = max(0, int(cx - rx) - pad)
    y0 = max(0, int(cy - ry) - pad)
    x1 = min(w, int(cx + rx) + pad + 1)
    y1 = min(h, int(cy + ry) + pad + 1)
    return x0 / w * 100, y0 / h * 100, (x1 - x0) / w * 100, (y1 - y0) / h * 100


def _save_highlight_position_json(json_path, sprite_file,
                                  left_pct, top_pct, width_pct, height_pct,
                                  *, badge_box=None) -> None:
    """Write a JSON sidecar with CSS position + optional sprite filename.

    sprite_file: shared category sprite filename, or None for a full-canvas
                 per-POI overlay (e.g. valley polygon WebPs).
    badge_box:   optional (left, top, width, height) in percent for the back
                 overlay badge.  Required when the highlight covers the full
                 canvas (left=0, top=0, width=100, height=100) so the badge
                 is still placed at a meaningful position.
    """
    import json as _json
    from pathlib import Path as _Path
    meta = {
        "left_pct":    round(left_pct,   6),
        "top_pct":     round(top_pct,    6),
        "width_pct":   round(width_pct,  6),
        "height_pct":  round(height_pct, 6),
    }
    if sprite_file is not None:
        meta["sprite_file"] = sprite_file
    if badge_box is not None:
        bl, bt, bw, bh = badge_box
        meta["badge_left_pct"]   = round(bl, 6)
        meta["badge_top_pct"]    = round(bt, 6)
        meta["badge_width_pct"]  = round(bw, 6)
        meta["badge_height_pct"] = round(bh, 6)
    _Path(json_path).write_text(_json.dumps(meta))


# ─── Overlay-only functions (for Anki CSS compositing) ───────────────────────

def generate_poi_highlight_overlay(d: POIDeck, poi: POI, output_path) -> None:
    """Overlay: red highlight circle on transparent background (standalone)."""
    fig, ax = create_figure(d)
    ax.set_facecolor("none")
    ax.patch.set_alpha(0.0)
    render_poi_highlight(ax, poi, d)
    save_figure(fig, output_path, overlay=True)
    plt.close(fig)


def generate_poi_back_overlay(d: POIDeck, poi: POI, output_path) -> None:
    """Overlay: red highlight circle + POI symbol centred inside it (standalone)."""
    fig, ax = create_figure(d)
    ax.set_facecolor("none")
    ax.patch.set_alpha(0.0)
    render_poi_highlight(ax, poi, d)
    style = d.category_style.get(poi.category, {})
    if style:
        _render_poi_marker(ax, poi, style, zorder=16, size_scale=1.0)
    save_figure(fig, output_path, overlay=True)
    plt.close(fig)


# ─── AVE 84 context back overlay (for Gipfel / Pässe / Seen sub-decks) ───────

def generate_ave84_poi_back_overlay(d: POIDeck, poi: POI, output_path) -> None:
    """Overlay: the AVE 84 Gebirgsgruppe(n) that contain/touch the POI.

    Used as the ``BackOverlay`` for the merged Gipfel / Pässe / Seen
    sub-decks so learners can see which mountain group the POI belongs to.

    The containing group is filled with its AVE 84 colour at full alpha;
    adjacent groups that the POI lies on the boundary of are shown at
    lower alpha.  The highlight ring is also rendered so the POI location
    is visible.
    """
    import json as _json
    from pathlib import Path as _Path
    try:
        from shapely.geometry import Point as _Point, shape as _shape
    except ImportError:
        print("[WARN] shapely not available — falling back to plain highlight overlay")
        generate_poi_back_overlay(d, poi, output_path)
        return

    import importlib as _il
    import cartopy.crs as ccrs

    ave84_path = _Path(__file__).parent.parent / "data" / "osm" / "ostalpen_ave84.geojson"
    if not ave84_path.exists():
        print(f"[WARN] AVE 84 GeoJSON not found: {ave84_path} — falling back")
        generate_poi_back_overlay(d, poi, output_path)
        return

    ave84_data = _json.loads(ave84_path.read_text(encoding="utf-8"))

    try:
        ave84_mod = _il.import_module("classifications.ave84")
        ave84_colors = ave84_mod.CLASSIFICATION.colors
        ave84_by_ref = {g.osm_ref: g for g in ave84_mod.CLASSIFICATION.groups}
    except Exception as e:
        print(f"[WARN] Could not load AVE 84 classification ({e}) — falling back")
        generate_poi_back_overlay(d, poi, output_path)
        return

    poi_point = _Point(poi.lon, poi.lat)
    crs = ccrs.PlateCarree()

    fig, ax = create_figure(d)
    ax.set_facecolor("none")
    ax.patch.set_alpha(0.0)

    from cartopy.feature import ShapelyFeature

    for feat in ave84_data["features"]:
        geom = _shape(feat["geometry"])
        if not geom.intersects(poi_point.buffer(0.05)):  # ~5 km tolerance
            continue
        ave_ref = feat["properties"].get("ref:aveo", "")
        group_obj = ave84_by_ref.get(ave_ref)
        if group_obj is None:
            continue
        color_info = ave84_colors.get(group_obj.hauptgruppe, {})
        fill_color = color_info.get("fill", "#888888")
        alpha = 0.75 if geom.contains(poi_point) else 0.35
        feat_obj = ShapelyFeature(
            [geom], crs,
            facecolor=fill_color, edgecolor="#FFFFFF",
            linewidth=0.6, alpha=alpha, zorder=4,
        )
        ax.add_feature(feat_obj)

    # Add the highlight ring so the POI location is visible on the back
    render_poi_highlight(ax, poi, d)

    save_figure(fig, output_path, overlay=True)
    plt.close(fig)


def _clear_overlay_axes(ax) -> None:
    """Remove all drawn artists from a transparent overlay axes.

    Keeps the projection, extent and facecolor intact so the figure can
    be reused for the next POI without the expensive GeoAxes construction.
    """
    for artist_list in (ax.lines, ax.patches, ax.collections, ax.texts, ax.images):
        for a in list(artist_list):
            a.remove()


# ─── Batch Generation ────────────────────────────────────────────────────────

def generate_all(d: POIDeck, pois=None, force=False):
    """Generate basemap + per-POI WebP images (overlay mode only).

    Generates transparent overlays for Anki CSS compositing:
      context + all_pois + 1 badge per category + 1 highlight per POI.
    """
    if pois is None:
        pois = d.pois

    _generate_basemap(d, force=force)

    n_categories = len({poi.category for poi in pois})
    # context + all_pois + badges + 1 highlight sprite per category + 1 JSON per POI
    total = 2 + 2 * n_categories + len(pois)
    count = 0

    print(f"[POI-CARDS] Generating {total} overlay images for {d.title} …")

    # 1. Context overlay
    count += 1
    context_path = d.output_images_dir / d.filename_context()
    if force or not context_path.exists():
        print(f"  [{count}/{total}] Context overlay")
        generate_context(d, context_path)
    else:
        print(f"  [{count}/{total}] Skip (exists): {context_path.name}")

    # 2. All-POIs overlay
    count += 1
    all_pois_path = d.output_images_dir / d.filename_all_pois_overlay(".webp")
    if force or not all_pois_path.exists():
        print(f"  [{count}/{total}] All-POIs overlay")
        generate_all_pois_overlay(d, all_pois_path, pois=pois)
    else:
        print(f"  [{count}/{total}] Skip (exists): {all_pois_path.name}")

    # 3. Category badges (one per type, shared by all POIs of that category)
    for category in sorted({poi.category for poi in pois}):
        count += 1
        badge_path = d.output_images_dir / d.filename_category_badge(category, ".webp")
        if force or not badge_path.exists():
            print(f"  [{count}/{total}] Badge: {category}")
            sprite = _get_marker_sprite(d, category)
            if sprite is not None:
                badge_path.parent.mkdir(parents=True, exist_ok=True)
                sprite.save(str(badge_path), "WEBP", lossless=True)
                sprite.close()
        else:
            print(f"  [{count}/{total}] Skip (exists): {badge_path.name}")

    # 4a. Category highlight ring sprites — one shared image per category
    cat_hl_files: dict[str, str] = {}  # category → filename (for JSON reference)
    for category in sorted({poi.category for poi in pois}):
        count += 1
        hl_cat_file = d.filename_category_highlight(category, ".webp")
        hl_cat_path = d.output_images_dir / hl_cat_file
        cat_hl_files[category] = hl_cat_file
        if force or not hl_cat_path.exists():
            # Render using any POI of this category (ring size depends on
            # category style — minor lat distortion is negligible)
            sample_poi = next(p for p in pois if p.category == category)
            print(f"  [{count}/{total}] Highlight ring: {category}")
            hl_img, *_ = _make_highlight_sprite(d, sample_poi, with_symbol=False)
            hl_img.save(str(hl_cat_path), "WEBP", lossless=True)
            hl_img.close()
        else:
            print(f"  [{count}/{total}] Skip (exists): {hl_cat_path.name}")

    # 4b. Per-POI highlight images / position JSONs
    #
    # Valley POIs whose name matches the GeoJSON get a full-canvas matplotlib
    # polygon overlay (per-POI WebP).  All other POIs share the category ring
    # sprite and only write a small position JSON.
    valley_polys = _get_valley_polygons(d) if any(
        p.category == "valley" for p in pois
    ) else {}

    for poi in pois:
        count += 1
        hl_json_path = (d.output_images_dir
                        / d.filename_poi_highlight(poi.poi_id, ".json"))
        cat_label = d.category_style.get(poi.category, {}).get("label", poi.category)

        # Check for valley polygon match
        vpoly = None
        if poi.category == "valley" and valley_polys:
            vpoly = _match_valley_polygon(poi, valley_polys)

        if vpoly is not None:
            # Valley with polygon: generate per-POI matplotlib highlight WebP
            hl_webp_path = (d.output_images_dir
                            / d.filename_poi_highlight(poi.poi_id, ".webp"))
            if force or not hl_webp_path.exists():
                print(f"  [{count}/{total}] {cat_label} {poi.name} (polygon)")
                generate_poi_highlight_overlay(d, poi, hl_webp_path)
            else:
                print(f"  [{count}/{total}] Skip (exists): {hl_webp_path.name}")
            if force or not hl_json_path.exists():
                # Badge position from the regular ellipse ring (same ring size)
                bl, bt, bw, bh = _highlight_sprite_position(d, poi)
                # sprite_file=None → _poi_overlay_html falls back to per-POI WebP
                _save_highlight_position_json(
                    hl_json_path, None,
                    0.0, 0.0, 100.0, 100.0,
                    badge_box=(bl, bt, bw, bh),
                )
        else:
            if force or not hl_json_path.exists():
                print(f"  [{count}/{total}] {cat_label} {poi.name} (position)")
                lp, tp, wp, hp = _highlight_sprite_position(d, poi)
                _save_highlight_position_json(
                    hl_json_path, cat_hl_files[poi.category], lp, tp, wp, hp
                )
            else:
                print(f"  [{count}/{total}] Skip (exists): {hl_json_path.name}")

    # ── AVE 84 back overlays for Merkmale sub-decks ───────────────────────────
    # Systems gipfel / paesse / seen generate a per-POI "poi_back.webp" that
    # shows the containing AVE 84 Gebirgsgruppe so that the merged ave84 deck
    # can display it as the BackOverlay on the card back.
    _MERKMALE_SYSTEMS = {"gipfel", "paesse", "seen"}
    if d.poi_classification.name in _MERKMALE_SYSTEMS:
        print(f"\n[POI-CARDS] Generating AVE 84 back overlays for {d.poi_classification.name} …")
        for poi in pois:
            back_path = d.output_images_dir / d.filename_poi_back(poi.poi_id, ".webp")
            if force or not back_path.exists():
                print(f"  AVE84 back: {poi.name}")
                generate_ave84_poi_back_overlay(d, poi, back_path)
            else:
                print(f"  AVE84 back: Skip (exists): {back_path.name}")

    print(f"\n[POI-CARDS] Done. {total} overlay files in {d.output_images_dir}")


# ─── Sub-Region Support ──────────────────────────────────────────────────────

def generate_overview_thumbnail(
    parent_deck: POIDeck,
    sub_bbox: tuple,
    output_path: Path,
    force: bool = False,
) -> None:
    """Generate a small overview thumbnail of the full region with a red
    rectangle marking the sub-region extent.

    The thumbnail is placed in the bottom-right corner of sub-region cards
    so the user always knows where they are within the full Ostalpen map.

    Args:
        parent_deck: The full-region POI deck (for basemap + extent).
        sub_bbox: (west, east, south, north) of the sub-region.
        output_path: Where to save the thumbnail WebP.
        force: Overwrite if exists.
    """
    from PIL import Image, ImageDraw

    if not force and output_path.exists():
        print(f"[THUMB] cached: {output_path.name}")
        return

    # Load full-region basemap
    basemap_path = parent_deck.output_images_dir / parent_deck.filename_basemap()
    if not basemap_path.exists():
        _generate_basemap(parent_deck, force=False)
    if not basemap_path.exists():
        print(f"[THUMB] ERROR: Basemap not found: {basemap_path}")
        return

    img = Image.open(str(basemap_path)).convert("RGB")
    w, h = img.size

    # Map geo coords → pixel coords
    p_west = parent_deck.bbox_west
    p_east = parent_deck.bbox_east
    p_south = parent_deck.bbox_south
    p_north = parent_deck.bbox_north

    def geo_to_px(lon, lat):
        x = (lon - p_west) / (p_east - p_west) * w
        y = (p_north - lat) / (p_north - p_south) * h
        return x, y

    sub_west, sub_east, sub_south, sub_north = sub_bbox
    x0, y0 = geo_to_px(sub_west, sub_north)  # top-left
    x1, y1 = geo_to_px(sub_east, sub_south)  # bottom-right

    # Draw red rectangle on image
    draw = ImageDraw.Draw(img)
    line_w = max(3, int(min(w, h) * 0.004))
    draw.rectangle([x0, y0, x1, y1], outline="#CC0000", width=line_w)

    # Scale to thumbnail size (~18% of full basemap width, min 200px)
    thumb_w = max(200, int(w * 0.18))
    thumb_h = int(h * thumb_w / w)
    img = img.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)

    # Add border
    from PIL import ImageOps
    img = ImageOps.expand(img, border=2, fill="#666666")

    img.save(str(output_path), "WEBP", quality=85, method=6)
    print(f"[THUMB] Generated: {output_path.name} ({img.size[0]}x{img.size[1]})")


def generate_all_sub_regions(
    parent_deck: POIDeck,
    region_name: str,
    force: bool = False,
    only_key: Optional[str] = None,
) -> None:
    """Generate basemaps, overlays, and thumbnails for all sub-region decks.

    Args:
        parent_deck: The parent POIDeck whose output directory is shared.
        region_name: Name of the region (e.g. ``'ostalpen'``).
        force:       Overwrite existing files.
        only_key:    When set, generate only the sub-region with this key.
                     When ``None`` (default), generate all configured ones.
    """
    multi_cfg = D.POI_MULTI_DECK.get(f"{region_name}_pois")
    if not multi_cfg:
        return

    sub_region_entries = multi_cfg.get("sub_regions", [])
    sub_regions = D.SUB_REGIONS.get(region_name, [])
    sub_by_key = {s.key: s for s in sub_regions}

    for sub_key, sub_label in sub_region_entries:
        if only_key is not None and sub_key != only_key:
            continue
        sub = sub_by_key.get(sub_key)
        if sub is None:
            print(f"[SUB-REGION] WARN: Unknown sub-region {sub_key!r}")
            continue

        print(f"\n[SUB-REGION] === {sub_label} ({sub_key}) ===")

        # Build the sub-region POIDeck
        sub_deck = D.get_sub_region_poi_deck(region_name, sub_key)

        # Ensure sub-region basemap + basemap_rot exist.
        # Try normal pipeline first; fall back to cropping from parent when DEM unavailable.
        sub_bm_path = sub_deck.output_images_dir / sub_deck.filename_basemap()
        sub_bm_rot_path = sub_deck.output_images_dir / sub_deck.filename_basemap_rot()

        if sub_deck.region.dem_tif.exists():
            _generate_basemap(sub_deck, force=force)
        else:
            tw, th = _compute_pixel_dims(sub_deck)
            parent_ext = (parent_deck.bbox_west, parent_deck.bbox_east,
                          parent_deck.bbox_south, parent_deck.bbox_north)
            sub_ext = (sub_deck.bbox_west, sub_deck.bbox_east,
                       sub_deck.bbox_south, sub_deck.bbox_north)
            for fn_name, sub_path in [
                ("filename_basemap",     sub_bm_path),
                ("filename_basemap_rot", sub_bm_rot_path),
            ]:
                parent_bm = parent_deck.output_images_dir / getattr(parent_deck, fn_name)()
                crop_basemap_from_parent(
                    parent_bm, parent_ext, sub_ext,
                    sub_path, tw, th, force=force,
                )

        # Generate all overlay images for the sub-region deck
        # (skip basemap — already handled above)
        generate_all(sub_deck, force=force)

        # Generate overview thumbnail
        thumb_path = parent_deck.output_images_dir / \
            f"{parent_deck.prefix}_thumb_{sub_key}.webp"
        generate_overview_thumbnail(
            parent_deck,
            sub_bbox=(sub.bbox_west, sub.bbox_east, sub.bbox_south, sub.bbox_north),
            output_path=thumb_path,
            force=force,
        )


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate POI card images for Anki decks.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python scripts/03b_generate_poi_cards.py --region ostalpen\n"
            "  python scripts/03b_generate_poi_cards.py --region westalpen --force\n"
            "  python scripts/03b_generate_poi_cards.py --region ostalpen "
            "--ids peak_01,pass_03\n"
            "  python scripts/03b_generate_poi_cards.py --region ostalpen "
            "--sub-region koenigsdorf --force\n"
        ),
    )
    # poi_mode=True: --system defaults to 'pois', choices restricted to POI
    # systems, and --sub-region option is added automatically.
    D.add_deck_arguments(parser, poi_mode=True)
    parser.add_argument(
        "--ids", type=str,
        help="Comma-separated POI IDs to (re)generate in the main deck "
             "(e.g. peak_01,pass_03).  Sub-region generation is unaffected.",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Overwrite existing images and remove stale overlay files.",
    )
    args = parser.parse_args()

    d = D.get_deck(args.region, args.system)
    if not isinstance(d, POIDeck):
        # Guard: should not reach here when poi_mode restricts choices.
        print(f"[ERROR] '{args.system}' is not a POI deck. "
              f"Use 03_generate_cards.py instead.")
        sys.exit(1)

    # ── Sub-region exclusion ──────────────────────────────────────────────────
    # Always compute the set of POIs claimed by sub-regions so we never
    # render the same POI in both the main deck and a sub-region deck.
    sub_poi_ids = D.get_all_sub_region_poi_ids(args.region)

    # ── Determine which POIs to process in the main deck ──────────────────
    if args.ids:
        # Explicit selection — generate exactly the named POIs.
        requested = [pid.strip() for pid in args.ids.split(",")]
        main_pois = []
        for pid in requested:
            try:
                poi = d.poi_by_id(pid)
                if pid in sub_poi_ids:
                    print(
                        f"[WARN] POI {pid!r} ({poi.name}) belongs to a sub-region "
                        f"deck; regenerating in main deck anyway. "
                        f"Use --sub-region to regenerate the sub-region images."
                    )
                main_pois.append(poi)
            except KeyError:
                print(f"[WARN] Unknown POI ID: {pid!r}")
        main_pois = main_pois or None
    else:
        # Automatic — exclude POIs that live in sub-region decks.
        if sub_poi_ids:
            main_pois = [p for p in d.pois if p.poi_id not in sub_poi_ids]
            print(
                f"[POI-CARDS] Excluding {len(sub_poi_ids)} sub-region POIs "
                f"from main deck ({len(main_pois)} remaining)"
            )
        else:
            main_pois = None

    # ── --force pre-cleanup ──────────────────────────────────────────────────
    # Mirrors 03_generate_cards.py so stale files from renamed/removed POIs
    # are never left behind.
    if args.force and d.output_images_dir.exists():
        if args.ids:
            # Targeted cleanup: remove only the selected POIs' position JSONs.
            for poi in (main_pois or []):
                json_path = (
                    d.output_images_dir
                    / d.filename_poi_highlight(poi.poi_id, ".json")
                )
                if json_path.exists():
                    json_path.unlink()
        else:
            # Full cleanup: remove all overlay files except the basemaps.
            basemap_names = {d.filename_basemap(), d.filename_basemap_rot()}
            prefix = d.prefix
            for pattern in (
                f"{prefix}_badge_*.webp",
                f"{prefix}_highlight_*.webp",
                f"{prefix}_poi_*.json",
                f"{prefix}_partition.webp",
                f"{prefix}_context.webp",
                f"{prefix}_allpois.webp",
            ):
                for f in d.output_images_dir.glob(pattern):
                    if f.name not in basemap_names:
                        f.unlink()

    # ── Generate main deck images ───────────────────────────────────────────────
    generate_all(d, pois=main_pois, force=args.force)

    # ── Generate sub-region images ──────────────────────────────────────────────
    # Controlled by --sub-region (all / none / <key>), not by --ids.
    sub_region_mode = args.sub_region
    if sub_region_mode != "none":
        only_key = None if sub_region_mode == "all" else sub_region_mode
        generate_all_sub_regions(
            d, args.region, force=args.force, only_key=only_key
        )


if __name__ == "__main__":
    main()
