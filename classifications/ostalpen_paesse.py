"""
Classification: Ostalpen Pässe (Wichtigste Pässe der Ostalpen)
==============================================================
Kuratierte Liste der bedeutendsten Alpenübergänge der Ostalpen.
Hauptkriterium: Befahrbarkeit (Straße/Bahn) oder historische Bedeutung.

Koordinaten und Höhen aus OpenStreetMap / Wikipedia (März 2026).
"""

from deck import POIClassification
from models import POI

# ─── Pässe (Passes only) ─────────────────────────────────────────────────────
PASSES = [
    # ── Längsverbindungen (N-S) ───────────────────────────────────────────────
    POI("op_01", "Brennerpass",          "pass", 47.00420, 11.50750, 1370,
        subtitle="A13 / Brennerbahn · AT-IT"),
    POI("op_02", "Reschenpass",          "pass", 46.83435, 10.51025, 1507,
        subtitle="B180 · AT-IT, Via Claudia Augusta"),
    POI("op_03", "Stilfser Joch",        "pass", 46.52860, 10.45330, 2757,
        subtitle="SS38 Passo dello Stelvio · IT"),
    POI("op_04", "Penser Joch",          "pass", 46.83610, 11.44170, 2211,
        subtitle="SP 508 · AT-IT"),
    POI("op_05", "Timmelsjoch",          "pass", 46.90000, 11.09170, 2474,
        subtitle="Hochalpenstraße · AT-IT (Sommer)"),
    POI("op_06", "Felbertauern",         "pass", 47.14720, 12.48530, 1650,
        subtitle="Felbertauerntunnel · AT"),
    POI("op_07", "Großglockner Hochalpenstraße", "pass", 47.08170, 12.84280, 2504,
        subtitle="Hochtor · AT (Sommer)"),
    POI("op_08", "Katschberg",           "pass", 47.05940, 13.61610, 1641,
        subtitle="A10 / B99 · AT"),
    POI("op_09", "Radstädter Tauern",    "pass", 47.26670, 13.50000, 1738,
        subtitle="B99 · AT"),
    POI("op_10", "Semmering",            "pass", 47.63556, 15.82972, 985,
        subtitle="Semmering-Tunnel/Bahn · AT · erste Hochgebirgsbahn"),
    # ── Querverbindungen (O-W) ────────────────────────────────────────────────
    POI("op_11", "Arlbergpass",          "pass", 47.12970, 10.21390, 1793,
        subtitle="B197 / Arlberg-Tunnel · AT"),
    POI("op_12", "Fernpass",             "pass", 47.36392, 10.83494, 1216,
        subtitle="B179 · AT-DE"),
    POI("op_13", "Gerlospass",           "pass", 47.24286, 12.10939, 1507,
        subtitle="B165 · AT"),
    POI("op_14", "Pass Thurn",           "pass", 47.30859, 12.40849, 1274,
        subtitle="B161 · AT"),
    # ── Dolomitenpässe ────────────────────────────────────────────────────────
    POI("op_15", "Sellajoch",            "pass", 46.50830, 11.76110, 2240,
        subtitle="Passo Sella · IT"),
    POI("op_16", "Grödnerjoch",          "pass", 46.55280, 11.80830, 2121,
        subtitle="Passo Gardena · IT"),
    POI("op_17", "Pordoijoch",           "pass", 46.48750, 11.81250, 2239,
        subtitle="Passo Pordoi · IT"),
    POI("op_18", "Falzaregopass",        "pass", 46.52080, 12.00830, 2105,
        subtitle="Passo Falzarego · IT"),
    # ── Karawanken / Karnische Alpen ──────────────────────────────────────────
    POI("op_19", "Plöckenpass",          "pass", 46.60280, 12.94440, 1357,
        subtitle="SS52/B110 · AT-IT"),
    POI("op_20", "Predilpass",           "pass", 46.41250, 13.57500, 1156,
        subtitle="Passo di Predil · IT-SI"),
]

CLASSIFICATION = POIClassification(
    name="paesse",
    title="Wichtigste Pässe",
    pois=PASSES,
    category_style={
        "pass": {"marker": "o", "color": "#2E86C1", "size": 12, "label": "Pass"},
    },
)
