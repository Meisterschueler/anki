"""
test_image_dimensions.py — Verify that related images share identical dimensions.

Three test cases per deck:
  1. All basemap layers (hillshade, lakes, rivers, ocean_mask) must match.
  2. All card images (front/back WebPs) must match.
  3. All top-level images in images/ (excl. _basemap_layers/) must match.
"""

from pathlib import Path
from typing import Dict, Tuple

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

        files = sorted(
            f for f in image_dir.glob("*_front.webp")
        ) + sorted(
            f for f in image_dir.glob("*_back.webp")
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
        files = sorted(image_dir.glob("*.webp"))
        if not files:
            pytest.skip(f"No WebP files in {image_dir}")

        sizes = _collect_sizes(files)
        _assert_uniform_dimensions(sizes)
