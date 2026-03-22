"""
Classification: Ostalpen Gipfel (Hauptgipfel der Ostalpen)
==========================================================
Kuratierte Liste der bedeutendsten Berggipfel der Ostalpen.
Kriterien: Wikidata-verlinkt, hohe Prominenz (>500 m) oder besondere
           Bekanntheit für Segelflieger / Alpinisten.

Koordinaten und Höhen aus OpenStreetMap / Wikipedia (März 2026).
"""

from deck import POIClassification
from models import POI

# ─── Gipfel (Peaks only) ─────────────────────────────────────────────────────
PEAKS = [
    # ── Zentrale Ostalpen (Hohe Tauern / Ötztaler / Stubaier / Zillertaler) ──
    POI("og_01", "Großglockner",         "peak", 47.07455, 12.69439, 3798,
        subtitle="AVE 84 Nr. 40 · Glocknergruppe"),
    POI("og_02", "Großvenediger",        "peak", 47.10917, 12.34639, 3657,
        subtitle="AVE 84 Nr. 36 · Venedigergruppe"),
    POI("og_03", "Hochalmspitze",        "peak", 47.01528, 13.31889, 3360,
        subtitle="AVE 84 Nr. 44 · Ankogelgruppe"),
    POI("og_04", "Hocharn",              "peak", 47.06444, 12.98583, 3254,
        subtitle="AVE 84 Nr. 42 · Goldberggruppe"),
    POI("og_05", "Hochfeiler",           "peak", 46.96861, 11.70722, 3510,
        subtitle="AVE 84 Nr. 35 · Zillertaler Alpen"),
    POI("og_06", "Wildspitze",           "peak", 46.88472, 10.86722, 3768,
        subtitle="AVE 84 Nr. 30 · Ötztaler Alpen"),
    POI("og_07", "Zuckerhütl",           "peak", 46.97389, 11.12861, 3507,
        subtitle="AVE 84 Nr. 31 · Stubaier Alpen"),
    POI("og_08", "Ortler",               "peak", 46.50889, 10.54389, 3905,
        subtitle="AVE 84 Nr. 48a · Ortler-Alpen"),
    POI("og_09", "Piz Bernina",          "peak", 46.38073,  9.90942, 4049,
        subtitle="AVE 84 Nr. 66 · Bernina-Alpen"),
    POI("og_10", "Piz Linard",           "peak", 46.82667,  9.95139, 3411,
        subtitle="AVE 84 Nr. 26 · Silvretta"),
    # ── Nördliche Kalkalpen ───────────────────────────────────────────────────
    POI("og_11", "Zugspitze",            "peak", 47.42121, 10.98630, 2962,
        subtitle="AVE 84 Nr. 4 · Wetterstein"),
    POI("og_12", "Hoher Dachstein",      "peak", 47.47528, 13.60583, 2995,
        subtitle="AVE 84 Nr. 14 · Dachsteingebirge"),
    POI("og_13", "Hochkönig",            "peak", 47.42222, 13.05556, 2941,
        subtitle="AVE 84 Nr. 10 · Berchtesgadener Alpen"),
    POI("og_14", "Parseierspitze",       "peak", 47.17111, 10.46889, 3036,
        subtitle="AVE 84 Nr. 3b · Lechtaler Alpen"),
    POI("og_15", "Birkkarspitze",        "peak", 47.41132, 11.43756, 2749,
        subtitle="AVE 84 Nr. 5 · Karwendel"),
    # ── Südliche Ostalpen ────────────────────────────────────────────────────
    POI("og_16", "Triglav",              "peak", 46.37917, 13.83611, 2864,
        subtitle="AVE 84 Nr. 58 · Julische Alpen"),
    POI("og_17", "Marmolata",            "peak", 46.43833, 11.85972, 3343,
        subtitle="AVE 84 Nr. 52 · Dolomiten"),
    POI("og_18", "Presanella",           "peak", 46.22028, 10.60556, 3556,
        subtitle="AVE 84 Nr. 49 · Adamello-Presanella"),
    POI("og_19", "Hohe Warte",           "peak", 46.61583, 12.94222, 2780,
        subtitle="AVE 84 Nr. 57a · Karnischer Hauptkamm"),
    # ── Westliche Ostalpen ───────────────────────────────────────────────────
    POI("og_20", "Piz Kesch",            "peak", 46.62889,  9.88806, 3418,
        subtitle="AVE 84 Nr. 65 · Albula-Alpen"),
    POI("og_21", "Schesaplana",          "peak", 47.07417,  9.73778, 2964,
        subtitle="AVE 84 Nr. 25 · Rätikon"),
]

CLASSIFICATION = POIClassification(
    name="gipfel",
    title="Hauptgipfel",
    pois=PEAKS,
    category_style={
        "peak": {"marker": "^", "color": "#B22222", "size": 7, "label": "Gipfel"},
    },
)
