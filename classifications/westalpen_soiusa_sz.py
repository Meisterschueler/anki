"""
Classification: SOIUSA SZ (Westalpen — Sezioni)
=================================================
All 14 Sezioni (sections) of the Western Alps according to the
Suddivisione Orografica Internazionale Unificata del Sistema Alpino
(SOIUSA, Sergio Marazzi, 2005).

Part I — Alpi Occidentali:
  Sector A — Alpi Sud-occidentali  (SZ 1–6)
  Sector B — Alpi Nord-occidentali (SZ 7–14)

Data source: homoalpinus.com/Capleymar via uMap (map #954288)
"""

from typing import List

from deck import Classification
from models import Gebirgsgruppe


# ─── Hauptgruppen (Sectors) ──────────────────────────────────────────────────

SUEDWEST = "Alpi Sud-occidentali"
NORDWEST = "Alpi Nord-occidentali"

HAUPTGRUPPEN = [SUEDWEST, NORDWEST]

# ─── All 14 Sezioni ──────────────────────────────────────────────────────────

GROUPS: List[Gebirgsgruppe] = [
    # ═══════════════════════════════════════════════════════════════════════════
    # SECTOR A — Alpi Sud-occidentali  (SZ 1–6)
    # ═══════════════════════════════════════════════════════════════════════════
    Gebirgsgruppe("1",  "Ligurische Alpen",                          SUEDWEST, "Pointe Marguareis (2651 m)",       "1"),
    Gebirgsgruppe("2",  "Seealpen",                                  SUEDWEST, "Cima Argentera (3297 m)",          "2"),
    Gebirgsgruppe("3",  "Provenzalische Alpen und Voralpen",         SUEDWEST, "Tête de l'Estrop (2961 m)",        "3"),
    Gebirgsgruppe("4",  "Cottische Alpen",                           SUEDWEST, "Monviso (3841 m)",                 "4"),
    Gebirgsgruppe("5",  "Dauphiné-Alpen",                            SUEDWEST, "Barre des Écrins (4101 m)",        "5"),
    Gebirgsgruppe("6",  "Dauphiné-Voralpen",                         SUEDWEST, "Grande Tête de l'Obiou (2790 m)",  "6"),

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTOR B — Alpi Nord-occidentali  (SZ 7–14)
    # ═══════════════════════════════════════════════════════════════════════════
    Gebirgsgruppe("7",  "Grajische Alpen",                           NORDWEST, "Mont Blanc (4808 m)",              "7"),
    Gebirgsgruppe("8",  "Savoyer Voralpen",                          NORDWEST, "Dents du Midi (3257 m)",           "8"),
    Gebirgsgruppe("9",  "Penninische Alpen",                         NORDWEST, "Monte Rosa (4634 m)",              "9"),
    Gebirgsgruppe("10", "Lepontinische Alpen",                       NORDWEST, "Mont Leone (3552 m)",              "10"),
    Gebirgsgruppe("11", "Lugano-Voralpen",                           NORDWEST, "Pizzo di Gino (2245 m)",           "11"),
    Gebirgsgruppe("12", "Berner Alpen",                              NORDWEST, "Finsteraarhorn (4274 m)",          "12"),
    Gebirgsgruppe("13", "Glarner Alpen",                             NORDWEST, "Tödi (3620 m)",                    "13"),
    Gebirgsgruppe("14", "Schweizerische Voralpen",                   NORDWEST, "Schilthorn (2970 m)",              "14"),
]


# ─── Colors ───────────────────────────────────────────────────────────────────

CLASSIFICATION = Classification(
    name="soiusa_sz",
    title="SOIUSA Sezioni",
    groups=GROUPS,
    hauptgruppen=HAUPTGRUPPEN,
    colors={
        SUEDWEST: {
            "fill": "#D96B2B",
            "border": "#FFFFFF", "label": "SW",
        },
        NORDWEST: {
            "fill": "#2E8FAA",
            "border": "#FFFFFF", "label": "NW",
        },
    },
    osm_tag="ref:soiusa",
    osm_fallback_ids={},
)
