"""
test_deck_size.py — Verify that built Anki decks stay within size limits.

The .apkg file must not exceed MAX_DECK_SIZE_MB (default: 50 MB).
"""

import pytest

MAX_DECK_SIZE_MB = 50


class TestDeckSize:
    """Anki .apkg file must not exceed the size limit."""

    def test_deck_file_not_exceeds_50mb(self, apkg_path):
        if not apkg_path.exists():
            pytest.skip(f"Deck file not found: {apkg_path}")

        size_bytes = apkg_path.stat().st_size
        size_mb = size_bytes / (1024 * 1024)

        assert size_mb <= MAX_DECK_SIZE_MB, (
            f"Deck {apkg_path.name} is {size_mb:.1f} MB, "
            f"exceeds limit of {MAX_DECK_SIZE_MB} MB"
        )
