"""render_utils.py — Shared rendering helpers for 03 and 03b
=============================================================

Contains the core WebP save helper and the context-overlay generator.
Both 03_generate_cards.py and 03b_generate_poi_cards.py import from
here so that 03b no longer depends on 03.
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Project root on path so `import deck` works when this module is
# imported from the scripts/ sub-directory.
sys.path.insert(0, str(Path(__file__).parent.parent))
import deck as D
from deck import Deck

# 02_generate_basemap has a numeric prefix — use importlib.
sys.path.insert(0, str(Path(__file__).parent))
from importlib import import_module
_bm = import_module("02_generate_basemap")

create_figure          = _bm.create_figure
render_country_borders = _bm.render_country_borders
render_cities          = _bm.render_cities


# ─── WebP save helper ────────────────────────────────────────────────────────

_SAVE_PARAMS = {
    "basemap": dict(facecolor="white", transparent=False),
    "overlay": dict(facecolor="none",  transparent=True),
}


def save_figure(fig, output_path, overlay: bool = False) -> None:
    """Save a matplotlib figure as WebP.

    Args:
        fig:         Matplotlib figure to save.
        output_path: Destination path (extension is forced to .webp).
        overlay:     True → transparent lossless WebP; False → opaque lossy WebP.
    """
    import io
    from PIL import Image as _PILImage

    if not isinstance(output_path, Path):
        output_path = Path(output_path)

    out_path = output_path.with_suffix(".webp")
    params   = _SAVE_PARAMS["overlay" if overlay else "basemap"]

    # Render into an in-memory buffer — avoids the temp-file round-trip.
    buf = io.BytesIO()
    try:
        fig.savefig(buf, format="png", dpi=D.FIGURE_DPI,
                    pad_inches=0, edgecolor="none", **params)
    except Exception as exc:
        print(f"[ERROR] Failed to save {out_path}\n  {exc}")
        return
    buf.seek(0)

    img = _PILImage.open(buf)
    img.load()  # fully decode before the buffer goes out of scope
    if img.mode == "RGBA":
        img.save(str(out_path), "WEBP", lossless=True)
    else:
        img.save(str(out_path), "WEBP",
                 quality=D.BASEMAP_WEBP_QUALITY, method=6)
    img.close()


# ─── Context overlay ─────────────────────────────────────────────────────────

def generate_context(d: Deck, output_path) -> None:
    """Shared context overlay: country borders + city labels on transparent bg."""
    fig, ax = create_figure(d)
    ax.set_facecolor("none")
    ax.patch.set_alpha(0.0)
    render_country_borders(ax, d)
    render_cities(ax, d)
    save_figure(fig, output_path, overlay=True)
    plt.close(fig)
