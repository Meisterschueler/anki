# Peak Soaring — Alpen-Lerndecks für Anki

Erzeugt Anki-Lerndecks (`.apkg`) für **Gebirgsgruppen** und **Landmarks** der Alpen.
Alle Karten basieren auf einem CSS-Layer-Ansatz: eine opake Basemap plus transparente
WebP-Overlays, die in Anki übereinander gelegt werden.

## Unterstützte Decks

### Gebirgsgruppen (Polygon-Decks)

| Region | System | Gruppen | Datenquelle |
|--------|--------|---------|-------------|
| Ostalpen | AVE 84 | 75 | OSM (`ref:aveo`) |
| Ostalpen | SOIUSA (Sezioni) | 22 | ARPA Piemonte FeatureServer |
| Ostalpen | SOIUSA (Sottosezioni) | 76 | ARPA Piemonte FeatureServer |
| Westalpen | SOIUSA (Sezioni) | 14 | uMap (homoalpinus.com) |
| Westalpen | SOIUSA (Sottosezioni) | 55 | ARPA Piemonte FeatureServer |

SOIUSA-Decks werden pro Region zu einem kombinierten `.apkg` mit Subdecks zusammengeführt:
`A Gliederung` (Sezioni) + `B Details` (Sottosezioni).

### POI-Decks (Punkte)

| Region | System | POIs | Inhalt |
|--------|--------|------|--------|
| Ostalpen | POIs | 209 | Gipfel, Pässe, Orte, Täler, Seen aus "Peak Soaring" |
| Westalpen | POIs | 209 | (gefiltert auf Region-Bbox) |

POI-Kategorien: 78 Gipfel (▲), 59 Pässe (⬤), 22 Täler (◆), 43 Orte (■), 7 Seen (⬡).

Das Ostalpen-POI-Deck wird als Multi-Deck mit Subdecks gebaut:
- **Sub-Regions** (gezoomte Karte + Thumbnail): `A Königsdorf`, `B Innsbruck`
- **Kategorien** (Gesamtkarte, gefiltert): `C Gipfel`, `D Pässe`, `E Orte`, `F Täler`, `G Seen`

## Kartentypen

### Gebirgsgruppen-Karten

Einzelnes Template „Gebirgsgruppe" mit Toggle-Buttons:

- **Vorderseite**: Reliefkarte mit rotem Fragezeichen im Gruppenpolygon
  + „▦ Einteilung"-Button (blendet farbige Gesamteinteilung ein)
  + „▦ Kontext"-Button (blendet Ländergrenzen + Städtenamen ein)
  + „↻ Drehen“-Button (dreht Karte um 180° mit korrektem Schattenfall — erhöht Schwierigkeit)
- **Rückseite**: Name + Gruppen-ID + höchster Gipfel,
  Reliefkarte mit farbigem Polygon (+ Parent-Polygon bei hierarchischen Systemen)
  + gleiche Toggle-Buttons

### POI-Karten

Ein Template „Was ist das?" (markierter Ort → Name erraten):

- **Vorderseite**: Reliefkarte mit rotem Highlight-Kreis am Ziel-POI
  + „▦ POIs"-Button (blendet alle POI-Marker ein)
  + „▦ Kontext"-Button (Grenzen + Städte)
  + „↻ Drehen"-Button (dreht alle Layer um 180°)
  + optionales Thumbnail (nur bei Sub-Region-Decks: Übersichtskarte mit rotem Rechteck)
- **Rückseite**: Name + Kategorie + Info (Höhe, Untertitel),
  Reliefkarte mit allen POIs + Ziel hervorgehoben
  + gleiche Toggle-Buttons

## Ausgabeformat — `.apkg`-Spezifikation

### Dateiformat

- **Paketformat**: Anki `.apkg` (ZIP mit SQLite-DB + Mediendateien)
- **Erzeugt mit**: `genanki` (Python-Bibliothek)
- **Bildformat**: WebP (alle Layer haben identische Pixeldimensionen pro Deck)

### Bild-Layer (WebP)

Jede Anki-Karte besteht aus mehreren WebP-Bildern, die per CSS (`position: absolute`)
pixelgenau übereinander gelegt werden. Alle Layer eines Decks haben exakt gleiche Dimensionen.

| Eigenschaft | Basemap | Overlays |
|-------------|---------|----------|
| **Transparenz** | Opak (RGB) | Transparent (RGBA) |
| **Kompression** | Lossy (Quality 90) | Lossless |
| **Auflösung** | Max 7680 × 4320 px (8K UHD) | Identisch zur Basemap |
| **Rendering-DPI** | 480 | 480 |
| **Inhalt** | Hillshade + Ozean + Flüsse + Seen | Vektordaten (Polygone, Marker, Grenzen, …) |

### Layer-Aufbau — Gebirgsgruppen-Deck

Jede Karte referenziert diese Bilder (alle `.webp`):

| Layer | CSS-Klasse | Dateinamenbeispiel | Inhalt | Sichtbarkeit |
|-------|------------|--------------------|--------|--------------|
| **Basemap** | `basemap` | `ps_ostalpen_ave84_basemap.webp` | Hillshade-Relief + Gewässer (Azimut 315°) + Kompassnadel N↑ | Immer sichtbar |
| **BasemapRot** | `basemap-rot` | `ps_ostalpen_ave84_basemap_rot.webp` | Hillshade-Relief + Gewässer (Azimut 135°), vorrotiert (Süd-oben) + Kompassnadel N↓ | Versteckt, per Drehen-Button einblendbar |
| **Partition** | `overlay partition` | `ps_ostalpen_ave84_partition.webp` | Alle Gruppen farbig + IDs | Versteckt, per Button einblendbar |
| **Context** | `overlay context` | `ps_ostalpen_ave84_context.webp` | Ländergrenzen + Städtenamen | Versteckt, per Button einblendbar |
| **FrontOverlay** | `overlay` | `ps_ostalpen_ave84_group_3b_front.webp` | Rotes Fragezeichen im Polygon | Nur Vorderseite |
| **BackOverlay** | `overlay` | `ps_ostalpen_ave84_group_3b_back.webp` | Farbiges Polygon (+ Parent) | Nur Rückseite |

### Layer-Aufbau — POI-Deck

| Layer | CSS-Klasse | Dateinamenbeispiel | Inhalt | Sichtbarkeit |
|-------|------------|--------------------|--------|--------------|
| **Basemap** | `basemap` | `ps_ostalpen_pois_basemap.webp` | Hillshade-Relief + Gewässer (Azimut 315°) + Kompassnadel N↑ | Immer sichtbar |
| **BasemapRot** | `basemap-rot` | `ps_ostalpen_pois_basemap_rot.webp` | Hillshade-Relief + Gewässer (Azimut 135°), vorrotiert (Süd-oben) + Kompassnadel N↓ | Versteckt, per Drehen-Button einblendbar |
| **AllPois** | `overlay allpois` | `ps_ostalpen_pois_all_pois.webp` | Alle POI-Marker + Labels | Versteckt, per Button einblendbar |
| **Highlight** | `overlay` | `ps_ostalpen_pois_poi_peak_01_highlight.webp` | Roter Kreis / Polygon am Ziel-POI | Nur Vorderseite |
| **BackOverlay** | `overlay` | `ps_ostalpen_pois_poi_peak_01_back.webp` | Roter Kreis am Ziel (Rückseite) | Nur Rückseite |
| **Context** | `overlay context` | `ps_ostalpen_pois_context.webp` | Ländergrenzen + Städtenamen | Versteckt, per Button einblendbar |
| **Thumbnail** | `thumbnail` | `ps_ostalpen_pois_thumb_koenigsdorf.webp` | Übersichtskarte mit rotem Rechteck + Kompassnadel N↑ | Nur bei Sub-Region-Decks (konditional) |

### CSS-Compositing in Anki

```css
.card-map {
    position: relative;
    display: inline-block;
}
.card-map img.basemap {
    display: block;           /* unterste Ebene, definiert die Kartengröße */
}
.card-map img.basemap-rot {
    display: none;            /* gedrehte Basemap, per Drehen-Button einblendbar */
}
.card-map img.overlay {
    position: absolute;       /* pixelgenau über der Basemap */
    top: 0; left: 0;
    width: 100%; height: 100%;
}
```

Partition, AllPois, Context und BasemapRot sind per CSS standardmäßig `display: none` und werden
über JavaScript-Toggle-Buttons (`sessionStorage`-persistent) ein-/ausgeblendet.
Der Drehen-Button tauscht Basemap ↔ BasemapRot und rotiert alle Overlay-Layer um 180°.
BasemapRot und Thumbnail werden **nicht** CSS-rotiert — BasemapRot ist bereits als
Süd-oben-Bild vorrotiert gespeichert, das Thumbnail zeigt immer Norden oben.
So bleibt die Schattenrichtung des Hillshade korrekt (Lichtquelle immer von Nordwesten).
Alle Basemaps und das Thumbnail enthalten eine eingebrannte Kompassnadel (N↑ bzw. N↓).
Das Thumbnail ist per `{{#Thumbnail}}…{{/Thumbnail}}` (Mustache-Konditional) nur vorhanden,
wenn das Feld befüllt ist.

### Anki-Datenmodell

**Gebirgsgruppen-Modell** — 9 Felder:

| Feld | Typ | Beschreibung |
|------|-----|-----------|
| `Group_ID` | Text | Gruppen-ID (z.B. `3b`, `SZ.5`) |
| `Name` | Text | Gruppenname |
| `Hoechster_Gipfel` | Text | Höchster Gipfel mit Höhe |
| `Basemap` | HTML | `<img class="basemap" src="…">` |
| `BasemapRot` | HTML | `<img class="basemap-rot" src="…">` |
| `FrontOverlay` | HTML | `<img class="overlay" src="…">` |
| `BackOverlay` | HTML | `<img class="overlay" src="…">` |
| `Partition` | HTML | `<img class="overlay partition" src="…">` |
| `Context` | HTML | `<img class="overlay context" src="…">` |

**POI-Modell** — 11 Felder:

| Feld | Typ | Beschreibung |
|------|-----|-----------|
| `POI_ID` | Text | Eindeutige ID (z.B. `peak_01`) |
| `Name` | Text | Anzeigename (z.B. `Zugspitze`) |
| `Category` | Text | Kategorie-Label (z.B. `Gipfel`) |
| `Info` | Text | Höhe + Untertitel (z.B. `2962 m`) |
| `Basemap` | HTML | `<img class="basemap" src="…">` |
| `BasemapRot` | HTML | `<img class="basemap-rot" src="…">` |
| `AllPois` | HTML | `<img class="overlay allpois" src="…">` |
| `Highlight` | HTML | `<img class="overlay" src="…">` |
| `BackOverlay` | HTML | `<img class="overlay" src="…">` |
| `Context` | HTML | `<img class="overlay context" src="…">` |
| `Thumbnail` | HTML | `<img class="thumbnail" src="…">` oder leer |

### Basemap-Rendering

Die opake Basemap wird als reines Raster (numpy / rasterio / Pillow) gerendert:

1. **DEM laden** — SRTM 90 m GeoTIFF, Downsampling bei > 7000 px Kantenlänge
2. **Hillshade** — Azimut 315°, Altitude 45°, vertikale Überhöhung 0.05, Soft-Blending
3. **Gewässer** — Flüsse (blau, ≥ 20 km) + Seen (gefüllt, ≥ 1 km²) aus OSM-GeoJSON
4. **Ozean** — Fläche außerhalb des Festlands in `#c6ddf0`
5. **Gedrehte Basemap** — zweite Variante mit Hillshade-Azimut 135° (= 315° − 180°).
   Das Bild wird nach dem Compositing mit PIL um 180° rotiert (Süd-oben) gespeichert.
   In Anki wird es direkt angezeigt (ohne CSS-Rotation) — der Drehen-Button
   tauscht Basemap ↔ BasemapRot und rotiert nur die Overlays per CSS.
6. **Kompassnadel** — in jede Basemap und jedes Thumbnail wird eine Kompassnadel
   (rot = Nord, weiß = Süd) mit „N“-Label in die rechte obere Ecke eingebrannt.
   Normale Basemaps: N↑ (Norden oben). Gedrehte Basemaps: N↓ (Süden oben).
   Größe: 2% der kurzen Bildkante, Margin: 1.5%.

Höhen > 4200 m werden gekappt. Projektion: PlateCarree (WGS 84).

### Dateinamen-Konvention

Alle Bilddateien folgen dem Schema `ps_{region}_{system}_{layer}.webp`:

```
ps_ostalpen_ave84_basemap.webp
ps_ostalpen_ave84_basemap_rot.webp
ps_ostalpen_ave84_partition.webp
ps_ostalpen_ave84_context.webp
ps_ostalpen_ave84_group_{id}_front.webp
ps_ostalpen_ave84_group_{id}_back.webp

ps_ostalpen_pois_basemap.webp
ps_ostalpen_pois_basemap_rot.webp
ps_ostalpen_pois_all_pois.webp
ps_ostalpen_pois_context.webp
ps_ostalpen_pois_poi_{poi_id}_highlight.webp
ps_ostalpen_pois_poi_{poi_id}_back.webp
ps_ostalpen_pois_thumb_{sub_region}.webp
```

### Ausgabeverzeichnisse

```
output/
├── ostalpen_ave84/
│   ├── anki_ostalpen_ave84.apkg         # Fertiges Deck
│   └── images/                           # Alle WebP-Layer
├── ostalpen_soiusa/
│   ├── anki_ostalpen_soiusa.apkg        # Kombiniertes Deck (SZ + STS)
│   └── images/
├── ostalpen_pois/
│   ├── anki_ostalpen_pois.apkg          # Multi-Deck (Sub-Regions + Kategorien)
│   └── images/
├── westalpen_soiusa/
│   ├── anki_westalpen_soiusa.apkg
│   └── images/
└── westalpen_pois/
    ├── anki_westalpen_pois.apkg
    └── images/
```

## Datenquellen

| Quelle | Verwendung |
|--------|-----------|
| OpenStreetMap | Gebirgsgruppen-Polygone, Ländergrenzen, Flüsse, Seen, Täler |
| uMap #954288 | SOIUSA-Polygone (Westalpen SZ) |
| ARPA Piemonte | SOIUSA-Polygone (Ost- & Westalpen SZ + STS) |
| CGIAR-CSI SRTM 90m | Höhenmodell für Hillshade-Relief |

Details zu allen Quellen, Lizenzen und Abrufmethoden: → `SOURCES.md`

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

Abhängigkeiten: cartopy, matplotlib, numpy, rasterio, geopandas, shapely,
Pillow, genanki, pytest u.a. (siehe `requirements.txt`).

## Workflow

```bash
# 1. Geodaten herunterladen
python scripts/01_download_data.py --region ostalpen
python scripts/01_download_data.py --region westalpen
python scripts/download_soiusa_umap.py   # Westalpen SOIUSA SZ (uMap)

# 2. Basemap erzeugen (Hillshade + Seen + Flüsse)
python scripts/02_generate_basemap.py --region ostalpen
python scripts/02_generate_basemap.py --region westalpen

# 3. Kartenbilder erzeugen
python scripts/03_generate_cards.py --region ostalpen --system ave84 --force
python scripts/03_generate_cards.py --region ostalpen --system soiusa_sz --force
python scripts/03_generate_cards.py --region ostalpen --system soiusa_sts --force
python scripts/03b_generate_poi_cards.py --region ostalpen --system pois --force

# 4. Anki-Deck (.apkg) bauen
python scripts/04_build_deck.py --region ostalpen --system ave84
python scripts/04_build_deck.py --region ostalpen --system soiusa_sz
python scripts/04_build_deck.py --region ostalpen --system pois

# 5. Tests ausführen
python scripts/05_run_tests.py
```

Bilder werden beim Deck-Bau (Schritt 4) automatisch erzeugt falls nicht vorhanden.
`--force` in Schritt 3 erzwingt Neugenerierung vorhandener Bilder.

## Projektstruktur

```
peak_soaring/
├── models.py                        # Gebirgsgruppe + POI Dataclasses
├── deck.py                          # Region / Classification / Deck / POIDeck / Konstanten
├── classifications/
│   ├── ave84.py                     # 75 Ostalpen-Gruppen (AVE 84)
│   ├── ostalpen_soiusa_sz.py        # 22 Ostalpen-Sezioni (SOIUSA)
│   ├── ostalpen_soiusa_sts.py       # 76 Ostalpen-Sottosezioni (SOIUSA)
│   ├── westalpen_soiusa_sz.py       # 14 Westalpen-Sezioni (SOIUSA)
│   ├── westalpen_soiusa_sts.py      # 55 Westalpen-Sottosezioni (SOIUSA)
│   └── pois.py                      # 209 POIs (Gipfel, Pässe, Orte, Täler, Seen)
├── regions/
│   ├── ostalpen.py                  # Bbox, Städte, Projektion
│   └── westalpen.py
├── scripts/
│   ├── 01_download_data.py          # OSM + DEM herunterladen
│   ├── 02_generate_basemap.py       # Raster-Basemap + Vektor-Rendering
│   ├── 03_generate_cards.py         # Kartenbilder für Polygon-Decks
│   ├── 03b_generate_poi_cards.py    # Kartenbilder für POI-Decks
│   ├── 04_build_deck.py             # .apkg-Export (Polygon + POI + Multi-Deck)
│   ├── 05_run_tests.py              # Pytest-Runner
│   ├── download_soiusa_arpa.py      # SOIUSA-Polygone von ARPA Piemonte
│   └── download_soiusa_umap.py      # SOIUSA-Polygone von uMap (Westalpen SZ)
├── tests/
│   ├── test_deck_size.py            # .apkg Dateigröße < 50 MB
│   └── test_image_dimensions.py     # Alle Bilder gleiche Dimensionen
├── data/
│   ├── osm/                         # GeoJSON (Polygone, Grenzen, Gewässer)
│   └── dem/                         # Höhenmodell (GeoTIFF)
└── output/
    ├── ostalpen_ave84/              # .apkg + Bilder
    ├── ostalpen_pois/               # .apkg + Bilder (Multi-Deck)
    ├── ostalpen_soiusa/             # .apkg + Bilder (SZ + STS kombiniert)
    ├── westalpen_pois/              # .apkg + Bilder
    └── westalpen_soiusa/            # .apkg + Bilder (SZ + STS kombiniert)
```

## Lizenz

- Kartendaten: © OpenStreetMap Contributors (ODbL)
- SOIUSA-Polygone: Massimo Accorsi / ARPA Piemonte, homoalpinus.com / Capleymar
- SRTM-Daten: CGIAR-CSI / NASA (Public Domain)
