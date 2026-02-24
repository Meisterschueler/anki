"""
03_generate_cards.py — Generate card images for Anki
=====================================================
Creates map images in two WebP output modes:

1. Partition map / Einteilung  (1 image)
   All groups coloured by Hauptgruppe, numbered with IDs.
   Filename: ps_{region}_{system}_partition.webp

2. Per-group maps (N × 2 images)
   Front: question mark at group centroid.
   Back:  single polygon (+ parent polygon if hierarchical).
   Filename: ps_{region}_{system}_group_{id}_{front|back}.webp

Always produces WebP files.
  basemap   — opaque, lossy (shared background)
  overlay   — transparent, lossless (vector layers composited in Anki)

Usage:
    python scripts/03_generate_cards.py --region ostalpen [--ids 3b,52,40] [--force]
    python scripts/03_generate_cards.py --region westalpen
"""

import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
import deck as D
from deck import Deck

# Import basemap module (filename starts with a digit, so use importlib)
sys.path.insert(0, str(Path(__file__).parent))
from importlib import import_module
_bm = import_module("02_generate_basemap")

create_figure = _bm.create_figure
render_full_basemap = _bm.render_full_basemap
generate_raster_basemap = _bm.generate_raster_basemap
render_polygons_colored = _bm.render_polygons_colored
render_single_polygon = _bm.render_single_polygon
render_parent_polygon = _bm.render_parent_polygon
render_question_mark = _bm.render_question_mark
render_country_borders = _bm.render_country_borders
render_cities = _bm.render_cities


# ─── WebP save helper ────────────────────────────────────────────────────────

# matplotlib savefig params by mode
_SAVE_PARAMS = {
    "basemap": dict(format="png", facecolor="white", transparent=False),
    "overlay": dict(format="png", facecolor="none",  transparent=True),
}


def save_figure(fig, output_path, overlay: bool = False, deck: Deck = None) -> None:
    """Save figure as WebP.

    Args:
        fig: Matplotlib figure
        output_path: Destination path (extension forced to .webp)
        overlay: True for transparent lossless overlay, False for opaque lossy basemap
        deck: Unused, kept for API compatibility
    """
    if not isinstance(output_path, Path):
        output_path = Path(output_path)

    out_path = output_path.with_suffix(".webp")
    mode = "overlay" if overlay else "basemap"
    params = _SAVE_PARAMS[mode]

    # Matplotlib cannot write WebP directly — save PNG then convert.
    tmp_path = out_path.with_suffix(".png")

    try:
        fig.savefig(str(tmp_path), dpi=D.FIGURE_DPI,
                    pad_inches=0, edgecolor="none", **params)
    except Exception as e:
        print(f"[ERROR] Failed to save {tmp_path}\n  {e}")
        return

    from PIL import Image as _PILImage
    img = _PILImage.open(str(tmp_path))
    if img.mode == "RGBA":
        # Transparent overlay → lossless WebP
        img.save(str(out_path), "WEBP", lossless=True)
    else:
        # Opaque image → lossy WebP
        img.save(str(out_path), "WEBP", quality=D.BASEMAP_WEBP_QUALITY, method=6)
    img.close()
    tmp_path.unlink()  # remove temporary PNG


def _generate_basemap(d: Deck, force: bool = False) -> None:
    """Generate the shared basemap WebP using the fast raster pipeline."""
    basemap_path = d.output_images_dir / d.filename_basemap()
    generate_raster_basemap(d, basemap_path, force=force)


# ─── Partition Map (Einteilung) ─────────────────────────────────────────────

def generate_partition(d: Deck, output_path) -> None:
    """Partition map (Einteilung): all groups coloured by Hauptgruppe, numbered."""
    fig, ax = create_figure(d)
    render_full_basemap(ax, d, svg_mode=False,
                        overlay_mode=True,
                        cities=False, borders=False,
                        rivers=False, lakes=False)
    render_polygons_colored(ax, d, show_ids=True)
    save_figure(fig, output_path, overlay=True)
    plt.close(fig)


# ─── Context Layer (borders + cities) ────────────────────────────────────────

def generate_context(d: Deck, output_path) -> None:
    """Shared context overlay: country borders + city labels on transparent bg."""
    fig, ax = create_figure(d)
    ax.set_facecolor("none")
    ax.patch.set_alpha(0.0)
    render_country_borders(ax, d)
    render_cities(ax, d)
    save_figure(fig, output_path, overlay=True)
    plt.close(fig)


# ─── Per-Group Map ────────────────────────────────────────────────────────────

def generate_group_card(d: Deck, group, output_path) -> None:
    """Front card: transparent overlay with red question mark at group centroid."""
    fig, ax = create_figure(d)
    render_full_basemap(ax, d, cities=False, borders=False,
                        rivers=False, lakes=False,
                        svg_mode=False, overlay_mode=True)
    render_question_mark(ax, d, group.osm_ref)
    save_figure(fig, output_path, overlay=True)
    plt.close(fig)


def generate_group_card_colored(d: Deck, group, output_path):
    """Back card: transparent overlay with single polygon (+ parent if hierarchical)."""
    fig, ax = create_figure(d)
    render_full_basemap(ax, d, cities=False, borders=False,
                        rivers=False, lakes=False,
                        svg_mode=False, overlay_mode=True)
    if d.classification.parent_osm_tag:
        render_parent_polygon(ax, d, group.osm_ref)
    render_single_polygon(ax, d, group.osm_ref)
    save_figure(fig, output_path, overlay=True)
    plt.close(fig)


# ─── Title Box ────────────────────────────────────────────────────────────────

def _render_title_box(fig, ax, d: Deck, group) -> None:
    """Render a two-line title box at the top centre of the axes.
    
    Line 1: group name (bold, 13pt)
    Line 2: classification label + group ID (normal, 9pt, grey)
    Background: white rounded box with drop shadow.
    """
    from matplotlib.patches import FancyBboxPatch
    from matplotlib.transforms import Bbox

    system_label = d.classification.title.split()[0]  # "AVE" or "SOIUSA"
    line1 = group.name
    line2 = f"{system_label}: {group.group_id}"

    t1 = ax.text(
        0.5, 0.955, line1,
        transform=ax.transAxes,
        ha="center", va="top",
        fontsize=13, fontweight="bold", color="black",
        zorder=21,
    )
    t2 = ax.text(
        0.5, 0.955, f"\n{line2}",
        transform=ax.transAxes,
        ha="center", va="top",
        fontsize=9, fontweight="normal", color="#444444",
        zorder=21,
        linespacing=2.2,
    )

    # Measure text extents to size the background box
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    bb1 = t1.get_window_extent(renderer).transformed(ax.transAxes.inverted())
    bb2 = t2.get_window_extent(renderer).transformed(ax.transAxes.inverted())
    bb = Bbox.union([bb1, bb2])

    pad_x, pad_y = 0.015, 0.008
    box = FancyBboxPatch(
        (bb.x0 - pad_x, bb.y0 - pad_y),
        bb.width + 2 * pad_x,
        bb.height + 2 * pad_y,
        boxstyle="round,pad=0.006",
        facecolor="white", edgecolor="black", linewidth=0.8,
        transform=ax.transAxes, zorder=20,
    )
    shadow = FancyBboxPatch(
        (bb.x0 - pad_x + 0.003, bb.y0 - pad_y - 0.004),
        bb.width + 2 * pad_x,
        bb.height + 2 * pad_y,
        boxstyle="round,pad=0.006",
        facecolor="#00000030", edgecolor="none",
        transform=ax.transAxes, zorder=19,
    )
    ax.add_patch(shadow)
    ax.add_patch(box)


# ─── Batch Generation ────────────────────────────────────────────────────────

def generate_all(d: Deck, groups=None, force=False):
    """Generate basemap + partition + per-group WebP images.
    
    Args:
        d: Deck configuration
        groups: List of groups to generate (None = all)
        force: Overwrite existing files
    """
    if groups is None:
        groups = d.groups

    # Ensure raster basemap exists
    _generate_basemap(d, force=force)

    total = 2 + 2 * len(groups)
    count = 0

    print(f"[CARDS] Generating {total} overlay images for {d.title} …")

    # 1. Partition (Einteilung)
    count += 1
    partition_path = d.output_images_dir / d.filename_partition(".webp")
    if force or not partition_path.exists():
        print(f"  [{count}/{total}] Partition map (Einteilung)")
        generate_partition(d, partition_path)
    else:
        print(f"  [{count}/{total}] Skip (exists): {partition_path.name}")

    # 2. Context layer (borders + cities)
    count += 1
    context_path = d.output_images_dir / d.filename_context()
    if force or not context_path.exists():
        print(f"  [{count}/{total}] Context layer (borders + cities)")
        generate_context(d, context_path)
    else:
        print(f"  [{count}/{total}] Skip (exists): {context_path.name}")

    # 3. Per-group cards
    for group in groups:
        # Front — question mark overlay
        count += 1
        path1 = d.output_images_dir / d.filename_group_front(group.group_id, ".webp")
        if force or not path1.exists():
            print(f"  [{count}/{total}] Group {group.group_id}: {group.name} (front)")
            generate_group_card(d, group, path1)
        else:
            print(f"  [{count}/{total}] Skip (exists): {path1.name}")

        # Back — polygon overlay
        count += 1
        path2 = d.output_images_dir / d.filename_group_back(group.group_id, ".webp")
        if force or not path2.exists():
            print(f"  [{count}/{total}] Group {group.group_id}: {group.name} (back)")
            generate_group_card_colored(d, group, path2)
        else:
            print(f"  [{count}/{total}] Skip (exists): {path2.name}")

    print(f"\n[CARDS] Done. {total} images in {d.output_images_dir}")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate Anki card images")
    D.add_deck_arguments(parser)
    parser.add_argument("--ids", type=str,
                        help="Comma-separated group IDs (e.g. 3b,52,40)")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite existing images")
    args = parser.parse_args()

    d = D.get_deck(args.region, args.system)

    # Determine which groups
    groups = None
    if args.ids:
        ids = [i.strip() for i in args.ids.split(",")]
        groups = []
        for i in ids:
            try:
                groups.append(d.group_by_id(i))
            except KeyError:
                print(f"[WARN] Unknown group ID: {i}")

    # Clean existing WebP overlays if --force
    if args.force and d.output_images_dir.exists():
        basemap_name = d.filename_basemap()
        if groups is None:
            # Delete all WebP overlays for this deck (keep basemap)
            for f in d.output_images_dir.glob(f"{d.prefix}_*.webp"):
                if f.name != basemap_name:
                    f.unlink()
        else:
            # Delete only selected group images
            for g in groups:
                for name in [
                    d.filename_group_front(g.group_id, ".webp"),
                    d.filename_group_back(g.group_id, ".webp"),
                ]:
                    p = d.output_images_dir / name
                    if p.exists():
                        p.unlink()

    generate_all(d, groups=groups, force=args.force)

if __name__ == "__main__":
    main()