"""
Classification: SOIUSA STS (Westalpen — Sottosezioni)
=======================================================
All 55 Sottosezioni (sub-sections) of the Western Alps according to the
Suddivisione Orografica Internazionale Unificata del Sistema Alpino
(SOIUSA, Sergio Marazzi, 2005).

Part I — Alpi Occidentali:
  Sector A — Alpi Sud-occidentali  (SZ 1–6,  23 STS)
  Sector B — Alpi Nord-occidentali (SZ 7–14, 32 STS)

Hauptgruppen = parent Sezioni (14 groups, matching westalpen_soiusa_sz.py).
Data source: ARPA Piemonte FeatureServer (dissolved from Gruppo level).
"""

from typing import List

from deck import Classification
from models import Gebirgsgruppe


# ─── Hauptgruppen = parent Sezioni ────────────────────────────────────────────

SZ01 = "Ligurische Alpen"
SZ02 = "Seealpen"
SZ03 = "Provenzalische Alpen und Voralpen"
SZ04 = "Cottische Alpen"
SZ05 = "Dauphiné-Alpen"
SZ06 = "Dauphiné-Voralpen"
SZ07 = "Grajische Alpen"
SZ08 = "Savoyer Voralpen"
SZ09 = "Penninische Alpen"
SZ10 = "Lepontinische Alpen"
SZ11 = "Lugano-Voralpen"
SZ12 = "Berner Alpen"
SZ13 = "Glarner Alpen"
SZ14 = "Schweizerische Voralpen"

HAUPTGRUPPEN = [
    SZ01, SZ02, SZ03, SZ04, SZ05, SZ06, SZ07,
    SZ08, SZ09, SZ10, SZ11, SZ12, SZ13, SZ14,
]


# ─── All 55 Sottosezioni ─────────────────────────────────────────────────────

GROUPS: List[Gebirgsgruppe] = [

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTOR A — Alpi Sud-occidentali  (SZ 1–6)
    # ═══════════════════════════════════════════════════════════════════════════

    # SZ 1 — Ligurische Alpen  (Alpi Liguri i.s.a.)
    Gebirgsgruppe("1.1", "Marguareis-Alpen",                              SZ01, "Punta Marguareis (2651 m)",             "Alpi del Marguareis"),
    Gebirgsgruppe("1.2", "Ligurische Voralpen",                           SZ01, "Monte Saccarello (2201 m)",             "Prealpi Liguri"),

    # SZ 2 — Seealpen  (Alpi Marittime e Prealpi di Nizza)
    Gebirgsgruppe("2.1", "Seealpen i. e. S.",                             SZ02, "Cima Argentera (3297 m)",               "Alpi Marittime"),
    Gebirgsgruppe("2.2", "Voralpen von Nizza",                            SZ02, "Mont Mounier (2817 m)",                 "Prealpi di Nizza"),

    # SZ 3 — Provenzalische Alpen und Voralpen  (Alpi e Prealpi di Provenza)
    Gebirgsgruppe("3.1", "Provenzalische Alpen",                          SZ03, "Tête de l'Estrop (2961 m)",             "Alpi di Provenza"),
    Gebirgsgruppe("3.2", "Voralpen von Digne",                            SZ03, "Montagne de Lure (1826 m)",             "Prealpi di Digne"),
    Gebirgsgruppe("3.3", "Voralpen von Grasse",                           SZ03, "Mont Cheiron (1778 m)",                 "Prealpi di Grasse"),
    Gebirgsgruppe("3.4", "Voralpen von Vaucluse",                         SZ03, "Mont Ventoux (1909 m)",                 "Prealpi di Vaucluse"),

    # SZ 4 — Cottische Alpen  (Alpi Cozie)
    Gebirgsgruppe("4.1", "Mont-Cenis-Alpen",                              SZ04, "Pointe de Ronce (3612 m)",              "Alpi del Moncenisio"),
    Gebirgsgruppe("4.2", "Montgenèvre-Alpen",                             SZ04, "Monte Chaberton (3131 m)",              "Alpi del Monginevro"),
    Gebirgsgruppe("4.3", "Monviso-Alpen",                                 SZ04, "Monviso (3841 m)",                      "Alpi del Monviso"),

    # SZ 5 — Dauphiné-Alpen  (Alpi del Delfinato)
    Gebirgsgruppe("5.1", "Grandes Rousses und Aiguilles d'Arves",         SZ05, "Pic de l'Étendard (3464 m)",            "Alpi delle Grandes Rousses e Aiguilles d'Arves"),
    Gebirgsgruppe("5.2", "Belledonne-Kette",                              SZ05, "Grand Pic de Belledonne (2977 m)",      "Catena di Belledonne"),
    Gebirgsgruppe("5.3", "Écrins-Massiv",                                 SZ05, "Barre des Écrins (4101 m)",             "Massiccio degli Écrins"),
    Gebirgsgruppe("5.4", "Champsaur-Massiv",                              SZ05, "Vieux Chaillol (3163 m)",               "Massiccio del Champsaur"),
    Gebirgsgruppe("5.5", "Taillefer-Massiv",                              SZ05, "Grand Taillefer (2857 m)",              "Massiccio del Taillefer"),
    Gebirgsgruppe("5.6", "Embrunais-Massiv",                              SZ05, "Mourre Froid (2993 m)",                 "Massiccio dell'Embrunais"),
    Gebirgsgruppe("5.7", "Berge östlich von Gap",                         SZ05, "Pic de Bure (2709 m)",                  "Monti orientali di Gap"),

    # SZ 6 — Dauphiné-Voralpen  (Prealpi del Delfinato)
    Gebirgsgruppe("6.1", "Dévoluy-Voralpen",                              SZ06, "Obiou (2790 m)",                        "Prealpi del Devoluy"),
    Gebirgsgruppe("6.2", "Diois-Voralpen",                                SZ06, "Montagne de Glandasse (2041 m)",        "Prealpi del Diois"),
    Gebirgsgruppe("6.3", "Vercors-Voralpen",                              SZ06, "Grand Veymont (2341 m)",                "Prealpi del Vercors"),
    Gebirgsgruppe("6.4", "Baronnies-Voralpen",                            SZ06, "Montagne d'Angèle (1606 m)",            "Prealpi delle Baronnies"),
    Gebirgsgruppe("6.5", "Westliche Voralpen von Gap",                    SZ06, "Montagne de Céüse (2016 m)",            "Prealpi occidentali di Gap"),

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTOR B — Alpi Nord-occidentali  (SZ 7–14)
    # ═══════════════════════════════════════════════════════════════════════════

    # SZ 7 — Grajische Alpen  (Alpi Graie)
    Gebirgsgruppe("7.1", "Beaufortain-Alpen",                             SZ07, "Aiguille du Grand Fond (2920 m)",       "Alpi del Beaufortain"),
    Gebirgsgruppe("7.2", "Gran-Paradiso-Alpen",                           SZ07, "Gran Paradiso (4061 m)",                "Alpi del Gran Paradiso"),
    Gebirgsgruppe("7.3", "Mont-Blanc-Gruppe",                             SZ07, "Mont Blanc (4808 m)",                   "Alpi del Monte Bianco"),
    Gebirgsgruppe("7.4", "Grande-Sassière- und Rutor-Alpen",              SZ07, "Grande Sassière (3747 m)",              "Alpi della Grande Sassière e del Rutor"),
    Gebirgsgruppe("7.5", "Vanoise und Grand Arc",                         SZ07, "Grande Casse (3855 m)",                 "Alpi della Vanoise e del Grand Arc"),
    Gebirgsgruppe("7.6", "Lanzo-Alpen und Haute-Maurienne",               SZ07, "Uia di Ciamarella (3676 m)",            "Alpi di Lanzo e dell'Alta Moriana"),

    # SZ 8 — Savoyer Voralpen  (Prealpi di Savoia)
    Gebirgsgruppe("8.1", "Aiguilles-Rouges-Kette",                        SZ08, "Aiguille du Belvédère (2965 m)",        "Catena delle Aiguilles Rouges"),
    Gebirgsgruppe("8.2", "Bauges-Voralpen",                               SZ08, "Pointe d'Arcalod (2217 m)",             "Prealpi dei Bauges"),
    Gebirgsgruppe("8.3", "Bornes-Voralpen",                               SZ08, "Pointe de la Tournette (2351 m)",       "Prealpi dei Bornes"),
    Gebirgsgruppe("8.4", "Giffre-Voralpen",                               SZ08, "Haute Cime (3257 m)",                   "Prealpi del Giffre"),
    Gebirgsgruppe("8.5", "Chartreuse-Voralpen",                           SZ08, "Chamechaude (2082 m)",                  "Prealpi della Chartreuse"),
    Gebirgsgruppe("8.6", "Chablais-Voralpen",                             SZ08, "Hauts Forts (2466 m)",                  "Prealpi dello Chablais"),

    # SZ 9 — Penninische Alpen  (Alpi Pennine)
    Gebirgsgruppe("9.1", "Biella- und Cusio-Alpen",                       SZ09, "Monte Mars (2600 m)",                   "Alpi Biellesi e Cusiane"),
    Gebirgsgruppe("9.2", "Grand-Combin-Alpen",                            SZ09, "Grand Combin (4314 m)",                 "Alpi del Grand Combin"),
    Gebirgsgruppe("9.3", "Mischabel- und Weissmies-Alpen",                SZ09, "Dom (4545 m)",                          "Alpi del Mischabel e del Weissmies"),
    Gebirgsgruppe("9.4", "Monte-Rosa-Alpen",                              SZ09, "Punta Dufour (4634 m)",                 "Alpi del Monte Rosa"),
    Gebirgsgruppe("9.5", "Weisshorn- und Matterhorn-Alpen",               SZ09, "Weisshorn (4506 m)",                    "Alpi del Weisshorn e del Cervino"),

    # SZ 10 — Lepontinische Alpen  (Alpi Lepontine)
    Gebirgsgruppe("10.1", "Tessiner und Verbano-Alpen",                   SZ10, "Basòdino (3273 m)",                     "Alpi Ticinesi e del Verbano"),
    Gebirgsgruppe("10.2", "Monte-Leone- und Gotthard-Alpen",              SZ10, "Monte Leone (3552 m)",                  "Alpi del Monte Leone e del San Gottardo"),
    Gebirgsgruppe("10.3", "Adula-Alpen",                                  SZ10, "Rheinwaldhorn (3402 m)",                "Alpi dell'Adula"),

    # SZ 11 — Lugano-Voralpen  (Prealpi Luganesi)
    Gebirgsgruppe("11.1", "Comer Voralpen",                               SZ11, "Pizzo di Gino (2245 m)",                "Prealpi Comasche"),
    Gebirgsgruppe("11.2", "Varesiner Voralpen",                           SZ11, "Monte Lema (1624 m)",                   "Prealpi Varesine"),

    # SZ 12 — Berner Alpen  (Alpi Bernesi)
    Gebirgsgruppe("12.1", "Berner Alpen i. e. S.",                        SZ12, "Finsteraarhorn (4274 m)",               "Alpi Bernesi p.d."),
    Gebirgsgruppe("12.2", "Urner Alpen",                                  SZ12, "Dammastock (3630 m)",                   "Alpi Urane"),
    Gebirgsgruppe("12.3", "Waadtländer Alpen",                            SZ12, "Les Diablerets (3210 m)",               "Alpi di Vaud"),

    # SZ 13 — Glarner Alpen  (Alpi Glaronesi)
    Gebirgsgruppe("13.1", "Glarner Alpen i. e. S.",                       SZ13, "Tödi (3614 m)",                         "Alpi Glaronesi p.d."),
    Gebirgsgruppe("13.2", "Urner-Glarner Alpen",                          SZ13, "Clariden (3267 m)",                     "Alpi Urano-Glaronesi"),

    # SZ 14 — Schweizerische Voralpen  (Prealpi Svizzere)
    Gebirgsgruppe("14.1", "Appenzeller und St. Galler Voralpen",          SZ14, "Säntis (2502 m)",                       "Prealpi Appenzellesi e Sangallesi"),
    Gebirgsgruppe("14.2", "Berner Voralpen",                              SZ14, "Schilthorn (2970 m)",                   "Prealpi Bernesi"),
    Gebirgsgruppe("14.3", "Luzerner und Unterwaldner Voralpen",           SZ14, "Brienzer Rothorn (2350 m)",             "Prealpi Lucernesi e Untervaldesi"),
    Gebirgsgruppe("14.4", "Schwyzer und Urner Voralpen",                  SZ14, "Gross Windgällen (3187 m)",             "Prealpi Svittesi e Urane"),
    Gebirgsgruppe("14.5", "Waadtländer und Freiburger Voralpen",          SZ14, "Rochers de Naye (2042 m)",              "Prealpi di Vaud e Friburgo"),
]


# ─── Colors (one per parent Sezione) ─────────────────────────────────────────
# SW sector: warm tones  —  NW sector: cool tones

CLASSIFICATION = Classification(
    name="soiusa_sts",
    title="SOIUSA Sottosezioni",
    groups=GROUPS,
    hauptgruppen=HAUPTGRUPPEN,
    colors={
        # ── Sector A — Alpi Sud-occidentali ──────────────────────────────────
        SZ01: {"fill": "#E96B56", "border": "#FFFFFF", "label": "1"},    # coral
        SZ02: {"fill": "#C0392B", "border": "#FFFFFF", "label": "2"},    # crimson
        SZ03: {"fill": "#D4A017", "border": "#FFFFFF", "label": "3"},    # gold
        SZ04: {"fill": "#E67E22", "border": "#FFFFFF", "label": "4"},    # orange
        SZ05: {"fill": "#A93226", "border": "#FFFFFF", "label": "5"},    # dark red
        SZ06: {"fill": "#E74C3C", "border": "#FFFFFF", "label": "6"},    # bright red
        # ── Sector B — Alpi Nord-occidentali ─────────────────────────────────
        SZ07: {"fill": "#2E86C1", "border": "#FFFFFF", "label": "7"},    # blue
        SZ08: {"fill": "#17A589", "border": "#FFFFFF", "label": "8"},    # teal-green
        SZ09: {"fill": "#27AE60", "border": "#FFFFFF", "label": "9"},    # green
        SZ10: {"fill": "#1ABC9C", "border": "#FFFFFF", "label": "10"},   # turquoise
        SZ11: {"fill": "#8E44AD", "border": "#FFFFFF", "label": "11"},   # purple
        SZ12: {"fill": "#4A569D", "border": "#FFFFFF", "label": "12"},   # indigo
        SZ13: {"fill": "#3498DB", "border": "#FFFFFF", "label": "13"},   # sky blue
        SZ14: {"fill": "#196F3D", "border": "#FFFFFF", "label": "14"},   # forest green
    },
    osm_tag="STS",
    osm_fallback_ids={},
    parent_osm_tag="SZ",
)
