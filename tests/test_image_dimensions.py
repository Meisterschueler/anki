"""
test_image_dimensions.py — Verify that related images share identical dimensions.

Three test cases per deck:
  1. All basemap layers (hillshade, lakes, rivers, ocean_mask) must match.
  2. All card images (front/back WebPs) must match.
  3. All top-level images in images/ (excl. _basemap_layers/) must match.
  4. lakes.png and rivers.png must contain non-transparent pixels (not empty/stale).
"""

from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pytest
from PIL import Image


def _collect_sizes(files: list[Path]) -> Dict[Path, Tuple[int, int]]:
    """Return {path: (width, height)} for each file."""
    sizes = {}
    for f in files:
        with Image.open(f) as img:
            sizes[f] = img.size
    return sizes


def _assert_uniform_dimensions(sizes: Dict[Path, Tuple[int, int]]) -> None:
    """Assert all images have the same dimensions; show deviations on failure."""
    unique = set(sizes.values())
    if len(unique) <= 1:
        return

    # Build readable report: group files by their size
    by_size: Dict[Tuple[int, int], list[str]] = {}
    for path, size in sizes.items():
        by_size.setdefault(size, []).append(path.name)

    lines = []
    for size, names in sorted(by_size.items(), key=lambda x: -len(x[1])):
        lines.append(f"  {size[0]}×{size[1]}: {', '.join(sorted(names))}")

    report = "\n".join(lines)
    pytest.fail(
        f"Images have {len(unique)} different dimensions:\n{report}"
    )


class TestBasemapLayers:
    """All basemap layer PNGs must have identical dimensions."""

    def test_basemap_layers_same_dimensions(self, basemap_layers_dir):
        if not basemap_layers_dir.exists():
            pytest.skip(f"Directory not found: {basemap_layers_dir}")

        files = sorted(basemap_layers_dir.glob("*.png"))
        if not files:
            pytest.skip(f"No PNG files in {basemap_layers_dir}")

        sizes = _collect_sizes(files)
        _assert_uniform_dimensions(sizes)


class TestCardImages:
    """All front/back card WebPs must have identical dimensions."""

    def test_card_images_same_dimensions(self, image_dir):
        if not image_dir.exists():
            pytest.skip(f"Directory not found: {image_dir}")

        # Exclude sprite overlays (per-POI back/front) that have a JSON
        # sidecar — sprites from different sub-region decks intentionally
        # have different pixel dimensions.
        files = sorted(
            f for f in image_dir.glob("*_front.webp")
            if not f.with_suffix(".json").exists()
        ) + sorted(
            f for f in image_dir.glob("*_back.webp")
            if not f.with_suffix(".json").exists()
        )
        if not files:
            pytest.skip(f"No front/back WebP files in {image_dir}")

        sizes = _collect_sizes(files)
        _assert_uniform_dimensions(sizes)


class TestAllToplevelImages:
    """All images directly in images/ (excl. subdirectories) must match."""

    def test_all_toplevel_images_same_dimensions(self, image_dir):
        if not image_dir.exists():
            pytest.skip(f"Directory not found: {image_dir}")

        # glob("*.webp") only matches direct children, not subdirs
        # Exclude thumbnails — intentionally smaller previews.
        # Exclude per-POI sprite overlays — identified by a sibling .json sidecar.
        # Exclude per-category badge/highlight sprites — small fixed-size icons
        # that intentionally differ from the full-canvas layer images.
        files = sorted(
            f for f in image_dir.glob("*.webp")
            if "_thumb_" not in f.name
            and "_badge_" not in f.name
            and "_highlight_" not in f.name
            and not f.with_suffix(".json").exists()
        )
        if not files:
            pytest.skip(f"No WebP files in {image_dir}")

        sizes = _collect_sizes(files)
        _assert_uniform_dimensions(sizes)


class TestBasemapLayerContent:
    """lakes.png and rivers.png must contain visible (non-transparent) pixels.

    An all-transparent layer means the basemap was cached before the OSM source
    data was downloaded — a stale-cache bug that causes the basemap to appear
    without lakes or rivers.
    """

    @pytest.mark.parametrize("layer_name", ["lakes.png", "rivers.png"])
    def test_layer_has_visible_pixels(self, basemap_layers_dir, layer_name):
        layer_path = basemap_layers_dir / layer_name
        if not layer_path.exists():
            pytest.skip(f"Layer not built yet: {layer_path}")

        arr = np.array(Image.open(layer_path))
        nonzero = int((arr[:, :, 3] > 0).sum())
        assert nonzero > 0, (
            f"{layer_name} in {basemap_layers_dir} is fully transparent "
            f"(0 visible pixels). The layer was likely cached before the OSM "
            f"source data was downloaded. Delete the stale file and re-run "
            f"02_generate_basemap.py to regenerate it."
        )
