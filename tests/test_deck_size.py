"""
test_deck_size.py — Verify that built Anki decks stay within size limits.

The .apkg file must not exceed MAX_DECK_SIZE_MB (default: 50 MB).
Landewiesen decks embed CUPX images and may be up to 80 MB.
"""

import pytest

MAX_DECK_SIZE_MB = 50
# Landewiesen decks include embedded JPGs from CUPX (satellite + field photos)
MAX_DECK_SIZE_LANDEWIESEN_MB = 80

def _max_size_for(apkg_path):
    if "landewiesen" in apkg_path.name:
        return MAX_DECK_SIZE_LANDEWIESEN_MB
    return MAX_DECK_SIZE_MB


class TestDeckSize:
    """Anki .apkg file must not exceed the size limit."""

    def test_deck_file_within_size_limit(self, apkg_path):
        if not apkg_path.exists():
            pytest.skip(f"Deck file not found: {apkg_path}")

        size_bytes = apkg_path.stat().st_size
        size_mb = size_bytes / (1024 * 1024)
        limit = _max_size_for(apkg_path)

        assert size_mb <= limit, (
            f"Deck {apkg_path.name} is {size_mb:.1f} MB, "
            f"exceeds limit of {limit} MB"
        )
