"""
Peak Soaring POIs — Points of Interest for glider pilots
=========================================================
Based on the book "Peak Soaring" by Benjamin Bachmaier.

40 POIs across the Northern Alps:
  - 25 peaks  (▲)
  -  7 passes (⬤)
  -  4 valleys (polygon)
  -  4 towns  (■)
"""

from models import POI

# ═══════════════════════════════════════════════════════════════════════════════
# PEAKS  (25)
# ═══════════════════════════════════════════════════════════════════════════════

PEAKS = [
    POI("peak_01", "Blomberg",                    "peak", 47.73354, 11.50729, 1236),
    POI("peak_02", "Rabenkopf",                   "peak", 47.65037, 11.41202, 1555),
    POI("peak_03", "Benediktenwand",              "peak", 47.65317, 11.46554, 1800),
    POI("peak_04", "Latschenkopf",                "peak", 47.65659, 11.49903, 1488),
    POI("peak_05", "Jochberg",                    "peak", 47.62594, 11.37186, 1565),
    POI("peak_06", "Heimgarten",                  "peak", 47.59273, 11.31499, 1791),
    POI("peak_07", "Hirschberg",                  "peak", 47.66076, 11.69611, 1670,
        subtitle="Mittagsspitze"),
    POI("peak_08", "Hohe Kisten",                 "peak", 47.56110, 11.20797, 1922),
    POI("peak_09", "Wank",                        "peak", 47.50871, 11.14303, 1780),
    POI("peak_10", "Kramerspitz",                 "peak", 47.50688, 11.04726, 1985),
    POI("peak_11", "Schlossberg",                 "peak", 47.60500, 11.40500, 1283),
    POI("peak_12", "Zugspitze",                   "peak", 47.42121, 10.98630, 2962),
    POI("peak_13", "Birkkarspitze",               "peak", 47.41132, 11.43756, 2749),
    POI("peak_14", "Westl. Karwendelspitze",      "peak", 47.43002, 11.29886, 2385),
    POI("peak_15", "Östl. Karwendelspitze",       "peak", 47.44486, 11.42143, 2537),
    POI("peak_16", "Nockspitze",                  "peak", 47.19207, 11.32472, 2404,
        subtitle="Saile"),
    POI("peak_17", "Bettelwurf",                  "peak", 47.34423, 11.51987, 2726),
    POI("peak_18", "Hafelekar",                   "peak", 47.31674, 11.39331, 2334),
    POI("peak_19", "Brandjoch",                   "peak", 47.30224, 11.34154, 2559,
        subtitle="Vordere Brandjochspitze"),
    POI("peak_20", "Stanser Joch",                "peak", 47.40015, 11.68706, 2102),
    POI("peak_21", "Bärenkopf",                   "peak", 47.41479, 11.71227, 1991),
    POI("peak_22", "Voldöppberg",                 "peak", 47.47442, 11.88839, 1509),
    POI("peak_23", "Kienberg",                    "peak", 47.51556, 11.94917, 1786),
    POI("peak_24", "Wallberg",                    "peak", 47.66588, 11.79675, 1722),
    POI("peak_25", "Pendling",                    "peak", 47.57125, 12.10902, 1563),
]

# ═══════════════════════════════════════════════════════════════════════════════
# PASSES  (7)
# ═══════════════════════════════════════════════════════════════════════════════

PASSES = [
    POI("pass_01", "Gerlospass",                  "pass", 47.24286, 12.10939, 1507),
    POI("pass_02", "Pass Thurn",                  "pass", 47.30859, 12.40849, 1274),
    POI("pass_03", "Fernpass",                    "pass", 47.36392, 10.83494, 1216),
    POI("pass_04", "Reschenpass",                 "pass", 46.83435, 10.51025, 1507),
    POI("pass_05", "Ofenpass",                    "pass", 46.63977, 10.29219, 2149),
    POI("pass_06", "Berninapass",                 "pass", 46.41578, 10.01148, 2328),
    POI("pass_07", "Malojapass",                  "pass", 46.39994,  9.69581, 1815),
]

# ═══════════════════════════════════════════════════════════════════════════════
# TOWNS  (4)
# ═══════════════════════════════════════════════════════════════════════════════

TOWNS = [
    POI("town_01", "Landeck",                     "town", 47.14241, 10.57046),
    POI("town_02", "Imst",                        "town", 47.23815, 10.74070),
    POI("town_03", "Pfunds",                      "town", 46.99845, 10.58300),
    POI("town_04", "Tösens",                      "town", 47.01771, 10.60768),
]

# ═══════════════════════════════════════════════════════════════════════════════
# VALLEYS  (4)  — centroid coordinates; actual polygons from OSM later
# ═══════════════════════════════════════════════════════════════════════════════

VALLEYS = [
    POI("valley_01", "Oberinntal",                "valley", 47.26248, 10.90077),
    POI("valley_02", "Lechtal",                   "valley", 47.26266, 10.38147),
    POI("valley_03", "Illertal",                  "valley", 47.50648, 10.27214),
    POI("valley_04", "Montafon",                  "valley", 47.04450,  9.94359),
]

# ═══════════════════════════════════════════════════════════════════════════════
# ALL POIs combined
# ═══════════════════════════════════════════════════════════════════════════════

ALL_POIS = PEAKS + PASSES + TOWNS + VALLEYS

# ── Category display properties ──────────────────────────────────────────────
CATEGORY_STYLE = {
    "peak":   {"marker": "^", "color": "#B22222", "size": 7, "label": "Gipfel"},
    "pass":   {"marker": "o", "color": "#2E86C1", "size": 6, "label": "Pass"},
    "town":   {"marker": "s", "color": "#1A1A1A", "size": 5, "label": "Ort"},
    "valley": {"marker": "D", "color": "#27AE60", "size": 5, "label": "Tal"},
}
