"""
Peak Soaring POIs — Points of Interest for glider pilots
=========================================================
Based on the book "Peak Soaring" by Benjamin Bachmaier.

209 POIs across the Alps:
  - 78 peaks  (▲)
  - 59 passes (⬤)
  - 22 valleys (◆)
  - 43 towns  (■)
  -  7 lakes  (⬡)

Coordinates verified against Wikipedia / OpenStreetMap (June 2025).
A few POIs without reliable source are marked with '# approx' or
'# not found on OSM' inline.
"""

import math

from models import POI

# Reference airfields for sorting by distance (nearest first)
_KOENIGSDORF_LAT, _KOENIGSDORF_LON = 47.820, 11.480   # EDNK
_PUIMOISSON_LAT, _PUIMOISSON_LON   = 43.883,  6.167   # LFGEN
_SORT_ORIGIN = {
    "ostalpen":  (_KOENIGSDORF_LAT, _KOENIGSDORF_LON),
    "westalpen": (_PUIMOISSON_LAT, _PUIMOISSON_LON),
}


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in km between two WGS84 points."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# ═══════════════════════════════════════════════════════════════════════════════
# PEAKS  (78)
# ═══════════════════════════════════════════════════════════════════════════════

PEAKS = [
    POI("peak_01", "Blomberg",                     "peak", 47.73333, 11.49167, 1236),
    POI("peak_02", "Rabenkopf",                    "peak", 47.65037, 11.41202, 1555),
    POI("peak_03", "Benediktenwand",               "peak", 47.65317, 11.46554, 1800),
    POI("peak_04", "Latschenkopf",                 "peak", 47.65659, 11.49903, 1488),
    POI("peak_05", "Jochberg",                     "peak", 47.62594, 11.37186, 1565),
    POI("peak_06", "Heimgarten",                   "peak", 47.61361, 11.28194, 1791),
    POI("peak_07", "Hirschberg",                   "peak", 47.66076, 11.69611, 1670,
        subtitle="Mittagsspitze"),
    POI("peak_08", "Hohe Kisten",                  "peak", 47.56110, 11.20797, 1922),
    POI("peak_09", "Wank",                         "peak", 47.50871, 11.14303, 1780),
    POI("peak_10", "Kramerspitz",                  "peak", 47.50688, 11.04726, 1985),
    POI("peak_11", "Schlossberg",                  "peak", 47.46073, 10.69878, 1283),  # bei Reutte/Ehrenberg
    POI("peak_12", "Zugspitze",                    "peak", 47.42121, 10.98630, 2962),
    POI("peak_13", "Birkkarspitze",                "peak", 47.41132, 11.43756, 2749),
    POI("peak_14", "Westl. Karwendelspitze",       "peak", 47.43002, 11.29886, 2385),
    POI("peak_15", "Östl. Karwendelspitze",        "peak", 47.44486, 11.42143, 2537),
    POI("peak_16", "Bettelwurf",                   "peak", 47.34423, 11.51987, 2726),
    POI("peak_17", "Hafelekar",                    "peak", 47.31278, 11.38639, 2334),
    POI("peak_18", "Brandjoch",                    "peak", 47.29530, 11.33560, 2599,
        subtitle="Hintere Brandjochspitze"),
    POI("peak_19", "Stanser Joch",                 "peak", 47.39944, 11.69889, 2102),
    POI("peak_20", "Bärenkopf",                    "peak", 47.41479, 11.71227, 1991),
    POI("peak_21", "Voldöppberg",                  "peak", 47.47442, 11.88839, 1509),
    POI("peak_22", "Kienberg",                     "peak", 47.51556, 11.94917, 1786),
    POI("peak_23", "Wallberg",                     "peak", 47.66588, 11.79675, 1722),
    POI("peak_24", "Pendling",                     "peak", 47.57125, 12.10902, 1563),
    POI("peak_25", "Großglockner",                 "peak", 47.07455, 12.69439, 3798),
    POI("peak_26", "Türchelkopf",                  "peak", 47.23864, 12.77799, 2134),
    POI("peak_27", "Großvenediger",                "peak", 47.10917, 12.34639, 3657),
    POI("peak_28", "Sandspitze",                   "peak", 46.76667, 12.81167, 2770),
    POI("peak_29", "Bischofsmütze",                "peak", 47.49389, 13.51111, 2458),
    POI("peak_30", "Rossbrand",                    "peak", 47.41528, 13.47889, 1770),
    POI("peak_31", "Dachstein",                    "peak", 47.47528, 13.60583, 2995),
    POI("peak_32", "Gscheuerwand",                 "peak", 47.72049, 12.43402, 1106),
    POI("peak_33", "Eiger",                        "peak", 46.57763,  8.00547, 3967),
    POI("peak_34", "Mönch",                        "peak", 46.55850,  7.99727, 4110),
    POI("peak_35", "Jungfrau",                     "peak", 46.53677,  7.96259, 4158),
    POI("peak_36", "Weißhorn",                     "peak", 46.10123,  7.71615, 4505),
    POI("peak_37", "Dom",                          "peak", 46.09393,  7.85887, 4545),
    POI("peak_38", "Oberrothorn",                  "peak", 46.02754,  7.81280, 3413),
    POI("peak_39", "Gornergrat",                   "peak", 45.98360,  7.78470, 3100),
    POI("peak_40", "Matterhorn",                   "peak", 45.97640,  7.65860, 4478),
    POI("peak_41", "Grand Combin",                 "peak", 45.93758,  7.29922, 4309),
    POI("peak_42", "Grandes Jorasses",             "peak", 45.86816,  6.98898, 4208),
    POI("peak_43", "Mont Blanc",                   "peak", 45.83271,  6.86517, 4806),
    POI("peak_44", "Grivola",                      "peak", 45.59600,  7.25744, 3969),
    POI("peak_45", "Gran Paradiso",                "peak", 45.51782,  7.26720, 4061),
    POI("peak_46", "Grande Casse",                 "peak", 45.40514,  6.82756, 3855),
    POI("peak_47", "Grand Roc Noir",               "peak", 45.33028,  6.89194, 3587),
    POI("peak_48", "Dent Parrachée",               "peak", 45.28909,  6.75608, 3697),
    POI("peak_49", "Pointe de Charbonnel",         "peak", 45.28047,  7.05568, 3752),
    POI("peak_50", "Pic de Rochebrune",            "peak", 44.82229,  6.78751, 3320),
    POI("peak_51", "La Meije",                     "peak", 45.00504,  6.30825, 3982),
    POI("peak_52", "Crête de Peyrolle",            "peak", 44.94240,  6.64390, 2618),  # approx, near Grande Peyrolle
    POI("peak_53", "Barre des Écrins",             "peak", 44.92216,  6.35955, 4102),
    POI("peak_54", "Monte Viso",                   "peak", 44.66744,  7.08999, 3841),
    POI("peak_55", "Mont Guillaume",               "peak", 44.58542,  6.43710, 2545),
    POI("peak_56", "Grand Bérard",                 "peak", 44.44973,  6.66027, 3046),
    POI("peak_57", "Dormillouse",                  "peak", 44.96559,  6.71314, 2510),
    POI("peak_58", "Chapeau de Gendarme",          "peak", 44.65000,  6.30000, 2682),  # not found on OSM
    POI("peak_59", "Les Trois Évêchés",            "peak", 44.28914, 6.53410, 2818),
    POI("peak_60", "Glandasse",                    "peak", 44.74189,  5.46343, 2041),
    POI("peak_61", "Merlu",                        "peak", 44.48777,  5.25752, 1540),
    POI("peak_62", "Pic de Bure",                  "peak", 44.62666,  5.93508, 2709),
    POI("peak_63", "Saint-Apôtre",                 "peak", 44.54085,  5.74450, 1491),
    POI("peak_64", "Montagne de Saint-Genis",      "peak", 44.39140,  5.83750, 1432),
    POI("peak_65", "Arambre",                      "peak", 44.43020,  5.74519, 1444),
    POI("peak_66", "Montagne de Chabre",           "peak", 44.26583, 5.64278, 1393),
    POI("peak_67", "Sommet de Bluye",              "peak", 44.23060,  5.25464, 1120),
    POI("peak_68", "Pic du Comte",                 "peak", 44.19779,  5.23966, 1154),
    POI("peak_69", "Mont Ventoux",                 "peak", 44.17396,  5.27840, 1909),
    POI("peak_70", "Montagne de Lure",             "peak", 44.12333, 5.80278, 1826),
    POI("peak_71", "Montagne de Jouère",           "peak", 44.27440,  6.10581, 1886),
    POI("peak_72", "Montagne de Gache",            "peak", 44.23391,  5.98769, 1357),
    POI("peak_73", "Blayeul",                      "peak", 44.24681,  6.31178, 2189),
    POI("peak_74", "Crête de Limans",              "peak", 44.08000,  5.83000, None),  # not found on OSM
    POI("peak_75", "Vachière",                     "peak", 44.15000,  6.10000, 2083),  # not found on OSM
    POI("peak_76", "Carton",                       "peak", 44.11407,  6.68163, 2123),
    POI("peak_77", "Cheval Blanc",                 "peak", 44.12701,  6.42381, 2323),
    POI("peak_78", "Serre de Montdenier",          "peak", 43.89788,  6.25498, 1750),
]

# ═══════════════════════════════════════════════════════════════════════════════
# PASSES  (59)
# ═══════════════════════════════════════════════════════════════════════════════

PASSES = [
    POI("pass_01", "Gerlospass",                   "pass", 47.24286, 12.10939, 1507),
    POI("pass_02", "Pass Thurn",                   "pass", 47.30859, 12.40849, 1274),
    POI("pass_03", "Fernpass",                     "pass", 47.36392, 10.83494, 1216),
    POI("pass_04", "Reschenpass",                  "pass", 46.83435, 10.51025, 1507),
    POI("pass_05", "Ofenpass",                     "pass", 46.63977, 10.29219, 2149),
    POI("pass_06", "Berninapass",                  "pass", 46.41578, 10.01148, 2328),
    POI("pass_07", "Malojapass",                   "pass", 46.39994,  9.69581, 1815),
    POI("pass_08", "Felbertauern",                 "pass", 47.14720, 12.48530, 1650),
    POI("pass_09", "Hochtor",                      "pass", 47.08170, 12.84280, 2504),
    POI("pass_10", "Korntauern",                   "pass", 47.09440, 13.07920, 2460),
    POI("pass_11", "Katschberg",                   "pass", 47.05940, 13.61610, 1641),
    POI("pass_12", "Turracherhöhe",                "pass", 46.91390, 13.87500, 1763),
    POI("pass_13", "Radstädter Tauern",            "pass", 47.26670, 13.50000, 1738),
    POI("pass_14", "Predilpass",                   "pass", 46.41250, 13.57500, 1156),
    POI("pass_15", "Wurzenpass",                   "pass", 46.51670, 13.75000, 1073),
    POI("pass_16", "Nassfeld",                     "pass", 46.55830, 13.28330, 1530),
    POI("pass_17", "Plöckenpass",                  "pass", 46.60280, 12.94440, 1357),
    POI("pass_18", "Kreuzbergsattel",              "pass", 46.65420, 12.78830, 1636),
    POI("pass_19", "Gailbergsattel",               "pass", 46.72500, 13.01670,  982),
    POI("pass_20", "Passo Tre Croci",              "pass", 46.56250, 12.21670, 1809),
    POI("pass_21", "Kartitscher Sattel",           "pass", 46.72280, 12.50280, 2174),
    POI("pass_22", "Campo Carlo Magno",            "pass", 46.23330, 10.86670, 1682),
    POI("pass_23", "Tonalepass",                   "pass", 46.26390, 10.58610, 1883),
    POI("pass_24", "Passo di Gavia",               "pass", 46.34170, 10.48890, 2621),
    POI("pass_25", "Stilfser Joch",                "pass", 46.52860, 10.45330, 2757),
    POI("pass_26", "Passo Rolle",                  "pass", 46.29720, 11.78610, 1984),
    POI("pass_27", "Pordoijoch",                   "pass", 46.48750, 11.81250, 2239),
    POI("pass_28", "Sellajoch",                    "pass", 46.50830, 11.76110, 2240),
    POI("pass_29", "Grödnerjoch",                  "pass", 46.55280, 11.80830, 2121),
    POI("pass_30", "Falzaregopass",                "pass", 46.52080, 12.00830, 2105),
    POI("pass_31", "Würzjoch",                     "pass", 46.68610, 11.68890, 2003),
    POI("pass_32", "Penser Joch",                  "pass", 46.83610, 11.44170, 2211),
    POI("pass_33", "Eisjöchl",                     "pass", 46.75000, 11.08330, 2895),
    POI("pass_34", "Timmelsjoch",                  "pass", 46.90000, 11.09170, 2474),
    POI("pass_35", "Brennerpass",                  "pass", 47.00420, 11.50750, 1370),
    POI("pass_36", "Holzleitensattel",             "pass", 47.35000, 10.93330, 1126),
    POI("pass_37", "Mädelejoch",                   "pass", 47.32500, 10.36670, 1974),
    POI("pass_38", "Arlbergpass",                  "pass", 47.12970, 10.21390, 1793),
    POI("pass_39", "Flüelapass",                   "pass", 46.74720, 9.94720, 2383),
    POI("pass_40", "Bieler Höhe",                  "pass", 46.91810, 10.09310, 2037),
    POI("pass_41", "Glaubenbielenpass",            "pass", 46.81881,  8.09317, 1611),
    POI("pass_42", "Brünigpass",                   "pass", 46.75640,  8.13760, 1008),
    POI("pass_43", "Lötschenlücke",                "pass", 46.47445,  7.96240, 3173),
    POI("pass_44", "Gemmipass",                    "pass", 46.39628,  7.61147, 2314),
    POI("pass_45", "Rawilpass",                    "pass", 46.38333,  7.44232, 2429),
    POI("pass_46", "Sanetschpass",                 "pass", 46.33157,  7.28623, 2252),
    POI("pass_47", "Col de Jambaz",                "pass", 46.23510,  6.52004, 1576),
    POI("pass_48", "Col de l'Encrenaz",            "pass", 46.17271,  6.63367, 1497),
    POI("pass_49", "Col des Montets",              "pass", 46.00391,  6.92363, 1461),
    POI("pass_50", "Simplonpass",                  "pass", 46.25021,  8.03168, 2005),
    POI("pass_51", "Theodulpass",                  "pass", 45.94350,  7.70871, 3295),
    POI("pass_52", "Großer St. Bernhard",          "pass", 45.86905,  7.17041, 2469),
    POI("pass_53", "Col Ferret",                   "pass", 45.88903,  7.07786, 2537),
    POI("pass_54", "Col du Petit St-Bernard",      "pass", 45.67925,  6.88294, 2188),
    POI("pass_55", "Col des Chavannes",            "pass", 45.74942,  6.83505, 2603),
    POI("pass_56", "Col du Joly",                  "pass", 45.78392,  6.67401, 1989),
    POI("pass_57", "Col des Aravis",               "pass", 45.87228,  6.46487, 1486),
    POI("pass_58", "Col du Marais",                "pass", 45.82430,  6.33428, 1750),
    POI("pass_59", "Col de Leschaux",              "pass", 45.77182,  6.13164, 1440),
]

# ═══════════════════════════════════════════════════════════════════════════════
# TOWNS  (43)
# ═══════════════════════════════════════════════════════════════════════════════

TOWNS = [
    POI("town_01", "Landeck",                      "town", 47.14241, 10.57046),
    POI("town_02", "Imst",                         "town", 47.23815, 10.74070),
    POI("town_03", "Pfunds",                       "town", 46.99845, 10.58300),
    POI("town_04", "Tösens",                       "town", 47.01771, 10.60768),
    POI("town_05", "Bozen",                        "town", 46.49830, 11.35480),
    POI("town_06", "Meran",                        "town", 46.67130, 11.15940),
    POI("town_07", "Prad",                         "town", 46.61670, 10.59170),
    POI("town_08", "Schluderns",                   "town", 46.66170, 10.58330),
    POI("town_09", "Saalfelden",                   "town", 47.42640, 12.84890),
    POI("town_10", "Kufstein",                     "town", 47.58330, 12.16670),
    POI("town_11", "Erl",                          "town", 47.63330, 12.18330),
    POI("town_12", "Bad Reichenhall",              "town", 47.72670, 12.87670),
    POI("town_13", "Salzburg",                     "town", 47.80950, 13.05500),
    POI("town_14", "Bischofshofen",                "town", 47.41670, 13.21670),
    POI("town_15", "St. Johann im Pongau",         "town", 47.35000, 13.20000),
    POI("town_16", "Radstadt",                     "town", 47.38330, 13.45830),
    POI("town_17", "Obertauern",                   "town", 47.25000, 13.56670),
    POI("town_18", "Wiener Neustadt",              "town", 47.81330, 16.24330),
    POI("town_19", "Maribor",                      "town", 46.55750, 15.64670),
    POI("town_20", "Füssen",                       "town", 47.57080, 10.70170),
    POI("town_21", "Ehrwald",                      "town", 47.39500, 10.91830),
    POI("town_22", "Kochel",                       "town", 47.65920, 11.36750),
    POI("town_23", "Garmisch-Partenkirchen",       "town", 47.49170, 11.09580),
    POI("town_24", "Telfs",                        "town", 47.30690, 11.07060),
    POI("town_25", "Vorderriss",                   "town", 47.49170, 11.42500),
    POI("town_26", "Benediktbeuern",               "town", 47.70830, 11.40280),
    POI("town_27", "Bad Tölz",                     "town", 47.76060, 11.55610),
    POI("town_28", "Spitzing",                     "town", 47.66170, 11.88580),
    POI("town_29", "Schönau",                      "town", 47.60000, 12.98330),
    POI("town_30", "Wörgl",                        "town", 47.48920, 12.06390),
    POI("town_31", "Domodossola",                  "town", 46.11525,  8.29205),
    POI("town_32", "Interlaken",                   "town", 46.68552,  7.85851),
    POI("town_33", "Modane",                       "town", 45.20154,  6.67282),
    POI("town_34", "Bardonecchia",                 "town", 45.07834,  6.70320),
    POI("town_35", "Ivrea",                        "town", 45.46738,  7.87480),
    POI("town_36", "Grenoble",                     "town", 45.18756,  5.73578),
    POI("town_37", "Champsaur",                    "town", 44.65872,  6.12946),
    POI("town_38", "Oulx",                         "town", 45.03305,  6.83251),
    POI("town_39", "Le Rosier",                    "town", 44.93907,  6.68053),
    POI("town_40", "Briançon",                     "town", 44.89840,  6.64363),
    POI("town_41", "La Faurie",                    "town", 44.56738,  5.73995),
    POI("town_42", "Châteauroux-les-Alpes",        "town", 44.61372,  6.52107),
    POI("town_43", "Saint-Crépin",                 "town", 44.70633,  6.60713),
]

# ═══════════════════════════════════════════════════════════════════════════════
# VALLEYS  (22)  — centroid coordinates; actual polygons from OSM later
# ═══════════════════════════════════════════════════════════════════════════════

VALLEYS = [
    POI("valley_01", "Oberinntal",                 "valley", 47.26248, 10.90077),
    POI("valley_02", "Lechtal",                    "valley", 47.26266, 10.38147),
    POI("valley_03", "Illertal",                   "valley", 47.50648, 10.27214),
    POI("valley_04", "Montafon",                   "valley", 47.04450,  9.94359),
    POI("valley_05", "Schnalstal",                 "valley", 46.71090, 10.87487),
    POI("valley_06", "Passeiertal",                "valley", 46.81200, 11.25500),
    POI("valley_07", "Pitztal",                    "valley", 47.07188, 10.81944),
    POI("valley_08", "Ötztal",                     "valley", 47.09655, 10.94460),
    POI("valley_09", "Wipptal",                    "valley", 46.99674, 11.47488),
    POI("valley_10", "Vinschgau",                  "valley", 46.66238, 10.74913),
    POI("valley_11", "Jachenau",                   "valley", 47.60000, 11.44000),
    POI("valley_12", "Mölltal",                    "valley", 46.93550, 13.01346),
    POI("valley_13", "Drautal",                    "valley", 46.73595, 13.60346),
    POI("valley_14", "Glemmtal",                   "valley", 47.37339, 12.64501),
    POI("valley_15", "Salzachtal",                 "valley", 47.36737, 12.85450),
    POI("valley_16", "Gailtal",                    "valley", 46.64336, 13.14412),
    POI("valley_17", "Ahrntal",                    "valley", 46.97500, 11.97500),
    POI("valley_18", "Gasteinertal",               "valley", 47.11170, 13.13170),
    POI("valley_19", "Rhonetal",                   "valley", 46.30000,  7.35000),
    POI("valley_20", "Mattertal",                  "valley", 46.10000,  7.78000),
    POI("valley_21", "Aostatal",                   "valley", 45.73000,  7.32000),
    POI("valley_22", "Baronnies",                  "valley", 44.27680,  5.27480),
]

# ═══════════════════════════════════════════════════════════════════════════════
# LAKES  (7)
# ═══════════════════════════════════════════════════════════════════════════════

LAKES = [
    POI("lake_01", "Reschensee",                   "lake", 46.81670, 10.53330, 1498),
    POI("lake_02", "Achensee",                     "lake", 47.43330, 11.71670,  929),
    POI("lake_03", "Tegernsee",                    "lake", 47.71300, 11.75830,  726),
    POI("lake_04", "Lago Maggiore",                "lake", 45.95000,  8.65000,  193),
    POI("lake_05", "Lac de Sainte-Croix",          "lake", 43.76000,  6.18000,  477),
    POI("lake_06", "Lac de Serre-Ponçon",          "lake", 44.53000,  6.33000,  780),
    POI("lake_07", "Genfer See",                   "lake", 46.45000,  6.52000,  372),
]

# ═══════════════════════════════════════════════════════════════════════════════
# ALL POIs combined
# ═══════════════════════════════════════════════════════════════════════════════

ALL_POIS = PEAKS + PASSES + TOWNS + VALLEYS + LAKES


def pois_for_region(region) -> list:
    """Return POIs within the region's bounding box, sorted by distance
    to the region's reference airfield (nearest first).

    Ostalpen  → Flugplatz Königsdorf
    Westalpen → Aérodrome de Puimoisson

    POIs in the overlap zone between Ost- and Westalpen appear in both decks.
    ``region`` must have bbox_south/north/west/east and name attributes.
    """
    filtered = [
        p for p in ALL_POIS
        if region.bbox_south <= p.lat <= region.bbox_north
        and region.bbox_west <= p.lon <= region.bbox_east
    ]
    origin = _SORT_ORIGIN.get(region.name, (_KOENIGSDORF_LAT, _KOENIGSDORF_LON))
    filtered.sort(key=lambda p: _haversine_km(origin[0], origin[1], p.lat, p.lon))
    return filtered


# ── Category display properties ──────────────────────────────────────────────
CATEGORY_STYLE = {
    "peak":   {"marker": "^", "color": "#B22222", "size": 7, "label": "Gipfel"},
    "pass":   {"marker": "o", "color": "#2E86C1", "size": 6, "label": "Pass"},
    "town":   {"marker": "s", "color": "#1A1A1A", "size": 5, "label": "Ort"},
    "valley": {"marker": "D", "color": "#27AE60", "size": 5, "label": "Tal"},
    "lake":   {"marker": "H", "color": "#17A2B8", "size": 6, "label": "See"},
}


# ═══════════════════════════════════════════════════════════════════════════════
# ABWEICHUNGEN: "Peak Soaring" (Buch) vs. OSM / Realität
# ═══════════════════════════════════════════════════════════════════════════════
#
# Die POI-Daten stammen aus dem Buch "Peak Soaring" von Benjamin Bachmaier.
# Koordinaten wurden gegen OSM (Nominatim) und Wikipedia verifiziert.
# Folgende Diskrepanzen zwischen Buch und OSM wurden festgestellt:
#
# ── Namensabweichungen ──────────────────────────────────────────────────────
#   Buch                    → OSM / hier verwendet       Anmerkung
#   "Nochspitze" (2547 m)  → "Nockspitze" (2404 m)     Vermutlich Tippfehler im Buch;
#                                                         Nockspitze/Saile bei Innsbruck;
#                                                         ENTFERNT — nicht im Buch bestätigt
#   "Hohe Kiste"            → "Hohe Kisten"              Plural auf OSM (NOT FOUND bei Nominatim)
#   "Volldöpp" (1509 m)     → "Voldöppberg"              Buch nutzt Ortsname statt Gipfelname
#   "Pass Turn"             → "Pass Thurn"               Tippfehler im Buch (fehlendes 'h')
#   "Col de l'Ancrenaz"     → "Col de l'Encrenaz"        Tippfehler im Buch ('A' statt 'E')
#   "Gscheuer Wand"         → "Gscheuerwand"             Zusammenschreibung auf OSM
#
# ── Höhenabweichungen ──────────────────────────────────────────────────────
#   Peak                    Buch     OSM       Δ         Anmerkung
#   Hafelekar               3599 m   2334 m  −1265 m    Offensichtlicher Druckfehler im Buch
#   Hirschberg              1660 m   1670 m    +10 m    Mittagsspitze; OSM-Wert übernommen
#   Nockspitze (entfernt)   2547 m   2404 m   −143 m    Nockspitze (Saile); Buch evtl. andere Spitze
#
# ── Koordinatenabweichungen ─────────────────────────────────────────────────
#   Peak                    Buch/Nominatim lat,lon         Hier verwendet
#   Blomberg                47.74423, 11.56852 (Straße)    47.73333, 11.49167 (Gipfel)
#   Heimgarten              47.59273, 11.31499 (Nominatim) 47.61361, 11.28194 (Gipfel)
#   Hafelekar               47.31674, 11.39331 (Nominatim) 47.31278, 11.38639 (Wikipedia-Gipfel)
#   Hirschberg              47.74452, 11.73957 (Straße)    47.66076, 11.69611 (Gipfel)
#   Wallberg                47.71713, 11.75782 (Nominatim) 47.66588, 11.79675 (Gipfel)
#   Stanser Joch            47.40015, 11.68706 (Nominatim) 47.39944, 11.69889 (Gipfel)
#   Voldöppberg             47.44383, 11.89366 (Ortsname)  47.47442, 11.88839 (Gipfel)
#   Schlossberg             NOT FOUND (Nominatim)          47.46073, 10.69878 (OSM node, Reutte)
#
# ── Nicht auf OSM gefunden ──────────────────────────────────────────────────
#   Latschenkopf, Jochberg, Birkkarspitze, Kienberg,
#   Malojapass, Schlossberg, Chapeau de Gendarme,
#   Crête de Limans, Vachière
#   → Koordinaten manuell aus Wikipedia oder Karte übernommen
#
# Quelle der Nominatim-Abfrage: _poi_coords.json (Lookup-Ergebnisse)
