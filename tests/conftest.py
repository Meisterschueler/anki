"""
conftest.py — Shared pytest fixtures for peak_soaring tests.
"""

import sys
from pathlib import Path

import pytest

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from deck import get_deck, VALID_COMBINATIONS


def _deck_params():
    """Yield (region, system) tuples for all valid deck combinations."""
    for region, systems in VALID_COMBINATIONS.items():
        for system in systems:
            yield region, system


@pytest.fixture(params=list(_deck_params()), ids=lambda p: f"{p[0]}_{p[1]}")
def deck(request):
    """Return a Deck instance for each valid region × classification combo."""
    region, system = request.param
    return get_deck(region, system)


@pytest.fixture
def image_dir(deck):
    """Path to the deck's output images directory."""
    return deck.output_images_dir


@pytest.fixture
def basemap_layers_dir(deck):
    """Path to the deck's basemap layers subdirectory."""
    return deck.output_images_dir / "_basemap_layers"


@pytest.fixture
def apkg_path(deck):
    """Path to the deck's .apkg output file."""
    return deck.output_csv_dir / f"{deck.anki_csv_name}.apkg"
