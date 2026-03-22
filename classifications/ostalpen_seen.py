"""
Classification: Ostalpen Seen (Wichtigste Seen der Ostalpen)
============================================================
Kuratierte Liste bedeutender Seen in den Ostalpen und im Alpenvorland.
Schwerpunkt: Seen mit hohem Wiedererkennungswert für Segelflieger.

Koordinaten und Höhen aus OpenStreetMap / Wikipedia (März 2026).
"""

from deck import POIClassification
from models import POI

# ─── Seen (Lakes only) ───────────────────────────────────────────────────────
LAKES = [
    # ── Voralpenseen (Nordrand) ────────────────────────────────────────────────
    POI("os_01", "Bodensee",             "lake", 47.65347,  9.43318,  395,
        subtitle="AT/DE/CH · 536 km²"),
    POI("os_02", "Chiemsee",             "lake", 47.87490, 12.45570,  518,
        subtitle="DE · 80 km²"),
    POI("os_03", "Tegernsee",            "lake", 47.71884, 11.73874,  726,
        subtitle="DE · 9 km²"),
    POI("os_04", "Achensee",             "lake", 47.45698, 11.71190,  929,
        subtitle="AT/TI · 7 km²"),
    POI("os_05", "Wolfgangsee",          "lake", 47.73736, 13.44688,  540,
        subtitle="AT/OÖ-SBG · 13 km²"),
    POI("os_06", "Attersee",             "lake", 47.89038, 13.54220,  469,
        subtitle="AT/OÖ · 46 km² — größter Altkrater-See AT"),
    POI("os_07", "Traunsee",             "lake", 47.84375, 13.79695,  422,
        subtitle="AT/OÖ · 26 km²"),
    POI("os_08", "Mondsee",              "lake", 47.84527, 13.39722,  481,
        subtitle="AT/OÖ · 14 km²"),
    # ── Inneralpine Seen ─────────────────────────────────────────────────────
    POI("os_09", "Zeller See",           "lake", 47.32417, 12.79472,  748,
        subtitle="AT/SBG · 4,5 km²"),
    POI("os_10", "Millstätter See",      "lake", 46.80000, 13.56667,  588,
        subtitle="AT/KTN · 13 km²"),
    POI("os_11", "Wörthersee",           "lake", 46.62222, 14.15556,  440,
        subtitle="AT/KTN · 19 km²"),
    POI("os_12", "Ossiacher See",        "lake", 46.67028, 13.98028,  501,
        subtitle="AT/KTN · 11 km²"),
    POI("os_13", "Weißensee",            "lake", 46.71417, 13.30806,  931,
        subtitle="AT/KTN · 7 km² — höchstgelegener schiffbarer See AT"),
    POI("os_14", "Reschensee",           "lake", 46.80274, 10.52807, 1498,
        subtitle="IT/BZ · 7 km² — versunkener Kirchturm"),
    POI("os_15", "Lago di Garda",        "lake", 45.65000, 10.65000,   65,
        subtitle="IT · 370 km² — größter See Italiens"),
    # ── Kärntner / Slowenische Grenzregion ───────────────────────────────────
    POI("os_16", "Klopeiner See",        "lake", 46.56889, 14.60194,  446,
        subtitle="AT/KTN · 1 km²"),
]

CLASSIFICATION = POIClassification(
    name="seen",
    title="Wichtigste Seen",
    pois=LAKES,
    category_style={
        "lake": {"marker": "o", "color": "#3A9FD8", "size": 12, "label": "See"},
    },
)
