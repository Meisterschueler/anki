"""
Classification: AVE 84 (Alpenvereinseinteilung der Ostalpen)
=============================================================
All 75 Gebirgsgruppen according to the 1984 revision.
"""

from typing import List

from deck import Classification
from models import Gebirgsgruppe


# ─── Hauptgruppen (Main Divisions) ───────────────────────────────────────────
NORD = "Nördliche Ostalpen"
ZENTRAL = "Zentrale Ostalpen"
SUED = "Südliche Ostalpen"
WEST = "Westliche Ostalpen"

HAUPTGRUPPEN = [NORD, ZENTRAL, SUED, WEST]

# ─── All 75 Gebirgsgruppen ───────────────────────────────────────────────────
GROUPS: List[Gebirgsgruppe] = [
    # ═══════════════════════════════════════════════════════════════════════════
    # NÖRDLICHE OSTALPEN (Northern Limestone Alps) — 27 groups
    # ═══════════════════════════════════════════════════════════════════════════
    Gebirgsgruppe("1",   "Bregenzerwaldgebirge",           NORD, "Glatthorn (2134 m)",              "01"),
    Gebirgsgruppe("2",   "Allgäuer Alpen",                 NORD, "Großer Krottenkopf (2657 m)",     "02"),
    Gebirgsgruppe("3a",  "Lechquellengebirge",             NORD, "Große Wildgrubenspitze (2753 m)", "03a"),
    Gebirgsgruppe("3b",  "Lechtaler Alpen",                NORD, "Parseierspitze (3036 m)",         "03b"),
    Gebirgsgruppe("4",   "Wettersteingebirge und Mieminger Kette", NORD, "Zugspitze (2962 m)",     "04"),
    Gebirgsgruppe("5",   "Karwendel",                      NORD, "Birkkarspitze (2749 m)",          "05"),
    Gebirgsgruppe("6",   "Brandenberger Alpen",            NORD, "Hochiss (2299 m)",                "06"),
    Gebirgsgruppe("7a",  "Ammergauer Alpen",               NORD, "Daniel (2340 m)",                 "07a"),
    Gebirgsgruppe("7b",  "Bayerische Voralpen",            NORD, "Krottenkopf (2086 m)",            "07b"),
    Gebirgsgruppe("8",   "Kaisergebirge",                  NORD, "Ellmauer Halt (2344 m)",          "08"),
    Gebirgsgruppe("9",   "Loferer und Leoganger Steinberge", NORD, "Birnhorn (2634 m)",             "09"),
    Gebirgsgruppe("10",  "Berchtesgadener Alpen",          NORD, "Hochkönig (2941 m)",              "10"),
    Gebirgsgruppe("11",  "Chiemgauer Alpen",               NORD, "Sonntagshorn (1961 m)",           "11"),
    Gebirgsgruppe("12",  "Salzburger Schieferalpen",       NORD, "Hundstein (2117 m)",              "12"),
    Gebirgsgruppe("13",  "Tennengebirge",                  NORD, "Raucheck (2430 m)",               "13"),
    Gebirgsgruppe("14",  "Dachsteingebirge",               NORD, "Hoher Dachstein (2995 m)",        "14"),
    Gebirgsgruppe("15",  "Totes Gebirge",                  NORD, "Großer Priel (2515 m)",           "15"),
    Gebirgsgruppe("16",  "Ennstaler Alpen",                NORD, "Hochtor (2369 m)",                "16"),
    Gebirgsgruppe("17a", "Salzkammergut-Berge",            NORD, "Gamsfeld (2027 m)",               "17a"),
    Gebirgsgruppe("17b", "Oberösterreichische Voralpen",   NORD, "Hoher Nock (1963 m)",             "17b"),
    Gebirgsgruppe("18",  "Hochschwabgruppe",               NORD, "Hochschwab (2277 m)",             "18"),
    Gebirgsgruppe("19",  "Mürzsteger Alpen",               NORD, "Hohe Veitsch (1981 m)",           "19"),
    Gebirgsgruppe("20",  "Rax-Schneeberg-Gruppe",          NORD, "Klosterwappen (2076 m)",          "20"),
    Gebirgsgruppe("21",  "Ybbstaler Alpen",                NORD, "Hochstadl (1919 m)",              "21"),
    Gebirgsgruppe("22",  "Türnitzer Alpen",                NORD, "Großer Sulzberg (1400 m)",        "22"),
    Gebirgsgruppe("23",  "Gutensteiner Alpen",             NORD, "Reisalpe (1399 m)",               "23"),
    Gebirgsgruppe("24",  "Wienerwald",                     NORD, "Schöpfl (893 m)",                 "24"),

    # ═══════════════════════════════════════════════════════════════════════════
    # ZENTRALE OSTALPEN (Central Eastern Alps) — 27 groups
    # ═══════════════════════════════════════════════════════════════════════════
    Gebirgsgruppe("25",  "Rätikon",                        ZENTRAL, "Schesaplana (2964 m)",           "25"),
    Gebirgsgruppe("26",  "Silvretta",                      ZENTRAL, "Piz Linard (3411 m)",            "26"),
    Gebirgsgruppe("27",  "Samnaungruppe",                  ZENTRAL, "Muttler (3294 m)",               "27"),
    Gebirgsgruppe("28",  "Verwallgruppe",                  ZENTRAL, "Hoher Riffler (3168 m)",         "28"),
    Gebirgsgruppe("29",  "Sesvennagruppe",                 ZENTRAL, "Piz Sesvenna (3204 m)",          "29"),
    Gebirgsgruppe("30",  "Ötztaler Alpen",                 ZENTRAL, "Wildspitze (3768 m)",            "30"),
    Gebirgsgruppe("31",  "Stubaier Alpen",                 ZENTRAL, "Zuckerhütl (3507 m)",            "31"),
    Gebirgsgruppe("32",  "Sarntaler Alpen",                ZENTRAL, "Hirzer (2781 m)",                "32"),
    Gebirgsgruppe("33",  "Tuxer Alpen",                    ZENTRAL, "Lizumer Reckner (2884 m)",       "33"),
    Gebirgsgruppe("34",  "Kitzbüheler Alpen",              ZENTRAL, "Kreuzjoch (2558 m)",             "34"),
    Gebirgsgruppe("35",  "Zillertaler Alpen",              ZENTRAL, "Hochfeiler (3510 m)",            "35"),
    Gebirgsgruppe("36",  "Venedigergruppe",                ZENTRAL, "Großvenediger (3657 m)",         "36"),
    Gebirgsgruppe("37",  "Rieserfernergruppe",             ZENTRAL, "Hochgall (3436 m)",              "37"),
    Gebirgsgruppe("38",  "Villgratner Berge",              ZENTRAL, "Weiße Spitze (2962 m)",          "38"),
    Gebirgsgruppe("39",  "Granatspitzgruppe",              ZENTRAL, "Großer Muntanitz (3232 m)",      "39"),
    Gebirgsgruppe("40",  "Glocknergruppe",                 ZENTRAL, "Großglockner (3798 m)",          "40"),
    Gebirgsgruppe("41",  "Schobergruppe",                  ZENTRAL, "Petzeck (3283 m)",               "41"),
    Gebirgsgruppe("42",  "Goldberggruppe",                 ZENTRAL, "Hocharn (3254 m)",               "42"),
    Gebirgsgruppe("43",  "Kreuzeckgruppe",                 ZENTRAL, "Polinik (2784 m)",               "43"),
    Gebirgsgruppe("44",  "Ankogelgruppe",                  ZENTRAL, "Hochalmspitze (3360 m)",         "44"),
    Gebirgsgruppe("45a", "Radstädter Tauern",              ZENTRAL, "Weißeck (2711 m)",               "45a"),
    Gebirgsgruppe("45b", "Schladminger Tauern",            ZENTRAL, "Hochgolling (2862 m)",           "45b"),
    Gebirgsgruppe("45c", "Rottenmanner und Wölzer Tauern", ZENTRAL, "Rettlkirchspitze (2475 m)",      "45c"),
    Gebirgsgruppe("45d", "Seckauer Tauern",                ZENTRAL, "Geierhaupt (2417 m)",            "45d"),
    Gebirgsgruppe("46a", "Gurktaler Alpen",                ZENTRAL, "Eisenhut (2441 m)",              "46a"),
    Gebirgsgruppe("46b", "Lavanttaler Alpen",              ZENTRAL, "Zirbitzkogel (2396 m)",          "46b"),
    Gebirgsgruppe("47",  "Randgebirge östlich der Mur",    ZENTRAL, "Stuhleck (1782 m)",              "47"),

    # ═══════════════════════════════════════════════════════════════════════════
    # SÜDLICHE OSTALPEN (Southern Limestone Alps) — 15 groups
    # ═══════════════════════════════════════════════════════════════════════════
    Gebirgsgruppe("48a", "Ortler-Alpen",                   SUED, "Ortler (3905 m)",                 "48a"),
    Gebirgsgruppe("48b", "Sobretta-Gavia-Gruppe",          SUED, "Monte Sobretta (3296 m)",         "48b"),
    Gebirgsgruppe("48c", "Nonsberggruppe",                 SUED, "Laugenspitze (2434 m)",           "48c"),
    Gebirgsgruppe("49",  "Adamello-Presanella-Alpen",      SUED, "Presanella (3556 m)",             "49"),
    Gebirgsgruppe("50",  "Gardaseeberge",                  SUED, "Monte Cadria (2254 m)",           "50"),
    Gebirgsgruppe("51",  "Brentagruppe",                   SUED, "Cima Tosa (3173 m)",              "51"),
    Gebirgsgruppe("52",  "Dolomiten",                      SUED, "Marmolada (3343 m)",              "52"),
    Gebirgsgruppe("53",  "Fleimstaler Alpen",              SUED, "Cima d'Asta (2847 m)",            "53"),
    Gebirgsgruppe("54",  "Vizentiner Alpen",               SUED, "Cima Dodici (2336 m)",            "54"),
    Gebirgsgruppe("56",  "Gailtaler Alpen",                SUED, "Große Sandspitze (2770 m)",       "56"),
    Gebirgsgruppe("57a", "Karnischer Hauptkamm",           SUED, "Hohe Warte (2780 m)",             "57a"),
    Gebirgsgruppe("57b", "Südliche Karnische Alpen",       SUED, "Cima dei Preti (2706 m)",         "57b"),
    Gebirgsgruppe("58",  "Julische Alpen",                 SUED, "Triglav (2864 m)",                "58"),
    Gebirgsgruppe("59",  "Karawanken und Bachergebirge",   SUED, "Hochstuhl (2237 m)",              "59"),
    Gebirgsgruppe("60",  "Steiner Alpen",                  SUED, "Grintovec (2558 m)",              "60"),

    # ═══════════════════════════════════════════════════════════════════════════
    # WESTLICHE OSTALPEN (Western Eastern Alps) — 6 groups
    # ═══════════════════════════════════════════════════════════════════════════
    Gebirgsgruppe("63",  "Plessur-Alpen",                  WEST, "Aroser Rothorn (2980 m)",         "63"),
    Gebirgsgruppe("64",  "Oberhalbsteiner Alpen",          WEST, "Piz Platta (3392 m)",             "64"),
    Gebirgsgruppe("65",  "Albula-Alpen",                   WEST, "Piz Kesch (3418 m)",              "65"),
    Gebirgsgruppe("66",  "Bernina",                        WEST, "Piz Bernina (4049 m)",            "66"),
    Gebirgsgruppe("67",  "Livigno-Alpen",                  WEST, "Cima de' Piazzi (3439 m)",        "67"),
    Gebirgsgruppe("68",  "Bergamasker Alpen",              WEST, "Pizzo di Coca (3052 m)",          "68"),
]


CLASSIFICATION = Classification(
    name="ave84",
    title="AVE 84",
    groups=GROUPS,
    hauptgruppen=HAUPTGRUPPEN,
    colors={
        "Nördliche Ostalpen": {
            "fill": "#4A90D9",
            "border": "#FFFFFF", "label": "N",
        },
        "Zentrale Ostalpen": {
            "fill": "#FF9500",
            "border": "#FFFFFF", "label": "Z",
        },
        "Südliche Ostalpen": {
            "fill": "#28A745",
            "border": "#FFFFFF", "label": "S",
        },
        "Westliche Ostalpen": {
            "fill": "#DC3545",
            "border": "#FFFFFF", "label": "W",
        },
    },
    osm_tag="ref:aveo",
)
