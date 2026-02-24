"""
Classification: SOIUSA STS (Ostalpen — Sottosezioni)
=======================================================
All 76 Sottosezioni (sub-sections) of the Eastern Alps according to the
Suddivisione Orografica Internazionale Unificata del Sistema Alpino
(SOIUSA, Sergio Marazzi, 2005).

Part II — Alpi Orientali:
  Sector A — Zentrale Ostalpen            (SZ 15–20, 21 STS)
  Sector B — Nördliche Ostalpen           (SZ 21–27, 28 STS)
  Sector C — Südliche Ostalpen            (SZ 28–36, 27 STS)

Hauptgruppen = parent Sezioni (22 groups, matching ostalpen_soiusa_sz.py).
Data source: ARPA Piemonte FeatureServer (dissolved from Gruppo level).
"""

from typing import List

from deck import Classification
from models import Gebirgsgruppe


# ─── Hauptgruppen = parent Sezioni ────────────────────────────────────────────

SZ15 = "Westliche Rätische Alpen"
SZ16 = "Östliche Rätische Alpen"
SZ17 = "Westliche Tauernalpen"
SZ18 = "Östliche Tauernalpen"
SZ19 = "Steirisch-Kärntnerische Alpen"
SZ20 = "Steirisches Randgebirge"
SZ21 = "Nordtiroler Kalkalpen"
SZ22 = "Bayerische Alpen"
SZ23 = "Tiroler Schieferalpen"
SZ24 = "Salzburger Nordalpen"
SZ25 = "Salzkammergut- und Oberösterreichische Alpen"
SZ26 = "Steirische Nordalpen"
SZ27 = "Niederösterreichische Alpen"
SZ28 = "Südliche Rätische Alpen"
SZ29 = "Bergamasker Alpen und Voralpen"
SZ30 = "Brescianer und Gardasee-Voralpen"
SZ31 = "Dolomiten"
SZ32 = "Venezianische Voralpen"
SZ33 = "Karnische und Gailtaler Alpen"
SZ34 = "Julische Alpen und Voralpen"
SZ35 = "Kärntner und Slowenische Alpen"
SZ36 = "Slowenische Voralpen"

HAUPTGRUPPEN = [
    SZ15, SZ16, SZ17, SZ18, SZ19, SZ20, SZ21, SZ22,
    SZ23, SZ24, SZ25, SZ26, SZ27, SZ28, SZ29, SZ30,
    SZ31, SZ32, SZ33, SZ34, SZ35, SZ36,
]


# ─── All 76 Sottosezioni ─────────────────────────────────────────────────────

GROUPS: List[Gebirgsgruppe] = [

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTOR A — Zentrale Ostalpen  (SZ 15–20)
    # ═══════════════════════════════════════════════════════════════════════════

    # SZ 15 — Westliche Rätische Alpen  (Alpi Retiche occidentali)
    Gebirgsgruppe("15.1", "Berninagruppe",                                SZ15, "Piz Bernina (4049 m)",                 "Alpi del Bernina"),
    Gebirgsgruppe("15.2", "Livigno-Alpen",                                SZ15, "Cima di Piazzi (3439 m)",              "Alpi di Livigno"),
    Gebirgsgruppe("15.3", "Albula-Alpen",                                 SZ15, "Piz Kesch (3418 m)",                   "Alpi dell'Albula"),
    Gebirgsgruppe("15.4", "Silvretta, Samnaun und Verwall",               SZ15, "Piz Linard (3411 m)",                  "Alpi del Silvretta, del Samnaun e del Verwall"),
    Gebirgsgruppe("15.5", "Plattagruppe",                                 SZ15, "Piz Platta (3392 m)",                  "Alpi del Platta"),
    Gebirgsgruppe("15.6", "Münstertaler Alpen",                           SZ15, "Piz Sesvenna (3204 m)",                "Alpi della Val Müstair"),
    Gebirgsgruppe("15.7", "Plessuralpen",                                 SZ15, "Aroser Rothorn (2980 m)",              "Alpi del Plessur"),
    Gebirgsgruppe("15.8", "Rätikon",                                      SZ15, "Schesaplana (2964 m)",                 "Rätikon"),

    # SZ 16 — Östliche Rätische Alpen  (Alpi Retiche orientali)
    Gebirgsgruppe("16.1", "Ötztaler Alpen",                               SZ16, "Wildspitze (3772 m)",                  "Alpi Venoste (Ötztaler Alpen)"),
    Gebirgsgruppe("16.2", "Stubaier Alpen",                               SZ16, "Zuckerhütl (3507 m)",                  "Alpi dello Stubai"),
    Gebirgsgruppe("16.3", "Sarntaler Alpen",                              SZ16, "Hirzer (2781 m)",                      "Alpi Sarentine (Sarntaler Alpen)"),

    # SZ 17 — Westliche Tauernalpen  (Alpi dei Tauri occidentali)
    Gebirgsgruppe("17.1", "Hohe Tauern",                                  SZ17, "Großglockner (3798 m)",                "Alti Tauri (Hohe Tauern)"),
    Gebirgsgruppe("17.2", "Zillertaler Alpen",                            SZ17, "Hochfeiler (3510 m)",                  "Alpi della Zillertal"),
    Gebirgsgruppe("17.3", "Defereggengebirge",                            SZ17, "Hochgall (3436 m)",                    "Alpi Pusteresi (Defereggen Alpen)"),
    Gebirgsgruppe("17.4", "Kreuzeckgruppe",                               SZ17, "Polinik (2784 m)",                     "Kreuzeckgruppe"),

    # SZ 18 — Östliche Tauernalpen  (Alpi dei Tauri orientali)
    Gebirgsgruppe("18.1", "Schladminger und Murauer Tauern",              SZ18, "Hochgolling (2863 m)",                 "Tauri di Schladming e di Murau"),
    Gebirgsgruppe("18.2", "Radstädter Tauern",                            SZ18, "Weißeck (2711 m)",                     "Tauri di Radstadt"),
    Gebirgsgruppe("18.3", "Wölzer und Rottenmanner Tauern",               SZ18, "Große Bösenstein (2449 m)",            "Tauri di Wölz e di Rottenmann"),
    Gebirgsgruppe("18.4", "Seckauer Tauern",                              SZ18, "Geierhaupt (2417 m)",                  "Tauri di Seckau"),

    # SZ 19 — Steirisch-Kärntnerische Alpen  (Alpi di Stiria e Carinzia)
    Gebirgsgruppe("19.1", "Gurktaler Alpen",                              SZ19, "Eisenhut (2441 m)",                    "Alpi della Gurktal"),
    Gebirgsgruppe("19.2", "Lavanttaler Alpen",                            SZ19, "Zirbitzkogel (2396 m)",                "Alpi della Lavanttal"),

    # SZ 20 — Steirisches Randgebirge  (Prealpi di Stiria)
    Gebirgsgruppe("20.1", "Nordwestliches Steirisches Randgebirge",       SZ20, "Ameringkogel (2184 m)",                "Prealpi nord-occidentali di Stiria"),
    Gebirgsgruppe("20.2", "Südwestliches Steirisches Randgebirge",        SZ20, "Großer Speikkogel (2140 m)",           "Prealpi sud-occidentali di Stiria"),
    Gebirgsgruppe("20.3", "Zentralsteirisches Randgebirge",               SZ20, "Stuhleck (1782 m)",                    "Prealpi centrali di Stiria"),
    Gebirgsgruppe("20.4", "Östliches Steirisches Randgebirge",            SZ20, "Hochwechsel (1743 m)",                 "Prealpi orientali di Stiria"),

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTOR B — Nördliche Ostalpen  (SZ 21–27)
    # ═══════════════════════════════════════════════════════════════════════════

    # SZ 21 — Nordtiroler Kalkalpen  (Alpi Calcaree Nordtirolesi)
    Gebirgsgruppe("21.1", "Lechtaler Alpen",                              SZ21, "Parseierspitze (3036 m)",              "Alpi della Lechtal"),
    Gebirgsgruppe("21.2", "Mieminger Kette und Wettersteingebirge",       SZ21, "Zugspitze (2962 m)",                   "Monti di Mieming e del Wetterstein"),
    Gebirgsgruppe("21.3", "Karwendel",                                    SZ21, "Birkkarspitze (2749 m)",               "Monti del Karwendel"),
    Gebirgsgruppe("21.4", "Lechquellengebirge",                           SZ21, "Rote Wand (2704 m)",                   "Monti delle Lechquellen"),
    Gebirgsgruppe("21.5", "Kaisergebirge",                                SZ21, "Ellmauer Halt (2344 m)",               "Monti del Kaiser"),
    Gebirgsgruppe("21.6", "Brandenberger Alpen",                          SZ21, "Hochiss (2299 m)",                     "Alpi di Brandenberg"),

    # SZ 22 — Bayerische Alpen  (Alpi Bavaresi)
    Gebirgsgruppe("22.1", "Allgäuer Alpen",                               SZ22, "Großer Krottenkopf (2657 m)",          "Alpi dell'Algovia"),
    Gebirgsgruppe("22.2", "Ammergauer Alpen",                             SZ22, "Kreuzspitze (2185 m)",                 "Alpi dell'Ammergau"),
    Gebirgsgruppe("22.3", "Bregenzerwaldgebirge",                         SZ22, "Glatthorn (2134 m)",                   "Prealpi di Bregenz"),
    Gebirgsgruppe("22.4", "Wallgauer Alpen",                              SZ22, "Krottenkopf (2086 m)",                 "Alpi del Wallgau"),
    Gebirgsgruppe("22.5", "Chiemgauer Alpen",                             SZ22, "Sonntagshorn (1961 m)",                "Alpi del Chiemgau"),
    Gebirgsgruppe("22.6", "Mangfallgebirge",                              SZ22, "Rotwand (1884 m)",                     "Alpi del Mangfall"),

    # SZ 23 — Tiroler Schieferalpen  (Alpi Scistose Tirolesi)
    Gebirgsgruppe("23.1", "Tuxer Voralpen",                               SZ23, "Lizumer Reckner (2884 m)",             "Prealpi del Tux"),
    Gebirgsgruppe("23.2", "Kitzbüheler Alpen",                            SZ23, "Großer Rettenstein (2366 m)",          "Alpi di Kitzbühel"),

    # SZ 24 — Salzburger Nordalpen  (Alpi Settentrionali Salisburghesi)
    Gebirgsgruppe("24.1", "Berchtesgadener Alpen",                        SZ24, "Watzmann (2713 m)",                    "Alpi di Berchtesgaden"),
    Gebirgsgruppe("24.2", "Steinernes Meer und Steinberge",               SZ24, "Birnhorn (2634 m)",                    "Monti dello Stein"),
    Gebirgsgruppe("24.3", "Tennengebirge",                                SZ24, "Raucheck (2430 m)",                    "Monti di Tennen"),
    Gebirgsgruppe("24.4", "Salzburger Schieferalpen",                     SZ24, "Hundstein (2117 m)",                   "Alpi Scistose Salisburghesi"),

    # SZ 25 — Salzkammergut- und Oberösterreichische Alpen
    Gebirgsgruppe("25.1", "Dachsteingebirge",                             SZ25, "Hoher Dachstein (2995 m)",             "Monti del Dachstein"),
    Gebirgsgruppe("25.2", "Totes Gebirge",                                SZ25, "Großer Priel (2515 m)",                "Monti Totes"),
    Gebirgsgruppe("25.3", "Salzkammergut-Berge",                          SZ25, "Gamsfeld (2027 m)",                    "Monti del Salzkammergut"),
    Gebirgsgruppe("25.4", "Oberösterreichische Voralpen",                 SZ25, "Hoher Nock (1963 m)",                  "Prealpi dell'Alta Austria"),

    # SZ 26 — Steirische Nordalpen  (Alpi Settentrionali di Stiria)
    Gebirgsgruppe("26.1", "Ennstaler Alpen",                              SZ26, "Hochtor (2369 m)",                     "Alpi dell'Ennstal"),
    Gebirgsgruppe("26.2", "Nordöstliche Steirische Kalkalpen",            SZ26, "Hochschwab (2278 m)",                  "Alpi Nord-orientali di Stiria"),

    # SZ 27 — Niederösterreichische Alpen  (Alpi della Bassa Austria)
    Gebirgsgruppe("27.1", "Ybbstaler Alpen",                              SZ27, "Hochstadl (1919 m)",                   "Alpi dell'Ybbstal"),
    Gebirgsgruppe("27.2", "Östliche Niederösterreichische Voralpen",      SZ27, "Reisalpe (1399 m)",                    "Prealpi Orientali della Bassa Austria"),

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTOR C — Südliche Ostalpen  (SZ 28–36)
    # ═══════════════════════════════════════════════════════════════════════════

    # SZ 28 — Südliche Rätische Alpen  (Alpi Retiche meridionali)
    Gebirgsgruppe("28.1", "Ortlergruppe",                                 SZ28, "Ortler (3905 m)",                      "Alpi dell'Ortles"),
    Gebirgsgruppe("28.2", "Adamello-Presanella-Gruppe",                   SZ28, "Cima Presanella (3558 m)",             "Alpi dell'Adamello e della Presanella"),
    Gebirgsgruppe("28.3", "Brentadolomiten",                              SZ28, "Cima Tosa (3173 m)",                   "Dolomiti di Brenta"),
    Gebirgsgruppe("28.4", "Nonsberger Alpen",                             SZ28, "Monte Roen (2116 m)",                  "Alpi della Val di Non"),

    # SZ 29 — Bergamasker Alpen und Voralpen  (Alpi e Prealpi Bergamasche)
    Gebirgsgruppe("29.1", "Orobische Alpen",                              SZ29, "Pizzo di Coca (3052 m)",               "Alpi Orobie"),
    Gebirgsgruppe("29.2", "Bergamasker Voralpen",                         SZ29, "Pizzo Arera (2512 m)",                 "Prealpi Bergamasche"),

    # SZ 30 — Brescianer und Gardasee-Voralpen  (Prealpi Bresciane e Gardesane)
    Gebirgsgruppe("30.1", "Gardasee-Voralpen",                            SZ30, "Monte Cadria (2254 m)",                "Prealpi Gardesane"),
    Gebirgsgruppe("30.2", "Brescianer Voralpen",                          SZ30, "Monte Colombine (2215 m)",             "Prealpi Bresciane"),

    # SZ 31 — Dolomiten  (Dolomiti)
    Gebirgsgruppe("31.1", "Grödner und Fassaner Dolomiten",               SZ31, "Marmolada (3343 m)",                   "Dolomiti di Gardena e di Fassa"),
    Gebirgsgruppe("31.2", "Sextner, Pragser und Ampezzaner Dolomiten",    SZ31, "Antelao (3264 m)",                     "Dolomiti di Sesto, di Braies e d'Ampezzo"),
    Gebirgsgruppe("31.3", "Zoldaner Dolomiten",                           SZ31, "Civetta (3220 m)",                     "Dolomiti di Zoldo"),
    Gebirgsgruppe("31.4", "Feltriner Dolomiten und Pala",                 SZ31, "Cima della Vezzana (3192 m)",          "Dolomiti Feltrine e delle Pale di San Martino"),
    Gebirgsgruppe("31.5", "Fleimstaler Dolomiten",                        SZ31, "Cima d'Asta (2847 m)",                 "Dolomiti di Fiemme"),

    # SZ 32 — Venezianische Voralpen  (Prealpi Venete)
    Gebirgsgruppe("32.1", "Belluneser Voralpen",                          SZ32, "Col Nudo (2472 m)",                    "Prealpi Bellunesi"),
    Gebirgsgruppe("32.2", "Vicentiner Voralpen",                          SZ32, "Cima Dodici (2341 m)",                 "Prealpi vicentine"),

    # SZ 33 — Karnische und Gailtaler Alpen  (Alpi Carniche e della Gail)
    Gebirgsgruppe("33.1", "Karnische Alpen",                              SZ33, "Hohe Warte (2780 m)",                  "Alpi Carniche"),
    Gebirgsgruppe("33.2", "Gailtaler Alpen",                              SZ33, "Große Sandspitze (2772 m)",            "Gailtaler Alpen (Alpi della Gail)"),
    Gebirgsgruppe("33.3", "Karnische Voralpen",                           SZ33, "Cima dei Preti (2703 m)",              "Prealpi Carniche"),

    # SZ 34 — Julische Alpen und Voralpen  (Alpi e Prealpi Giulie)
    Gebirgsgruppe("34.1", "Julische Alpen",                               SZ34, "Triglav (2864 m)",                     "Alpi Giulie"),
    Gebirgsgruppe("34.2", "Julische Voralpen",                            SZ34, "Monte Musi (1869 m)",                  "Prealpi Giulie"),

    # SZ 35 — Kärntner und Slowenische Alpen  (Alpi di Carinzia e di Slovenia)
    Gebirgsgruppe("35.1", "Steiner Alpen",                                SZ35, "Grintovec (2558 m)",                   "Alpi di Kamnik e della Savinja"),
    Gebirgsgruppe("35.2", "Karawanken",                                   SZ35, "Hochstuhl (2236 m)",                   "Caravanche"),

    # SZ 36 — Slowenische Voralpen  (Prealpi Slovene)
    Gebirgsgruppe("36.1", "Westliche Slowenische Voralpen",               SZ36, "Porezen (1630 m)",                     "Prealpi Slovene occidentali"),
    Gebirgsgruppe("36.2", "Nordöstliche Slowenische Voralpen",            SZ36, "Velika Kopa (1542 m)",                 "Prealpi Slovene nord-orientali"),
    Gebirgsgruppe("36.3", "Östliche Slowenische Voralpen",                SZ36, "Kum (1220 m)",                         "Prealpi Slovene orientali"),
]


# ─── Colors (one per parent Sezione) ─────────────────────────────────────────
# Sector A (Zentral): purple/violet tones
# Sector B (Nord): cool tones (blue/teal/green)
# Sector C (Süd): warm tones (red/orange/gold)

CLASSIFICATION = Classification(
    name="soiusa_sts",
    title="SOIUSA Sottosezioni",
    groups=GROUPS,
    hauptgruppen=HAUPTGRUPPEN,
    colors={
        # ── Sector A — Zentrale Ostalpen ─────────────────────────────────────
        SZ15: {"fill": "#8E44AD", "border": "#FFFFFF", "label": "15"},   # purple
        SZ16: {"fill": "#A569BD", "border": "#FFFFFF", "label": "16"},   # light purple
        SZ17: {"fill": "#6C3483", "border": "#FFFFFF", "label": "17"},   # deep purple
        SZ18: {"fill": "#BB8FCE", "border": "#FFFFFF", "label": "18"},   # lavender
        SZ19: {"fill": "#7D3C98", "border": "#FFFFFF", "label": "19"},   # violet
        SZ20: {"fill": "#D2B4DE", "border": "#333333", "label": "20"},   # pastel violet
        # ── Sector B — Nördliche Ostalpen ────────────────────────────────────
        SZ21: {"fill": "#2E86C1", "border": "#FFFFFF", "label": "21"},   # blue
        SZ22: {"fill": "#17A589", "border": "#FFFFFF", "label": "22"},   # teal-green
        SZ23: {"fill": "#1ABC9C", "border": "#FFFFFF", "label": "23"},   # turquoise
        SZ24: {"fill": "#3498DB", "border": "#FFFFFF", "label": "24"},   # sky blue
        SZ25: {"fill": "#27AE60", "border": "#FFFFFF", "label": "25"},   # green
        SZ26: {"fill": "#2980B9", "border": "#FFFFFF", "label": "26"},   # dark blue
        SZ27: {"fill": "#196F3D", "border": "#FFFFFF", "label": "27"},   # forest green
        # ── Sector C — Südliche Ostalpen ─────────────────────────────────────
        SZ28: {"fill": "#C0392B", "border": "#FFFFFF", "label": "28"},   # crimson
        SZ29: {"fill": "#E96B56", "border": "#FFFFFF", "label": "29"},   # coral
        SZ30: {"fill": "#D4A017", "border": "#FFFFFF", "label": "30"},   # gold
        SZ31: {"fill": "#E67E22", "border": "#FFFFFF", "label": "31"},   # orange
        SZ32: {"fill": "#E74C3C", "border": "#FFFFFF", "label": "32"},   # bright red
        SZ33: {"fill": "#A93226", "border": "#FFFFFF", "label": "33"},   # dark red
        SZ34: {"fill": "#D35400", "border": "#FFFFFF", "label": "34"},   # burnt orange
        SZ35: {"fill": "#CB4335", "border": "#FFFFFF", "label": "35"},   # red
        SZ36: {"fill": "#F39C12", "border": "#FFFFFF", "label": "36"},   # amber
    },
    osm_tag="STS",
    osm_fallback_ids={},
    parent_osm_tag="SZ",
)
