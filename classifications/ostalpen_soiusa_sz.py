"""
Classification: SOIUSA SZ (Ostalpen — Sezioni)
=================================================
All 22 Sezioni (sections) of the Eastern Alps according to the
Suddivisione Orografica Internazionale Unificata del Sistema Alpino
(SOIUSA, Sergio Marazzi, 2005).

Part II — Alpi Orientali:
  Sector A — Zentrale Ostalpen            (SZ 15–20)
  Sector B — Nördliche Ostalpen           (SZ 21–27)
  Sector C — Südliche Ostalpen            (SZ 28–36)

Data source: ARPA Piemonte FeatureServer (dissolved from Gruppo level).
"""

from typing import List

from deck import Classification
from models import Gebirgsgruppe


# ─── Hauptgruppen (Sectors) ──────────────────────────────────────────────────

ZENTRAL = "Zentrale Ostalpen"
NORD    = "Nördliche Ostalpen"
SUED    = "Südliche Ostalpen"

HAUPTGRUPPEN = [ZENTRAL, NORD, SUED]

# ─── All 22 Sezioni ──────────────────────────────────────────────────────────

GROUPS: List[Gebirgsgruppe] = [
    # ═══════════════════════════════════════════════════════════════════════════
    # SECTOR A — Zentrale Ostalpen  (SZ 15–20)
    # ═══════════════════════════════════════════════════════════════════════════
    Gebirgsgruppe("15", "Westliche Rätische Alpen",                       ZENTRAL, "Piz Bernina (4049 m)",              "Alpi Retiche occidentali"),
    Gebirgsgruppe("16", "Östliche Rätische Alpen",                        ZENTRAL, "Wildspitze (3772 m)",               "Alpi Retiche orientali"),
    Gebirgsgruppe("17", "Westliche Tauernalpen",                          ZENTRAL, "Großglockner (3798 m)",             "Alpi dei Tauri occidentali"),
    Gebirgsgruppe("18", "Östliche Tauernalpen",                           ZENTRAL, "Hochgolling (2863 m)",              "Alpi dei Tauri orientali"),
    Gebirgsgruppe("19", "Steirisch-Kärntnerische Alpen",                  ZENTRAL, "Eisenhut (2441 m)",                 "Alpi di Stiria e Carinzia"),
    Gebirgsgruppe("20", "Steirisches Randgebirge",                        ZENTRAL, "Ameringkogel (2184 m)",             "Prealpi di Stiria"),

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTOR B — Nördliche Ostalpen  (SZ 21–27)
    # ═══════════════════════════════════════════════════════════════════════════
    Gebirgsgruppe("21", "Nordtiroler Kalkalpen",                          NORD,    "Parseierspitze (3036 m)",            "Alpi Calcaree Nordtirolesi"),
    Gebirgsgruppe("22", "Bayerische Alpen",                               NORD,    "Großer Krottenkopf (2657 m)",        "Alpi Bavaresi"),
    Gebirgsgruppe("23", "Tiroler Schieferalpen",                          NORD,    "Lizumer Reckner (2884 m)",           "Alpi Scistose Tirolesi"),
    Gebirgsgruppe("24", "Salzburger Nordalpen",                           NORD,    "Hochkönig (2941 m)",                 "Alpi Settentrionali Salisburghesi"),
    Gebirgsgruppe("25", "Salzkammergut- und Oberösterreichische Alpen",   NORD,    "Hoher Dachstein (2995 m)",           "Alpi del Salzkammergut e dell'Alta Austria"),
    Gebirgsgruppe("26", "Steirische Nordalpen",                           NORD,    "Hochtor (2369 m)",                   "Alpi Settentrionali di Stiria"),
    Gebirgsgruppe("27", "Niederösterreichische Alpen",                    NORD,    "Hochstadl (1919 m)",                 "Alpi della Bassa Austria"),

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTOR C — Südliche Ostalpen  (SZ 28–36)
    # ═══════════════════════════════════════════════════════════════════════════
    Gebirgsgruppe("28", "Südliche Rätische Alpen",                        SUED,    "Ortler (3905 m)",                    "Alpi Retiche meridionali"),
    Gebirgsgruppe("29", "Bergamasker Alpen und Voralpen",                 SUED,    "Pizzo di Coca (3052 m)",             "Alpi e Prealpi Bergamasche"),
    Gebirgsgruppe("30", "Brescianer und Gardasee-Voralpen",               SUED,    "Monte Cadria (2254 m)",              "Prealpi Bresciane e Gardesane"),
    Gebirgsgruppe("31", "Dolomiten",                                      SUED,    "Marmolata (3343 m)",                 "Dolomiti"),
    Gebirgsgruppe("32", "Venezianische Voralpen",                         SUED,    "Col Nudo (2472 m)",                  "Prealpi Venete"),
    Gebirgsgruppe("33", "Karnische und Gailtaler Alpen",                  SUED,    "Hohe Warte (2780 m)",                "Alpi Carniche e della Gail"),
    Gebirgsgruppe("34", "Julische Alpen und Voralpen",                    SUED,    "Triglav (2864 m)",                   "Alpi e Prealpi Giulie"),
    Gebirgsgruppe("35", "Kärntner und Slowenische Alpen",                 SUED,    "Grintovec (2558 m)",                 "Alpi di Carinzia e di Slovenia"),
    Gebirgsgruppe("36", "Slowenische Voralpen",                           SUED,    "Porezen (1630 m)",                   "Prealpi Slovene"),
]


# ─── Colors ───────────────────────────────────────────────────────────────────

CLASSIFICATION = Classification(
    name="soiusa_sz",
    title="SOIUSA Sezioni",
    groups=GROUPS,
    hauptgruppen=HAUPTGRUPPEN,
    colors={
        ZENTRAL: {
            "fill": "#9B59B6",
            "border": "#FFFFFF", "label": "Z",
        },
        NORD: {
            "fill": "#2E8FAA",
            "border": "#FFFFFF", "label": "N",
        },
        SUED: {
            "fill": "#D96B2B",
            "border": "#FFFFFF", "label": "S",
        },
    },
    osm_tag="SZ",
    osm_fallback_ids={},
)
