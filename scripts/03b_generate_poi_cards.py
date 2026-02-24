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
render_country_borders = _bm.render_country_borders
render_cities = _bm.render_cities

# Import save_figure from 03
_cards = import_module("03_generate_cards")
save_figure = _cards.save_figure


# ─── POI Rendering ───────────────────────────────────────────────────────────

def _render_poi_marker(ax, poi: POI, style: dict, zorder: int = 10,
                       size_scale: float = 1.0, alpha: float = 1.0):
    """Render a single POI marker on the map."""
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
                    label_alpha: float = 0.7, skip_poi_id: str = None):
    """Render all POI markers with optional small labels."""
    for poi in d.pois:
        if poi.poi_id == skip_poi_id:
            continue
        style = d.category_style.get(poi.category, {})
        _render_poi_marker(ax, poi, style, zorder=10)

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


def render_poi_highlight(ax, poi: POI, radius_deg: float = 0.08):
    """Render a red highlight circle around a target POI.

    Uses an Ellipse with aspect-ratio correction so the circle appears
    round on the projected map (lon degrees are narrower at higher lats).
    """
    import math
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


def render_legend(ax, d: POIDeck):
    """Render a small legend showing category symbols."""
    handles = []
    for cat in ["peak", "pass", "town", "valley"]:
        style = d.category_style.get(cat, {})
        if not style:
            continue
        count = len(d.pois_by_category(cat))
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

def _generate_basemap(d: POIDeck, force: bool = False):
    """Generate the shared basemap WebP."""
    basemap_path = d.output_images_dir / d.filename_basemap()
    generate_raster_basemap(d, basemap_path, force=force)


def generate_partition(d: POIDeck, output_path) -> None:
    """Partition map (Einteilung): all POIs coloured by category with legend."""
    fig, ax = create_figure(d)
    render_full_basemap(ax, d, svg_mode=False, overlay_mode=True,
                        rivers=False, lakes=False)
    render_all_pois(ax, d, label_fontsize=4.0, label_alpha=0.6)
    render_legend(ax, d)
    save_figure(fig, output_path, overlay=True)
    plt.close(fig)


def generate_context(d: POIDeck, output_path) -> None:
    """Shared context overlay: country borders + city labels."""
    fig, ax = create_figure(d)
    ax.set_facecolor("none")
    ax.patch.set_alpha(0.0)
    render_country_borders(ax, d)
    render_cities(ax, d)
    save_figure(fig, output_path, overlay=True)
    plt.close(fig)


def generate_all_pois_overlay(d: POIDeck, output_path) -> None:
    """Shared overlay with all POI markers + small labels (transparent bg)."""
    fig, ax = create_figure(d)
    ax.set_facecolor("none")
    ax.patch.set_alpha(0.0)
    render_all_pois(ax, d, label_fontsize=3.5, label_alpha=0.5)
    save_figure(fig, output_path, overlay=True)
    plt.close(fig)


def generate_poi_front_locate(d: POIDeck, poi: POI, output_path) -> None:
    """Template 1 front — 'Wo ist X?' title label on transparent overlay."""
    fig, ax = create_figure(d)
    render_full_basemap(ax, d, cities=False, borders=False,
                        rivers=False, lakes=False,
                        svg_mode=False, overlay_mode=True)
    render_poi_question(ax, poi, d)
    save_figure(fig, output_path, overlay=True)
    plt.close(fig)


def generate_poi_back_locate(d: POIDeck, poi: POI, output_path) -> None:
    """Template 1 back — all POIs + highlight circle (transparent overlay)."""
    fig, ax = create_figure(d)
    render_full_basemap(ax, d, cities=False, borders=False,
                        rivers=False, lakes=False,
                        svg_mode=False, overlay_mode=True)
    render_all_pois(ax, d, label_fontsize=3.5, label_alpha=0.5,
                    skip_poi_id=poi.poi_id)
    render_poi_highlight(ax, poi)
    style = d.category_style.get(poi.category, {})
    render_poi_label(ax, poi, style)
    save_figure(fig, output_path, overlay=True)
    plt.close(fig)


# ─── Overlay-only functions (for Anki CSS compositing) ───────────────────────

def generate_poi_highlight_overlay(d: POIDeck, poi: POI, output_path) -> None:
    """Overlay: just the red highlight circle (transparent bg).

    Used for Template 2 ('Was ist das?') front — composited with
    basemap + all_pois in Anki via CSS.
    """
    fig, ax = create_figure(d)
    ax.set_facecolor("none")
    ax.patch.set_alpha(0.0)
    render_poi_highlight(ax, poi)
    save_figure(fig, output_path, overlay=True)
    plt.close(fig)


def generate_poi_back_overlay(d: POIDeck, poi: POI, output_path) -> None:
    """Overlay: highlight circle only (transparent bg).

    Used for both template backs — composited with basemap + context +
    all_pois in Anki via CSS.  Label is shown in the HTML template, not
    burned into the image.
    """
    fig, ax = create_figure(d)
    ax.set_facecolor("none")
    ax.patch.set_alpha(0.0)
    render_poi_highlight(ax, poi)
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

    _generate_basemap(d, force=False)

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
        generate_all_pois_overlay(d, all_pois_path)
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
            generate_poi_back_overlay(d, poi, back_path)
        else:
            print(f"  [{count}/{total}] Skip (exists): {back_path.name}")

    print(f"\n[POI-CARDS] Done. {total} images in {d.output_images_dir}")


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

    generate_all(d, pois=pois, force=args.force)


if __name__ == "__main__":
    main()
