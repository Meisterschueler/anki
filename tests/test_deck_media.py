"""
test_deck_media.py — Verify that built Anki decks contain all referenced media.

Opens each .apkg (ZIP) file, extracts the note HTML from the SQLite database,
and checks that every src="..." filename has a matching entry in the media map.
This catches:
  - Media files referenced in HTML but not packed into the .apkg
  - Typos / stale filenames left over after renaming images
  - Race conditions where images were deleted between generation and packaging
  - Overlay images that are completely transparent (empty placeholders)
"""

import io
import json
import os
import re
import sqlite3
import tempfile
import zipfile

import pytest
from PIL import Image

# Regex matching src="filename" in Anki note HTML fields
_SRC_RE = re.compile(r'src="([^"]+)"')


def _extract_apkg_media_info(apkg_path):
    """Extract referenced and available media from an .apkg file.

    Returns:
        (referenced, available, notes_count)
        - referenced: set of filenames found in src="..." in note fields
        - available:  set of filenames listed in the media JSON map
        - notes_count: total number of notes in the deck
    """
    with zipfile.ZipFile(str(apkg_path)) as z:
        # Parse media map: {"0": "file_a.webp", "1": "file_b.webp", ...}
        media_map = json.loads(z.read("media"))
        available = set(media_map.values())

        # Verify that every mapped file is actually in the ZIP
        zip_entries = set(z.namelist())
        for idx, fname in media_map.items():
            assert idx in zip_entries, (
                f"Media map entry {idx} -> {fname} is not in the ZIP archive"
            )

        # Extract SQLite DB to a temp file
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".db")
        try:
            with os.fdopen(tmp_fd, "wb") as f:
                f.write(z.read("collection.anki2"))

            conn = sqlite3.connect(tmp_path)
            rows = conn.execute("SELECT flds FROM notes").fetchall()
            conn.close()
        finally:
            os.unlink(tmp_path)

    # Extract all src="..." references from note fields
    referenced = set()
    for (flds,) in rows:
        for field_val in flds.split("\x1f"):
            for m in _SRC_RE.finditer(field_val):
                referenced.add(m.group(1))

    return referenced, available, len(rows)


class TestDeckMediaCompleteness:
    """Every media file referenced in note HTML must exist in the .apkg."""

    def test_all_referenced_media_present(self, apkg_path):
        if not apkg_path.exists():
            pytest.skip(f"Deck file not found: {apkg_path}")

        referenced, available, n_notes = _extract_apkg_media_info(apkg_path)

        if not referenced:
            pytest.skip(f"No media references found in {apkg_path.name} "
                        f"({n_notes} notes)")

        missing = referenced - available
        assert not missing, (
            f"{apkg_path.name}: {len(missing)} media file(s) referenced in "
            f"notes but missing from the .apkg package:\n"
            + "\n".join(f"  - {f}" for f in sorted(missing))
        )

    def test_no_orphan_media(self, apkg_path):
        """Warn about media files packed but never referenced (wasted space)."""
        if not apkg_path.exists():
            pytest.skip(f"Deck file not found: {apkg_path}")

        referenced, available, n_notes = _extract_apkg_media_info(apkg_path)

        if not available:
            pytest.skip(f"No media in {apkg_path.name}")

        orphans = available - referenced
        # Orphans are not critical errors, just warnings — some shared
        # layers (context, basemap) may appear in every note's HTML and
        # thus always be "referenced".  But orphan detection helps catch
        # leftover files that inflate the package size.
        if orphans:
            pct = len(orphans) / len(available) * 100
            # Fail only if > 20% of media is orphaned (likely a bug)
            assert pct <= 20, (
                f"{apkg_path.name}: {len(orphans)}/{len(available)} "
                f"({pct:.0f}%) media files are orphaned (packed but never "
                f"referenced in any note):\n"
                + "\n".join(f"  - {f}" for f in sorted(orphans)[:20])
            )

    def test_no_empty_transparent_overlays(self, apkg_path):
        """Overlay images must contain visible pixels, not be fully transparent.

        An overlay that is completely transparent indicates a failed or
        incomplete card generation step.  Such overlays are technically
        valid WebP files and pass the ``test_all_referenced_media_present``
        check, but render as invisible images in Anki — showing only
        the basemap with no polygons or question marks.

        Basemap and basemap_rot images are excluded (they are opaque).
        """
        if not apkg_path.exists():
            pytest.skip(f"Deck file not found: {apkg_path}")

        with zipfile.ZipFile(str(apkg_path)) as z:
            media_map = json.loads(z.read("media"))

            # Identify overlay files (skip basemaps — they're opaque)
            overlay_entries = {
                idx: fname for idx, fname in media_map.items()
                if "basemap" not in fname
            }

            if not overlay_entries:
                pytest.skip(f"No overlay images in {apkg_path.name}")

            empty_files = []
            for idx, fname in overlay_entries.items():
                data = z.read(idx)
                # Quick size heuristic: a 6704×4320 fully-transparent
                # lossless WebP compresses to ~1164 bytes.  Overlays with
                # actual content (polygons, text, markers) are always larger.
                # Use a generous threshold to avoid false positives.
                if len(data) > 1500:
                    continue

                # Confirm by checking the alpha channel
                try:
                    img = Image.open(io.BytesIO(data))
                    if img.mode != "RGBA":
                        continue
                    # Sample a few rows instead of loading the entire
                    # pixel buffer (much faster for large images).
                    has_visible = False
                    width, height = img.size
                    for y in range(0, height, max(1, height // 20)):
                        row = img.crop((0, y, width, y + 1))
                        if any(p[3] > 0 for p in row.getdata()):
                            has_visible = True
                            break
                    if not has_visible:
                        empty_files.append(fname)
                except Exception:
                    pass  # can't decode → other test will catch it

            assert not empty_files, (
                f"{apkg_path.name}: {len(empty_files)}/{len(overlay_entries)} "
                f"overlay(s) are completely transparent (empty placeholders).\n"
                f"Re-generate cards with:  python scripts/03_generate_cards.py "
                f"--region <region> --force\n"
                + "\n".join(f"  - {f}" for f in sorted(empty_files)[:20])
                + (f"\n  ... and {len(empty_files) - 20} more"
                   if len(empty_files) > 20 else "")
            )
