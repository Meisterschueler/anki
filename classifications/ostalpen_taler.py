"""
Classification: Ostalpen Täler (Haupttäler der Ostalpen)
=========================================================
~18 Haupttäler, gruppiert nach Einzugsgebiet.

Die Täler werden als Polygon-Überlagerungen dargestellt (wie AVE 84).
Jedes Tal wird durch seine OSM-Relation identifiziert — entweder über
den Tag ``natural=valley`` + ``name`` (primär) oder über ``osm_fallback_ids``
(Fallback per Relations-ID, falls der Tag-Query nicht trifft).

Für den Download:  python scripts/01_download_data.py --region ostalpen --system taler
                   → data/osm/ostalpen_taler.geojson

OSM-Tag: ``name`` (Täler haben kein einheitliches Referenz-Tag wie ``ref:aveo``)
Primär: Overpass-Query nach ``relation["natural"="valley"]["name"="…"]`` für
jeden Tal-Namen.  ``osm_fallback_ids`` enthält OSM-IDs (Relations oder Ways)
für Täler, die nicht per Tag-Query gefunden werden.
"""

from typing import List

from deck import Classification
from models import Gebirgsgruppe

# ─── Hauptgruppen (Einzugsgebiete) ───────────────────────────────────────────
INN      = "Inn-System"
SALZACH  = "Salzach-System"
ENNS     = "Enns/Mur-System"
DRAU     = "Drau-System"
ETSCH    = "Etsch/Adria-System"
RHEIN    = "Rhein-System"

HAUPTGRUPPEN = [INN, SALZACH, ENNS, DRAU, ETSCH, RHEIN]

# ─── ~18 Haupttäler ──────────────────────────────────────────────────────────
# Gebirgsgruppe(group_id, name, hauptgruppe, hoechster_gipfel, osm_ref)
# osm_ref = exakter OSM-Name der Relation (muss osm_tag="name" entsprechen)
GROUPS: List[Gebirgsgruppe] = [
    # ═══ Inn-System ══════════════════════════════════════════════════════════
    # (Inn → Donau → Schwarzes Meer)
    Gebirgsgruppe("T01", "Inntal",           INN,     "Umläuft Innsbruck (524 m)",     "Inntal"),
    Gebirgsgruppe("T02", "Oberinntal",       INN,     "Landeck (817 m)",               "Oberinntal"),
    Gebirgsgruppe("T03", "Unterinntal",      INN,     "Kufstein (499 m)",              "Unterinntal"),
    Gebirgsgruppe("T04", "Lechtal",          INN,     "Lech (800 m)",                  "Lechtal"),
    Gebirgsgruppe("T05", "Ötztal",           INN,     "Sölden (1368 m)",               "Ötztal"),
    Gebirgsgruppe("T06", "Zillertal",        INN,     "Mayrhofen (630 m)",             "Zillertal"),
    Gebirgsgruppe("T07", "Stubaital",        INN,     "Fulpmes (937 m)",               "Stubaital"),

    # ═══ Salzach-System ══════════════════════════════════════════════════════
    # (Salzach → Inn → Donau)
    Gebirgsgruppe("T08", "Salzachtal",       SALZACH, "Salzburg (424 m)",              "Salzachtal"),
    Gebirgsgruppe("T09", "Gasteinertal",     SALZACH, "Bad Gastein (1002 m)",          "Gasteinertal"),

    # ═══ Enns/Mur-System ═════════════════════════════════════════════════════
    # (Enns/Mur → Donau)
    Gebirgsgruppe("T10", "Ennstal",          ENNS,    "Schladming (745 m)",            "Ennstal"),
    Gebirgsgruppe("T11", "Murtal",           ENNS,    "Knittelfeld (647 m)",           "Murtal"),

    # ═══ Drau-System ═════════════════════════════════════════════════════════
    # (Drau/Drava → Donau)
    Gebirgsgruppe("T12", "Drautal",          DRAU,    "Spittal an der Drau (556 m)",   "Drautal"),
    Gebirgsgruppe("T13", "Mölltal",          DRAU,    "Winklern (967 m)",              "Mölltal"),
    Gebirgsgruppe("T14", "Gailtal",          DRAU,    "Hermagor (612 m)",              "Gailtal"),

    # ═══ Etsch/Adria-System ══════════════════════════════════════════════════
    # (Etsch/Adige → Adriatisches Meer; Eisack/Rienz tributaries)
    Gebirgsgruppe("T15", "Wipptal",          ETSCH,   "Brenner (1374 m)",              "Wipptal"),
    Gebirgsgruppe("T16", "Eisacktal",        ETSCH,   "Bozen (262 m)",                 "Eisacktal - Valle Isarco"),
    Gebirgsgruppe("T17", "Pustertal",        ETSCH,   "Bruneck (836 m)",               "Pustertal - Val Pusteria"),
    Gebirgsgruppe("T18", "Vinschgau",        ETSCH,   "Mals (1053 m)",                 "Vinschgau - Val Venosta"),

    # ═══ Rhein-System ════════════════════════════════════════════════════════
    # (Vorderrhein/Hinterrhein → Bodensee → Nordsee)
    Gebirgsgruppe("T19", "Alpenrheintal",    RHEIN,   "Feldkirch (457 m)",             "Alpenrheintal"),
    Gebirgsgruppe("T20", "Montafon",         RHEIN,   "Schruns (690 m)",               "Montafon"),
]

# ─── OSM relation IDs for robust download ────────────────────────────────────
# Format: {osm_ref → OSM relation ID}
# These are well-known valleys with stable relation IDs on OpenStreetMap.
# Update if a relation is split/replaced (check osm.org/relation/{id}).
OSM_FALLBACK_IDS = {
    # ── Relations found via natural=valley tag (confirmed by Overpass) ───────
    "Inntal":                   12533003,   # relation 12533003
    "Stubaital":                19042342,   # relation 19042342
    "Ennstal":                  18844824,   # relation 18844824
    "Murtal":                   19965565,   # relation 19965565
    "Gailtal":                  12705333,   # relation 12705333
    "Wipptal":                  19042352,   # relation 19042352
    # ── Ways found via Nominatim (administrative / area boundaries) ──────────
    # These are typically administrative area ways that approximate the valley.
    # The downloader will try way(id) when relation(id) returns nothing.
    "Oberinntal":               925622570,  # way – Bezirk Imst boundary (approx.)
    "Unterinntal":              925622569,  # way – Tirol
    "Lechtal":                  925971043,  # way – Bezirk Reutte boundary (approx.)
    "Ötztal":                   925622633,  # way – Bezirk Imst / Ötztal area
    "Zillertal":                199265512,  # way – Kaltenbach, Bezirk Schwaz
    "Salzachtal":              1367428195,  # way – Salzachtal, Salzburg
    "Gasteinertal":            1367137706,  # way – Gasteinertal, Lend
    "Drautal":                  942503499,  # way – Drautal, Bezirk Villach-Land
    "Mölltal":                  942503498,  # way – Mölltal, Bezirk Spittal
    "Eisacktal - Valle Isarco": 370532975,  # way – Eisacktal - Valle Isarco (South Tyrol)
    "Pustertal - Val Pusteria": 338451906,  # way – Pustertal - Val Pusteria
    "Vinschgau - Val Venosta":  568532120,  # way – Vinschgau - Val Venosta
    "Alpenrheintal":           1104102861,  # way – Alpenrheintal, St. Gallen/CH
    "Montafon":                 584737457,  # way – Montafon, Bludenz, Vorarlberg
}

CLASSIFICATION = Classification(
    name="taler",
    title="Ostalpen Täler",
    groups=GROUPS,
    hauptgruppen=HAUPTGRUPPEN,
    colors={
        INN:     {"fill": "#2E86C1", "border": "#FFFFFF", "label": "Inn"},
        SALZACH: {"fill": "#28A745", "border": "#FFFFFF", "label": "Salzach"},
        ENNS:    {"fill": "#FF9500", "border": "#FFFFFF", "label": "Enns/Mur"},
        DRAU:    {"fill": "#8E44AD", "border": "#FFFFFF", "label": "Drau"},
        ETSCH:   {"fill": "#DC3545", "border": "#FFFFFF", "label": "Etsch"},
        RHEIN:   {"fill": "#6C757D", "border": "#FFFFFF", "label": "Rhein"},
    },
    osm_tag="name",          # Valley polygons are matched by their OSM name
    osm_fallback_ids=OSM_FALLBACK_IDS,
)
