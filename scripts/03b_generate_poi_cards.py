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

# Import shared helpers from 03
_cards = import_module("03_generate_cards")
save_figure = _cards.save_figure
generate_context = _cards.generate_context
_generate_basemap = _cards._generate_basemap


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

    # Airstrip with heading: circle + rotated line indicating runway direction
    if poi.category == "airstrip" and getattr(poi, 'heading', None) is not None:
        from matplotlib.markers import MarkerStyle
        from matplotlib.transforms import Affine2D
        # Base circle
        ax.plot(
            poi.lon, poi.lat,
            marker="o",
            color=style["color"],
            markersize=style["size"] * size_scale,
            markeredgecolor="white",
            markeredgewidth=0.3 * size_scale,
            transform=ccrs.PlateCarree(),
            zorder=zorder,
            alpha=alpha,
        )
        # Heading line: "|" marker rotated to runway direction
        # heading 0° = North; rotate_deg expects CCW, so negate.
        t = Affine2D().rotate_deg(-poi.heading)
        heading_marker = MarkerStyle("|", transform=t)
        ax.plot(
            poi.lon, poi.lat,
            marker=heading_marker,
            color=style["color"],
            markersize=style["size"] * size_scale * 1.8,
            markeredgecolor=style["color"],
            markeredgewidth=0.8 * size_scale,
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


# ─── Overlay-only functions (for Anki CSS compositing) ───────────────────────

def generate_poi_highlight_overlay(d: POIDeck, poi: POI, output_path) -> None:
    """Overlay: red highlight circle on transparent background.

    Used for highlight and back overlays — composited with basemap +
    context + all_pois in Anki via CSS.  Label is shown in the HTML
    template, not burned into the image.
    """
    fig, ax = create_figure(d)
    ax.set_facecolor("none")
    ax.patch.set_alpha(0.0)
    render_poi_highlight(ax, poi, d)
    save_figure(fig, output_path, overlay=True)
    plt.close(fig)


# ─── Batch Generation ────────────────────────────────────────────────────────

def generate_all(d: POIDeck, pois=None, force=False):
    """Generate basemap + partition + per-POI WebP images (overlay mode only).

    Generates transparent overlays for Anki CSS compositing:
      context + all_pois + 2 per POI (highlight + back).
    """
    if pois is None:
        pois = d.pois

    _generate_basemap(d, force=force)

    # context + all_pois + 2 per POI (highlight + back)
    total = 2 + 2 * len(pois)
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

    # 3. Per-POI overlays
    for poi in pois:
        cat_label = d.category_style.get(poi.category, {}).get("label", poi.category)

        # Highlight overlay (for Template 2 front: "Was ist das?")
        count += 1
        hl_path = d.output_images_dir / d.filename_poi_highlight(poi.poi_id, ".webp")
        if force or not hl_path.exists():
            print(f"  [{count}/{total}] {cat_label} {poi.name} (highlight)")
            generate_poi_highlight_overlay(d, poi, hl_path)
        else:
            print(f"  [{count}/{total}] Skip (exists): {hl_path.name}")

        # Back overlay (for both template backs)
        count += 1
        back_path = d.output_images_dir / d.filename_poi_back(poi.poi_id, ".webp")
        if force or not back_path.exists():
            print(f"  [{count}/{total}] {cat_label} {poi.name} (back)")
            generate_poi_highlight_overlay(d, poi, back_path)
        else:
            print(f"  [{count}/{total}] Skip (exists): {back_path.name}")

    print(f"\n[POI-CARDS] Done. {total} images in {d.output_images_dir}")


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
) -> None:
    """Generate basemaps, overlays, and thumbnails for all sub-region decks.

    Called automatically when generating images for a POI deck that has
    sub-regions configured in POI_MULTI_DECK.
    """
    multi_cfg = D.POI_MULTI_DECK.get(f"{region_name}_pois")
    if not multi_cfg:
        return

    sub_region_entries = multi_cfg.get("sub_regions", [])
    sub_regions = D.SUB_REGIONS.get(region_name, [])
    sub_by_key = {s.key: s for s in sub_regions}

    for sub_key, sub_label in sub_region_entries:
        sub = sub_by_key.get(sub_key)
        if sub is None:
            print(f"[SUB-REGION] WARN: Unknown sub-region {sub_key!r}")
            continue

        print(f"\n[SUB-REGION] === {sub_label} ({sub_key}) ===")

        # Build the sub-region POIDeck
        sub_deck = D.get_sub_region_poi_deck(region_name, sub_key)

        # Ensure sub-region basemap exists.
        # Try normal pipeline first; fall back to cropping from parent
        # basemap when the DEM is unavailable.
        sub_bm_path = sub_deck.output_images_dir / sub_deck.filename_basemap()
        sub_bm_rot_path = sub_deck.output_images_dir / sub_deck.filename_basemap_rot()

        # Basemap variants: (filename method on parent, sub output path, gen function)
        _bm_variants = [
            ("filename_basemap",     sub_bm_path,     None),
            ("filename_basemap_rot", sub_bm_rot_path, generate_raster_basemap_rot),
        ]

        if force or not sub_bm_path.exists():
            if sub_deck.region.dem_tif.exists():
                _generate_basemap(sub_deck, force=force)
            else:
                tw, th = _compute_pixel_dims(sub_deck)
                parent_ext = (parent_deck.bbox_west, parent_deck.bbox_east,
                              parent_deck.bbox_south, parent_deck.bbox_north)
                sub_ext = (sub_deck.bbox_west, sub_deck.bbox_east,
                           sub_deck.bbox_south, sub_deck.bbox_north)
                for fn_name, sub_path, _ in _bm_variants:
                    parent_bm = parent_deck.output_images_dir / getattr(parent_deck, fn_name)()
                    crop_basemap_from_parent(
                        parent_bm, parent_ext, sub_ext,
                        sub_path, tw, th,
                    )
        else:
            print(f"[BASEMAP] Already exists: {sub_bm_path.name}")
            # Still ensure all rotated basemaps exist
            for fn_name, sub_path, gen_func in _bm_variants[1:]:
                if force or not sub_path.exists():
                    if sub_deck.region.dem_tif.exists():
                        gen_func(sub_deck, sub_path, force=force)
                    else:
                        tw, th = _compute_pixel_dims(sub_deck)
                        parent_ext = (parent_deck.bbox_west, parent_deck.bbox_east,
                                      parent_deck.bbox_south, parent_deck.bbox_north)
                        sub_ext = (sub_deck.bbox_west, sub_deck.bbox_east,
                                   sub_deck.bbox_south, sub_deck.bbox_north)
                        parent_bm = parent_deck.output_images_dir / getattr(parent_deck, fn_name)()
                        crop_basemap_from_parent(
                            parent_bm, parent_ext, sub_ext,
                            sub_path, tw, th,
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
    parser = argparse.ArgumentParser(description="Generate POI card images")
    D.add_deck_arguments(parser)
    parser.add_argument("--ids", type=str,
                        help="Comma-separated POI IDs (e.g. peak_01,pass_03)")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite existing images")
    args = parser.parse_args()

    d = D.get_deck(args.region, args.system)
    if not isinstance(d, POIDeck):
        print(f"[ERROR] {args.system} is not a POI deck. Use 03_generate_cards.py instead.")
        sys.exit(1)

    # Determine which POIs
    pois = None
    if args.ids:
        ids = [i.strip() for i in args.ids.split(",")]
        pois = []
        for i in ids:
            try:
                pois.append(d.poi_by_id(i))
            except KeyError:
                print(f"[WARN] Unknown POI ID: {i}")

    # Exclude sub-region POIs from the main / full-region deck so that
    # each POI only appears once (either in a sub-region or category deck).
    if pois is None and not args.ids:
        sub_poi_ids = D.get_all_sub_region_poi_ids(args.region)
        if sub_poi_ids:
            main_pois = [p for p in d.pois if p.poi_id not in sub_poi_ids]
            print(f"[POI-CARDS] Excluding {len(sub_poi_ids)} sub-region POIs "
                  f"from main deck ({len(main_pois)} remaining)")
        else:
            main_pois = None
    else:
        main_pois = pois

    # Generate main deck images
    generate_all(d, pois=main_pois, force=args.force)

    # Generate sub-region images if configured (POI_MULTI_DECK)
    if not args.ids:
        generate_all_sub_regions(d, args.region, force=args.force)


if __name__ == "__main__":
    main()
