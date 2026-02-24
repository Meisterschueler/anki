# Peak Soaring — Alpen-Lerndecks für Anki

Erzeugt Anki-Lerndecks (`.apkg`) für **Gebirgsgruppen** und **Landmarks** der Alpen.

## Unterstützte Decks

### Gebirgsgruppen (Polygon-Decks)

| Region | System | Gruppen | Datenquelle |
|--------|--------|---------|-------------|
| Ostalpen | AVE 84 | 75 | OSM (`ref:aveo`) |
| Westalpen | SOIUSA (Sezioni) | 14 | uMap (homoalpinus.com) |
| Westalpen | SOIUSA (Sottosezioni) | 55 | uMap (homoalpinus.com) |

### POI-Decks (Punkte)

| Region | System | POIs | Inhalt |
|--------|--------|------|--------|
| Ostalpen | POIs | 40 | Gipfel, Pässe, Orte, Täler aus "Peak Soaring" |

## Kartentypen

### Gebirgsgruppen-Karten

Einzelnes Template mit Toggle-Button:

- **Vorderseite**: Reliefkarte mit rot hervorgehobener Gruppe + „▦ Einteilung"-Button
  (blendet die farbige Gesamteinteilung als Hinweis ein)
- **Rückseite**: Name + höchster Gipfel + Reliefkarte mit Gruppe, Städten und
  Ländergrenzen + „▦ Einteilung"-Button

### POI-Karten

Zwei Templates pro POI:

- **Template 1 — „Wo ist X?"**: Name gegeben → Ort auf der Karte finden
- **Template 2 — „Was ist das?"**: Ort markiert → Name erraten

## Datenquellen

| Quelle | Verwendung |
|--------|-----------|
| OpenStreetMap | Gebirgsgruppen-Polygone, Ländergrenzen, Flüsse, Seen |
| uMap #954288 | SOIUSA-Polygone (Westalpen) |
| CGIAR-CSI SRTM 90m | Höhenmodell für Reliefkarte |

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

## Workflow

```bash
# 1. Geodaten herunterladen
python scripts/01_download_data.py --region ostalpen
python scripts/download_soiusa_umap.py   # Westalpen SOIUSA

# 2. Basemap erzeugen (Hillshade + Seen + Flüsse)
python scripts/02_generate_basemap.py --region ostalpen

# 3. Kartenbilder erzeugen
python scripts/03_generate_cards.py --region ostalpen --system ave84 --force
python scripts/03b_generate_poi_cards.py --region ostalpen --system pois --force

# 4. Anki-Deck (.apkg) bauen
python scripts/04_build_deck.py --region ostalpen --system ave84
python scripts/04_build_deck.py --region ostalpen --system pois

# 5. Tests ausführen
python scripts/05_run_tests.py
```

## Projektstruktur

```
peak_soaring/
├── models.py                        # Gebirgsgruppe Dataclass
├── deck.py                          # Region / Classification / Deck / POIDeck
├── classifications/
│   ├── ave84.py                     # 75 Ostalpen-Gruppen (AVE 84)
│   ├── soiusa.py                    # 14 Westalpen-Sezioni (SOIUSA)
│   ├── soiusa_sts.py                # 55 Westalpen-Sottosezioni (SOIUSA)
│   └── pois.py                      # 40 POIs (Gipfel, Pässe, Orte, Täler)
├── regions/
│   ├── ostalpen.py                  # Bbox, Städte, Projektion
│   └── westalpen.py
├── scripts/
│   ├── 01_download_data.py          # OSM + DEM herunterladen
│   ├── 02_generate_basemap.py       # Rendering-Funktionen (Basemap, Polygone, …)
│   ├── 03_generate_cards.py         # Kartenbilder für Polygon-Decks
│   ├── 03b_generate_poi_cards.py    # Kartenbilder für POI-Decks
│   ├── 04_build_deck.py             # .apkg-Export (Polygon + POI)
│   ├── 05_run_tests.py              # Pytest-Runner
│   └── download_soiusa_umap.py      # SOIUSA-Polygone von uMap
├── tests/
│   ├── test_deck_size.py            # .apkg Dateigröße < 50 MB
│   └── test_image_dimensions.py     # Alle Bilder gleiche Dimensionen
├── data/
│   ├── osm/                         # GeoJSON (Polygone, Grenzen, Gewässer)
│   └── dem/                         # Höhenmodell (GeoTIFF)
└── output/
    ├── ostalpen_ave84/              # .apkg + Bilder
    ├── ostalpen_pois/               # .apkg + Bilder
    ├── westalpen_soiusa/            # .apkg + Bilder
    └── westalpen_soiusa_sts/        # .apkg + Bilder
```

## Lizenz

- Kartendaten: © OpenStreetMap Contributors (ODbL)
- SOIUSA-Polygone: homoalpinus.com / Capleymar
- SRTM-Daten: CGIAR-CSI / NASA (Public Domain)
