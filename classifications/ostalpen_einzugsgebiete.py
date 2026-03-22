"""
Classification: Ostalpen Einzugsgebiete (Drainage Basins)
==========================================================
~10 Einzugsgebiete der Ostalpen, gruppiert nach Mündungsgebiet.

Die Einzugsgebiete bilden eine lückenlose Partition der Ostalpen-Karte —
jeder Punkt gehört zu genau einem Flusssystem.  Das macht dieses Subdeck
zur idealen Einstiegskarte für die Grundstruktur der Alpen.

Polygon-Daten stammen aus HydroBASINS (HydroSHEDS, Level 8), aufbereitet
mit ``tools/prepare_einzugsgebiete.py``.

Für die Datenaufbereitung:
    python tools/prepare_einzugsgebiete.py
    → data/osm/ostalpen_einzugsgebiete.geojson

osm_tag: ``basin_id``  (synthetisches Feld, von prepare-Skript gesetzt)
"""

from typing import List

from deck import Classification
from models import Gebirgsgruppe

# ─── Hauptgruppen (Mündungsgebiet) ────────────────────────────────────────────
NORDSEE  = "Nordsee"
SCHWARZES_MEER = "Schwarzes Meer"
ADRIA    = "Adriatisches Meer"

HAUPTGRUPPEN = [NORDSEE, SCHWARZES_MEER, ADRIA]

# ─── Einzugsgebiete ──────────────────────────────────────────────────────────
# Gebirgsgruppe(group_id, name, hauptgruppe, hoechster_gipfel, osm_ref)
# hoechster_gipfel wird hier für Flussinformationen umgenutzt.
# osm_ref = basin_id im GeoJSON (gesetzt von prepare_einzugsgebiete.py)
GROUPS: List[Gebirgsgruppe] = [
    # ═══ Nordsee (via Rhein) ═════════════════════════════════════════════════
    Gebirgsgruppe(
        "E01", "Rhein",
        NORDSEE,
        "Rhein → Bodensee → Nordsee",
        "E01",
    ),
    # ═══ Schwarzes Meer (via Donau) ══════════════════════════════════════════
    Gebirgsgruppe(
        "E02", "Inn",
        SCHWARZES_MEER,
        "Inn → Donau → Schwarzes Meer",
        "E02",
    ),
    Gebirgsgruppe(
        "E03", "Salzach / Saalach",
        SCHWARZES_MEER,
        "Salzach → Inn → Donau → Schwarzes Meer",
        "E03",
    ),
    Gebirgsgruppe(
        "E04", "Traun",
        SCHWARZES_MEER,
        "Traun → Donau → Schwarzes Meer",
        "E04",
    ),
    Gebirgsgruppe(
        "E05", "Enns",
        SCHWARZES_MEER,
        "Enns → Donau → Schwarzes Meer",
        "E05",
    ),
    Gebirgsgruppe(
        "E06", "Mur",
        SCHWARZES_MEER,
        "Mur → Drau → Donau → Schwarzes Meer",
        "E06",
    ),
    Gebirgsgruppe(
        "E07", "Drau",
        SCHWARZES_MEER,
        "Drau → Donau → Schwarzes Meer",
        "E07",
    ),
    # ═══ Adriatisches Meer ═══════════════════════════════════════════════════
    Gebirgsgruppe(
        "E08", "Etsch (Adige)",
        ADRIA,
        "Etsch → Adriatisches Meer",
        "E08",
    ),
    Gebirgsgruppe(
        "E09", "Brenta / Sarca",
        ADRIA,
        "Sarca → Gardasee → Mincio → Adriatisches Meer",
        "E09",
    ),
    Gebirgsgruppe(
        "E10", "Tagliamento / Piave",
        ADRIA,
        "Tagliamento → Adriatisches Meer",
        "E10",
    ),
]

CLASSIFICATION = Classification(
    name="einzugsgebiete",
    title="Ostalpen Einzugsgebiete",
    groups=GROUPS,
    hauptgruppen=HAUPTGRUPPEN,
    colors={
        NORDSEE: {
            "fill": "#2E86C1", "border": "#FFFFFF", "label": "Nordsee",
        },
        SCHWARZES_MEER: {
            "fill": "#FF9500", "border": "#FFFFFF", "label": "Schwarzes Meer",
        },
        ADRIA: {
            "fill": "#DC3545", "border": "#FFFFFF", "label": "Adria",
        },
    },
    osm_tag="basin_id",        # synthetic field set by prepare_einzugsgebiete.py
    osm_fallback_ids={},       # no OSM fallback — data is pre-placed GeoJSON
)
