# Peak Soaring — Projektdokumentation

## Inhaltsverzeichnis

- [Peak Soaring — Projektdokumentation](#peak-soaring--projektdokumentation)
  - [Inhaltsverzeichnis](#inhaltsverzeichnis)
  - [1. Zweck](#1-zweck)
  - [2. Tools \& Abhängigkeiten](#2-tools--abhängigkeiten)
    - [Python-Bibliotheken](#python-bibliotheken)
    - [Externe Dienste / Quellen](#externe-dienste--quellen)
    - [Projektstruktur](#projektstruktur)
  - [3. Architektur](#3-architektur)
    - [Datenmodell](#datenmodell)
    - [Pipeline-Schritte](#pipeline-schritte)
    - [Karten-Compositing in Anki](#karten-compositing-in-anki)
    - [Dateinamen-Schema](#dateinamen-schema)
    - [Subdeck-Zusammenführung (SUBDECK\_MERGE)](#subdeck-zusammenführung-subdeck_merge)
  - [4. Überblick über die Decks](#4-überblick-über-die-decks)
  - [5. Deck 1: Ostalpen AVE 84 (Kombiniertes Deck)](#5-deck-1-ostalpen-ave-84-kombiniertes-deck)
    - [Kartenmodell (Gebirgsgruppen \& Täler)](#kartenmodell-gebirgsgruppen--täler)
    - [Kartenmodell (Gipfel, Pässe, Seen — POI-Subdecks)](#kartenmodell-gipfel-pässe-seen--poi-subdecks)
    - [Subdeck 1.1: A Gebirgsgruppen](#subdeck-11-a-gebirgsgruppen)
      - [Hauptgruppen \& Farben](#hauptgruppen--farben)
      - [Kartenaufbau pro Gruppe](#kartenaufbau-pro-gruppe)
    - [Subdeck 1.2: B Gipfel](#subdeck-12-b-gipfel)
      - [Inhalt](#inhalt)
      - [Kartenaufbau (Rückseite)](#kartenaufbau-rückseite)
    - [Subdeck 1.3: C Täler](#subdeck-13-c-täler)
      - [Hauptgruppen (Einzugsgebiete) \& Farben](#hauptgruppen-einzugsgebiete--farben)
      - [Besonderheit: Geometrie-Reparatur](#besonderheit-geometrie-reparatur)
      - [Kartenaufbau pro Tal](#kartenaufbau-pro-tal)
    - [Subdeck 1.4: D Pässe](#subdeck-14-d-pässe)
      - [Inhalt (Auswahl nach Typ)](#inhalt-auswahl-nach-typ)
      - [Kartenaufbau (Rückseite)](#kartenaufbau-rückseite-1)
    - [Subdeck 1.5: E Seen](#subdeck-15-e-seen)
      - [Inhalt](#inhalt-1)
    - [Subdeck 1.6: F Gebirgsgruppen visualisieren](#subdeck-16-f-gebirgsgruppen-visualisieren)
      - [Unterschied zu Subdeck 1.1](#unterschied-zu-subdeck-11)
  - [6. Deck 2: Ostalpen SOIUSA](#6-deck-2-ostalpen-soiusa)
    - [Subdeck 2.1: A Gliederung (Sezioni)](#subdeck-21-a-gliederung-sezioni)
      - [Sektoren \& Farben](#sektoren--farben)
      - [Hierarchie auf der Rückseite](#hierarchie-auf-der-rückseite)
    - [Subdeck 2.2: B Details (Sottosezioni)](#subdeck-22-b-details-sottosezioni)
  - [7. Deck 3: Ostalpen Marken (POIs)](#7-deck-3-ostalpen-marken-pois)
    - [Subdeck 3.1: A Königsdorf](#subdeck-31-a-königsdorf)
    - [Subdeck 3.2: B Innsbruck](#subdeck-32-b-innsbruck)
    - [Subdeck 3.3 – 3.10: Kategorien C–J](#subdeck-33--310-kategorien-cj)
  - [8. Deck 4: Westalpen SOIUSA](#8-deck-4-westalpen-soiusa)
    - [Subdeck 4.1: A Gliederung (Sezioni)](#subdeck-41-a-gliederung-sezioni)
    - [Subdeck 4.2: B Details (Sottosezioni)](#subdeck-42-b-details-sottosezioni)
  - [9. Deck 5: Westalpen Marken (POIs)](#9-deck-5-westalpen-marken-pois)
    - [Subdeck 5.1: A Puimoisson](#subdeck-51-a-puimoisson)
    - [Subdeck 5.2 – 5.9: Kategorien B–I](#subdeck-52--59-kategorien-bi)

---

## 1. Zweck

Das Projekt erzeugt **Anki-Lernkarten** (`.apkg`-Pakete) für die Alpen. Zielgruppe sind
Segelflieger, die Geländekenntnisse trainieren möchten — konkret:

- **Gebirgsgruppen erkennen** (AVE 84, SOIUSA): Wo auf der Karte liegt eine bestimmte
  Gruppe? Zu welcher Hauptgruppe/Sektion gehört sie?
- **Landmarken erkennen** (POI-Decks): Gipfel, Pässe, Täler, Seen und Orte aus dem
  Standardwerk *Peak Soaring* von Benjamin Bachmaier sowie Außenlandewiesen aus
  dem Streckenflug.at-Katalog.
- **Täler der Ostalpen** (Neudeckerweiterung): Die 20 wichtigsten Haupttäler als
  farbige Polygon-Überlagerungen, eingebettet im AVE-84-Hauptdeck.

Alle Karten arbeiten nach dem **CSS-Layer-Prinzip**: eine opake Basemap (Hillshade-Relief,
8K-UHD-Auflösung) wird in Anki mit transparenten WebP-Overlays überlagert. Buttons auf
der Karte blenden zusätzliche Layer ein (Gesamteinteilung, Ländergrenzen + Städte,
gedrehte Karte für erhöhten Schwierigkeitsgrad).

---

## 2. Tools & Abhängigkeiten

### Python-Bibliotheken

| Bibliothek | Verwendung |
|---|---|
| **cartopy** | Kartenprojektion, coastlines (Vektor-Layer auf Matplotlib) |
| **matplotlib** | Figur/Axes-Verwaltung, Vektorgrafik, PNG-Export |
| **numpy** | Hillshade-Berechnung, Raster-Compositing |
| **rasterio** | DEM (GeoTIFF) einlesen, Hillshade rendern |
| **geopandas** | GeoJSON laden, Geometrie-Operationen (clip, dissolve) |
| **shapely** | Polygon-Operationen (Intersect, Buffer, Polylabel), Topologie-Reparatur |
| **Pillow (PIL)** | Basemap-Compositing (Hillshade + Seen + Flüsse + Ozean), Kompassnadel einbrennen, WebP speichern |
| **genanki** | Anki-Modell, Notizen und `.apkg`-Paket erzeugen |
| **requests** | HTTP-Abfragen (Overpass API, ARPA Piemonte FeatureServer, SRTM-Tiles) |
| **tqdm** | Fortschrittsbalken beim Tile-Download |
| **pytest** | Test-Suite |

### Externe Dienste / Quellen

| Dienst | Verwendung |
|---|---|
| **Overpass API** (`overpass-api.de`) | AVE-84-Polygone, Täler, Flüsse, Seen, Ländergrenzen |
| **Nominatim** (`nominatim.openstreetmap.org`) | OSM-Relation-/Way-IDs nachschlagen (Einmalig bei Erstellung) |
| **ARPA Piemonte FeatureServer** | SOIUSA-Polygone (Sezioni + Sottosezioni) |
| **uMap #954288** | SOIUSA Westalpen-Sezioni |
| **streckenflug.at** | Außenlandewiesenkatalog (CUPX-ZIP-Archiv) |
| **CGIAR-CSI SRTM 90 m** | Digitales Höhenmodell (DEM GeoTIFF) |

### Projektstruktur

```
anki/
├── deck.py                        # Zentrale Konfigurations-Datei
├── models.py                      # Dataclasses: Gebirgsgruppe, POI
├── requirements.txt
├── regions/
│   ├── ostalpen.py                # Bbox, Projektion, Städte
│   └── westalpen.py
├── classifications/
│   ├── ave84.py                   # 75 AVE-84-Gruppen
│   ├── ostalpen_soiusa_sz.py      # 22 SOIUSA-Sezioni (Ostalpen)
│   ├── ostalpen_soiusa_sts.py     # 76 SOIUSA-Sottosezioni (Ostalpen)
│   ├── westalpen_soiusa_sz.py     # 14 SOIUSA-Sezioni (Westalpen)
│   ├── westalpen_soiusa_sts.py    # 55 SOIUSA-Sottosezioni (Westalpen)
│   ├── ostalpen_taler.py          # 20 Ostalpen-Haupttäler (Polygon-Deck)
│   ├── ostalpen_gipfel.py         # 21 Hauptgipfel (POI-Deck)
│   ├── ostalpen_paesse.py         # 20 Wichtigste Pässe (POI-Deck)
│   ├── ostalpen_seen.py           # 16 Wichtigste Seen (POI-Deck)
│   ├── peak_soaring_pois.py       # ~215 POIs aus dem Buch "Peak Soaring"
│   └── landewiesen.py             # ~615 Außenlandewiesen (streckenflug.at)
├── scripts/
│   ├── 01_download_data.py        # Schritt 1: Geodaten herunterladen
│   ├── 02_generate_basemap.py     # Schritt 2: Basemap / Overlays rendern
│   ├── 03_generate_cards.py       # Schritt 3a: Karten für Polygon-Decks
│   ├── 03b_generate_poi_cards.py  # Schritt 3b: Karten für POI-Decks
│   ├── 04_build_deck.py           # Schritt 4: .apkg bauen
│   ├── 05_run_tests.py            # Schritt 5: Tests
│   ├── render_utils.py            # Hilfsfunktionen (save_figure, context)
│   ├── download_soiusa_arpa.py    # SOIUSA: ARPA-FeatureServer abfragen
│   ├── download_soiusa_umap.py    # SOIUSA: uMap-GeoJSON herunterladen
│   └── lookup_town_elevations.py  # Einmalig: Höhen für Orte nachschlagen
├── data/
│   ├── osm/                       # GeoJSON-Dateien (heruntergeladen)
│   └── dem/                       # DEM GeoTIFF + Tile-Cache
├── output/
│   ├── ostalpen_ave84/
│   ├── ostalpen_soiusa/
│   ├── ostalpen_pois/
│   ├── westalpen_soiusa/
│   └── westalpen_pois/
└── tests/
    ├── conftest.py
    ├── test_deck_media.py
    ├── test_deck_size.py
    └── test_image_dimensions.py
```

---

## 3. Architektur

### Datenmodell

Das Projekt folgt dem Prinzip **Region × Classification → Deck**.

```
Region                Classification              Deck / POIDeck
──────                ──────────────             ──────────────
name                  name                       region  ──► Region
bbox_west/east/…      title                      classification ──► Classification
projection_params     groups: [Gebirgsgruppe]    osm_geojson
figure_width/height   hauptgruppen               output_images_dir
cities                colors                     prefix  → "ps_ostalpen_ave84"
osm_rivers_geojson    osm_tag
osm_lakes_geojson     osm_fallback_ids           POIDeck
osm_borders_geojson                              region  ──► Region
dem_tif               POIClassification          poi_classification ──► POIClassification
                      name
                      title
                      pois: [POI]
                      category_style
```

**Gebirgsgruppe**-Felder: `group_id` · `name` · `hauptgruppe` · `hoechster_gipfel` · `osm_ref`

**POI**-Felder: `poi_id` · `name` · `category` · `lat` · `lon` · `elevation` · `subtitle` · `heading` · `tags` · `pics`

### Pipeline-Schritte

```
01_download_data.py          Geodaten herunterladen
│  ├── Overpass API          → data/osm/ostalpen_ave84.geojson (Polygone)
│  ├── Overpass API          → data/osm/osm_rivers_*.geojson
│  ├── Overpass API          → data/osm/osm_lakes_*.geojson
│  ├── Overpass API          → data/osm/osm_borders_*.geojson
│  └── SRTM 90m              → data/dem/ostalpen_dem.tif
│
02_generate_basemap.py       Shared-Basemap rendern (Raster-Pipeline)
│  ├── DEM laden + Hillshade (numpy/rasterio)
│  ├── Seen + Flüsse rasterisieren (Pillow)
│  ├── Ozean-Maske compositen
│  ├── Kompassnadel einbrennen
│  └── WebP speichern  → ps_ostalpen_ave84_basemap.webp
│                        ps_ostalpen_ave84_basemap_rot.webp
│
03_generate_cards.py         Overlay-Bilder für Polygon-Decks (Matplotlib/Cartopy)
│  ├── Partition-Map         → ps_…_partition.webp
│  ├── Context-Layer         → ps_…_context.webp
│  └── Pro Gruppe (×2)       → ps_…_group_{id}_front.webp / …_back.webp
│
03b_generate_poi_cards.py    Overlay-Bilder für POI-Decks
│  ├── Context-Layer         → ps_…_context.webp
│  ├── All-POIs-Overlay      → ps_…_all_pois.webp
│  ├── Kategorie-Badge       → ps_…_badge_{cat}.webp
│  ├── Kategorie-Highlight   → ps_…_highlight_{cat}.webp
│  ├── Pro POI (Highlight)   → ps_…_poi_{id}_highlight.(webp|json)
│  └── Pro POI (Back)        → ps_…_poi_{id}_back.webp  ← AVE84-Kontext
│
04_build_deck.py             .apkg zusammenstellen (genanki)
│  ├── Notizen pro Gruppe/POI erstellen
│  ├── Subdecks packen (SUBDECK_MERGE / POI_MULTI_DECK)
│  └── → output/ostalpen_ave84/anki_ostalpen_ave84.apkg
│
05_run_tests.py              pytest-Test-Suite
```

### Karten-Compositing in Anki

Jede Karte besteht aus mehreren WebP-Bildern, die per CSS pixelgenau gestapelt werden:

```
┌─────────────────────────────────────┐
│  Basemap (opak, immer sichtbar)     │  ← Hillshade + Seen + Flüsse
│  ── overlay: Context (toggle)       │  ← Ländergrenzen + Städte
│  ── overlay: Partition (toggle)     │  ← Alle Gruppen farbig + IDs
│  ── overlay: FrontOverlay           │  ← Fragezeichen im Polygon (Vorderseite)
│  ── overlay: BackOverlay            │  ← Farbiges Polygon (Rückseite)
└─────────────────────────────────────┘
  + BasemapRot (gedreht, per Button tauschbar)
```

Drei Toggle-Buttons auf jeder Karte:

- **▦ Einteilung** — blendet die farbige Gesamt-Partition ein/aus
- **▦ Kontext** — blendet Ländergrenzen und Städtenamen ein/aus
- **↻ Drehen** — tauscht Basemap ↔ BasemapRot (Süd-oben); rotiert Overlays per CSS

Der Button-Zustand wird per `sessionStorage` zwischen Frage- und Antwortseite
weitergereicht, sodass aufgeklappte Layer offen bleiben.

### Dateinamen-Schema

```
ps_{region}_{system}_{layer}.webp
    ───────  ──────  ───────
    ostalpen ave84   basemap
    westalpen soiusa_sz group_3b_front
             taler   partition
             gipfel  context
             pois    poi_og_01_highlight
                     all_pois
                     badge_peak
```

### Subdeck-Zusammenführung (SUBDECK_MERGE)

Kombinierte `.apkg`-Pakete fassen mehrere Systeme in einem Eltern-Deck zusammen:

```python
SUBDECK_MERGE["ostalpen_ave84"] = [
    ("ave84",  "A Gebirgsgruppen"),
    ("gipfel", "B Gipfel"),
    ("taler",  "C Täler"),
    ("paesse", "D Pässe"),
    ("seen",   "E Seen"),
    ("ave84",  "F Gebirgsgruppen visualisieren", "neighbor"),
]
```

Anki-Deck-Namen werden als `"Ostalpen AVE 84::A Gebirgsgruppen"` etc. gespeichert.
Der `"neighbor"`-Typ erzeugt eine Karte, auf der alle **Nachbargruppen** gleichzeitig
einfarbig (hellgrau) hervorgehoben werden — anders als die normale Rückseite, die nur
die eine abgefragte Gruppe zeigt.

---

## 4. Überblick über die Decks

| # | `.apkg`-Datei | Karten | Region | Subdecks |
|---|---|---|---|---|
| 1 | `ostalpen_ave84/anki_ostalpen_ave84.apkg` | 75 + 21 + 20 + 20 + 16 + 75 = **227** | Ostalpen | A–F |
| 2 | `ostalpen_soiusa/anki_ostalpen_soiusa.apkg` | 22 + 76 = **98** | Ostalpen | A–B |
| 3 | `ostalpen_pois/anki_ostalpen_pois.apkg` | ~209 | Ostalpen | A–J |
| 4 | `westalpen_soiusa/anki_westalpen_soiusa.apkg` | 14 + 55 = **69** | Westalpen | A–B |
| 5 | `westalpen_pois/anki_westalpen_pois.apkg` | ~209 | Westalpen | A–I |

Alle `.apkg`-Dateien befinden sich unter `output/`.

---

## 5. Deck 1: Ostalpen AVE 84 (Kombiniertes Deck)

**Datei:** `output/ostalpen_ave84/anki_ostalpen_ave84.apkg`  
**Region:** Ostalpen · Bbox: 9.05°O – 16.82°O / 45.2°N – 48.62°N  
**Basemap-Auflösung:** 6704 × 4320 px (8K UHD)  
**Einteilung:** AVE 84 (Alpenvereinseinteilung der Ostalpen, 1984-Revision)  
**Datenquelle:** OpenStreetMap (`ref:aveo`-Tag), osm.org  

Das Deck besteht aus 6 Subdecks, die gemeinsam in einer `.apkg`-Datei gebündelt werden.
Alle Subdecks teilen dieselbe Basemap und denselben Context-Layer. Die **Einteilung**
(▦-Button) zeigt in allen Subdecks die AVE-84-Farbpartition.

### Kartenmodell (Gebirgsgruppen & Täler)

**9 Felder:** `Group_ID` · `Name` · `Hoechster_Gipfel` · `Basemap` · `BasemapRot` ·
`FrontOverlay` · `BackOverlay` · `Partition` · `Context`

**Vorderseite:** Reliefkarte + rotes Fragezeichen im Gruppenpolygon  
**Rückseite:** Name + ID + höchster Gipfel/Kennwert + farbiges Polygon

### Kartenmodell (Gipfel, Pässe, Seen — POI-Subdecks)

**11 Felder:** `POI_ID` · `Name` · `Category` · `Info` · `Basemap` · `BasemapRot` ·
`AllPois` · `Highlight` · `BackOverlay` · `Context` · `Thumbnail`

**Vorderseite:** Reliefkarte + roter Highlight-Ring am Ziel-POI  
**Rückseite:** Name + Kategorie + Info + Karte mit AVE-84-Kontext (welche Gebirgsgruppe(n)
liegen am POI?)

---

### Subdeck 1.1: A Gebirgsgruppen

**Anki-Deckname:** `Ostalpen AVE 84::A Gebirgsgruppen`  
**Karten:** 75  
**Klassifikation:** AVE 84 (Alpenvereinseinteilung 1984)  
**Datenquelle:** OpenStreetMap `relation["ref:aveo"]`

#### Hauptgruppen & Farben

| Kurzname | Vollname | Farbe | Gruppen |
|---|---|---|---|
| N | Nördliche Ostalpen | `#4A90D9` (blau) | 27 (Nr. 1–24 + 7a, 7b, 17a, 17b) |
| Z | Zentrale Ostalpen | `#FF9500` (orange) | 27 (Nr. 25–47 + 45a–d, 46a–b) |
| S | Südliche Ostalpen | `#27AE60` (grün) | 15 (Nr. 48a–c, 49–60) |
| W | Westliche Ostalpen | `#E74C3C` (rot) | 6 (Nr. 63–68) |

#### Kartenaufbau pro Gruppe

| Bild | Dateiname | Inhalt |
|---|---|---|
| Basemap | `ps_ostalpen_ave84_basemap.webp` | Hillshade N↑ |
| BasemapRot | `ps_ostalpen_ave84_basemap_rot.webp` | Hillshade S↑ (180° rotiert) |
| Partition | `ps_ostalpen_ave84_partition.webp` | Alle 75 Gruppen farbig mit ID-Labels |
| Context | `ps_ostalpen_ave84_context.webp` | Staatsgrenzen (rot gestrichelt) + Städtenamen |
| FrontOverlay | `ps_ostalpen_ave84_group_{id}_front.webp` | Rotes Fragezeichen (Greedy Circle Packing) |
| BackOverlay | `ps_ostalpen_ave84_group_{id}_back.webp` | Farbiges ausgefülltes Polygon (α = 0.55) |

**Beispiel-Gruppen:**

- `3b` · Lechtaler Alpen · Nördliche Ostalpen · Parseierspitze (3036 m)
- `40` · Glocknergruppe · Zentrale Ostalpen · Großglockner (3798 m)
- `52` · Dolomiten · Südliche Ostalpen · Marmolata (3343 m)
- `66` · Bernina-Alpen · Westliche Ostalpen · Piz Bernina (4049 m)

---

### Subdeck 1.2: B Gipfel

**Anki-Deckname:** `Ostalpen AVE 84::B Gipfel`  
**Karten:** 21  
**Typ:** POI-Karten  
**Klassifikation:** Kuratierte Liste (März 2026), Datei `classifications/ostalpen_gipfel.py`  
**Kategorie-Stil:** Dreieck `▲`, Farbe `#B22222` (dunkelrot)

#### Inhalt

21 bedeutende Gipfel der Ostalpen mit Höhe > 2700 m (Ausnahmen: Triglav, Hohe Warte),
ausgewählt nach Prominenz, Bekanntheit für Segelflieger und AVE-84-Repräsentativität.

| Gruppe | Gipfel (Auswahl) |
|---|---|
| Zentrale Ostalpen (Hohe Tauern etc.) | Großglockner (3798 m), Großvenediger (3657 m), Hochalmspitze (3360 m), Hocharn (3254 m), Hochfeiler (3510 m), Wildspitze (3768 m), Zuckerhütl (3507 m), Ortler (3905 m), Piz Bernina (4049 m), Piz Linard (3411 m) |
| Nördliche Kalkalpen | Zugspitze (2962 m), Hoher Dachstein (2995 m), Hochkönig (2941 m), Parseierspitze (3036 m), Birkkarspitze (2749 m) |
| Südliche Ostalpen | Triglav (2864 m), Marmolata (3343 m), Presanella (3556 m), Hohe Warte (2780 m) |
| Westliche Ostalpen | Piz Kesch (3418 m), Schesaplana (2964 m) |

#### Kartenaufbau (Rückseite)

Die Rückseite zeigt die AVE-84-Gebirgsgruppe(n), in denen der Gipfel liegt:
- Enthaltende Gruppe: α = 0.75 (stark hervorgehoben)
- Angrenzende Gruppen: α = 0.35 (schwach hervorgehoben)
- Zus. roter Highlight-Ring am genauen Gipfelstandort

---

### Subdeck 1.3: C Täler

**Anki-Deckname:** `Ostalpen AVE 84::C Täler`  
**Karten:** 20  
**Typ:** Polygon-Karten (wie AVE 84, aber nach Flusseinzugsgebiet gefärbt)  
**Klassifikation:** Ostalpen Haupttäler, Datei `classifications/ostalpen_taler.py`  
**OSM-Tag:** `name` (Täler haben keinen einheitlichen Referenz-Tag)  
**Datenquelle:** Overpass (6 Relationen mit `natural=valley`) + Nominatim-Fallback (14 Ways)

#### Hauptgruppen (Einzugsgebiete) & Farben

| Einzugsgebiet | Farbe | Täler |
|---|---|---|
| Inn-System | `#2E86C1` (blau) | Inntal, Oberinntal, Unterinntal, Lechtal, Ötztal, Zillertal, Stubaital |
| Salzach-System | `#28A745` (grün) | Salzachtal, Gasteinertal |
| Enns/Mur-System | `#FF9500` (orange) | Ennstal, Murtal |
| Drau-System | `#8E44AD` (violett) | Drautal, Mölltal, Gailtal |
| Etsch/Adria-System | `#DC3545` (rot) | Wipptal, Eisacktal, Pustertal, Vinschgau |
| Rhein-System | `#6C757D` (grau) | Alpenrheintal, Montafon |

#### Besonderheit: Geometrie-Reparatur

OSM-Tal-Polygone können Selbstüberschneidungen aufweisen. Die Funktion
`render_question_mark()` in `02_generate_basemap.py` ruft vor dem
Circle-Packing `shapely.make_valid()` auf, um Topology-Exceptions zu vermeiden.

#### Kartenaufbau pro Tal

| Bild | Dateiname | Inhalt |
|---|---|---|
| Basemap | `ps_ostalpen_taler_basemap.webp` | Hillshade N↑ |
| BasemapRot | `ps_ostalpen_taler_basemap_rot.webp` | Hillshade S↑ |
| Partition | `ps_ostalpen_ave84_partition.webp` | **Geteilt mit AVE 84!** (Button zeigt AVE-84-Einteilung) |
| Context | `ps_ostalpen_taler_context.webp` | Staatsgrenzen + Städte |
| FrontOverlay | `ps_ostalpen_taler_group_{id}_front.webp` | Rotes Fragezeichen |
| BackOverlay | `ps_ostalpen_taler_group_{id}_back.webp` | Tal-Polygon + AVE-84-Kontext (semi-transparent) |

**Rückseite:** Das Tal-Polygon wird farbig dargestellt. Zusätzlich werden alle AVE-84-Gruppen,
die das Tal schneiden, als halb-transparente Überlagerung gezeigt (α = 0.30), damit der
Lernende den alpinen Kontext erkennt.

---

### Subdeck 1.4: D Pässe

**Anki-Deckname:** `Ostalpen AVE 84::D Pässe`  
**Karten:** 20  
**Typ:** POI-Karten  
**Klassifikation:** Wichtigste Pässe, Datei `classifications/ostalpen_paesse.py`  
**Kategorie-Stil:** Kreis `●`, Farbe `#2E86C1` (blau)

#### Inhalt (Auswahl nach Typ)

| Passgattung | Pässe |
|---|---|
| N–S-Verbindungen | Brennerpass (1370 m), Reschenpass (1507 m), Stilfser Joch (2757 m), Penser Joch (2211 m), Timmelsjoch (2474 m), Felbertauern (1650 m), Großglockner-HS (2504 m), Katschberg (1641 m), Radstädter Tauern (1738 m), Semmering (985 m) |
| O–W-Verbindungen | Arlbergpass (1793 m), Fernpass (1216 m), Gerlospass (1507 m), Pass Thurn (1274 m) |
| Dolomitenpässe | Sellajoch (2240 m), Grödnerjoch (2121 m), Pordoijoch (2239 m), Falzaregopass (2105 m) |
| Karawanken/Karnisch | Plöckenpass (1357 m), Predilpass (1156 m) |

#### Kartenaufbau (Rückseite)

Analog zu den Gipfeln: AVE-84-Gebirgsgruppe(n) am Passstandort hervorgehoben, 
roter Highlight-Ring am genauen Passstandort.

---

### Subdeck 1.5: E Seen

**Anki-Deckname:** `Ostalpen AVE 84::E Seen`  
**Karten:** 16  
**Typ:** POI-Karten  
**Klassifikation:** Wichtigste Seen, Datei `classifications/ostalpen_seen.py`  
**Kategorie-Stil:** Kreis `●`, Farbe `#3A9FD8` (hellblau)

#### Inhalt

| Gruppe | Seen |
|---|---|
| Voralpenseen (Nordrand) | Bodensee (536 km²), Chiemsee (80 km²), Tegernsee (9 km²), Achensee (7 km²), Wolfgangsee (13 km²), Attersee (46 km²), Traunsee (26 km²), Mondsee (14 km²) |
| Inneralpine Seen | Zeller See (4,5 km²), Millstätter See (13 km²), Wörthersee (19 km²), Ossiacher See (11 km²), Weißensee (7 km²), Reschensee (7 km²) |
| Südrand | Lago di Garda (370 km²), Klopeiner See (1 km²) |

---

### Subdeck 1.6: F Gebirgsgruppen visualisieren

**Anki-Deckname:** `Ostalpen AVE 84::F Gebirgsgruppen visualisieren`  
**Karten:** 75  
**Typ:** Nachbar-Karten (`neighbor`-Modus)  
**Klassifikation:** AVE 84 (dieselben 75 Gruppen wie Subdeck 1.1)

#### Unterschied zu Subdeck 1.1

Die **Rückseite** zeigt nicht die einzelne abgefragte Gruppe, sondern alle
**direkt angrenzenden Gruppen** gleichzeitig hellgrau hervorgehoben. So übt man,
eine Gruppe in ihrem geografischen Kontext zu verorten und Nachbargruppen zu erkennen.

Das BackOverlay-Bild heißt `ps_ostalpen_ave84_group_{id}_neighbors.webp`.

---

## 6. Deck 2: Ostalpen SOIUSA

**Datei:** `output/ostalpen_soiusa/anki_ostalpen_soiusa.apkg`  
**Region:** Ostalpen (gleiche Bbox und Basemap wie Deck 1)  
**Klassifikationssystem:** SOIUSA (Sergio Marazzi, 2005) — Alpi Orientali  
**Datenquelle:** ARPA Piemonte FeatureServer (ArcGIS REST)  

Das SOIUSA-System gliedert die Ostalpen in einer zweigliedrigen Hierarchie:
Sektion (SZ, 22 Gruppen) → Untersektion (STS, 76 Gruppen). Beide Ebenen werden
als separate Subdecks in einem `.apkg` gebündelt.

### Subdeck 2.1: A Gliederung (Sezioni)

**Anki-Deckname:** `Ostalpen SOIUSA::A Gliederung`  
**Karten:** 22  
**OSM-Tag:** `ref:soiusa` (Wert = SOIUSA-Name der Sektion in Italienisch, z.B. `"Alpi Retiche occidentali"`)

#### Sektoren & Farben

| Sektor | Farbe | SZ-Nummern | Gruppen |
|---|---|---|---|
| Zentrale Ostalpen | `#9B59B6` (violett) | 15–20 | 6 (Rätische Alpen, Tauernalpen, Steirisch-Kärntnerische A.) |
| Nördliche Ostalpen | `#3498DB` (hellblau) | 21–27 | 7 (Nordtiroler Kalkalpen – Niederösterr. Alpen) |
| Südliche Ostalpen | `#2ECC71` (grün) | 28–36 | 9 (Südl. Rätische Alpen – Slowenische Voralpen) |

#### Hierarchie auf der Rückseite

Da das SOIUSA-System hierarchisch ist, zeigt die Rückseite das Sezioni-Polygon **farbig**
und das zugehörige Eltern-Objekt (Großer Sektor, `SR`-Ebene) als schwach-transparentes
Hintergrund-Polygon.

---

### Subdeck 2.2: B Details (Sottosezioni)

**Anki-Deckname:** `Ostalpen SOIUSA::B Details`  
**Karten:** 76  
**OSM-Tag:** `ref:soiusa` (Wert = SOIUSA-Name der Untersektion)  
**Hierarchie-Tag:** `SZ` (GeoJSON-Property → Eltern-Sezione wird mitgerendert)

Feinere Gliederung der Ostalpen in 76 Untersektionen. Die Rückseite zeigt zusätzlich
die übergeordnete Sezione als transparenten Kontext.

---

## 7. Deck 3: Ostalpen Marken (POIs)

**Datei:** `output/ostalpen_pois/anki_ostalpen_pois.apkg`  
**Region:** Ostalpen  
**POI-Quelle:** *Peak Soaring* (Benjamin Bachmaier) + streckenflug.at Landewiesen  
**Gesamt-POIs:** ~209 (Hauptdeck) + ~615 Landewiesen  

Die ~615 Landewiesen-POIs befinden sich **nicht** direkt im Hauptdeck, sondern
werden zusammen mit den Peak-Soaring-POIs in regionalen Subdecks und Kategorie-Subdecks
gebündelt. Die 10 Subdecks decken Sub-Regionen (gezoomte Karte + Thumbnail) und
Kategorien (Gesamtkarte, nach POI-Typ gefiltert) ab.

### Subdeck 3.1: A Königsdorf

**Anki-Deckname:** `Ostalpen Marken::A Königsdorf`  
**Zoom-Bbox:** 10.8°O – 12.3°O / 47.23°N – 47.78°N  
**Referenzpunkt:** Flugplatz Königsdorf (~20 km N der Benediktenwand)

Zeigt alle POIs im Bereich Innsbruck–Bad Tölz–Kufstein auf einer **gezoomten** Karte.
Jede Karte enthält zusätzlich ein **Thumbnail** (Übersichtskarte mit rotem Rechteck),
das den vergrößerten Ausschnitt im Kontext der gesamten Ostalpen-BB zeigt.

POIs, die weniger als 10 % vom Bounding-Box-Rand entfernt sind, werden aus dem
Hauptdeck ausgeschlossen (`SUB_REGION_EDGE_MARGIN_FRAC = 0.10`) und nur im Subdeck geführt.

**Städte auf der Zoom-Karte:** Innsbruck, Kochel, Bad Tölz, Garmisch-P., Kufstein

---

### Subdeck 3.2: B Innsbruck

**Anki-Deckname:** `Ostalpen Marken::B Innsbruck`  
**Zoom-Bbox:** 10.8°O – 11.9°O / 46.9°N – 47.5°N  

Noch engerer Ausschnitt um Innsbruck, Karwendel, Nordkette. Städte:
Innsbruck, Mittenwald, Weilheim, Rosenheim, Miesbach, Scharnitz u.a.

---

### Subdeck 3.3 – 3.10: Kategorien C–J

Jedes Kategorie-Subdeck zeigt dieselbe Gesamtbasemap (Ostalpen), filtert aber
den `AllPois`-Overlay auf **eine Kategorie**:

| Subdeck | Deckname | Kategorie | POIs (ca.) |
|---|---|---|---|
| 3.3 | `C Gipfel` | `peak` ▲ | 82 |
| 3.4 | `D Pässe` | `pass` ⬤ | 59 |
| 3.5 | `E Orte` | `town` ■ | 24 |
| 3.6 | `F Täler` | `valley` ◆ | 43 |
| 3.7 | `G Seen` | `lake` ⬡ | 7 |
| 3.8 | `H Landefelder Kat A` | `landefeld_a` | ~327 |
| 3.9 | `I Landefelder Kat B` | `landefeld_b` | ~288 |
| 3.10 | `J Flugplätze` | `airstrip` | ~65 |

Landefelder-Karten enthalten eingebettete Fotos (Satellite + Feldfotos) aus dem
CUPX-Archiv von streckenflug.at, die im Anki-Feld `Thumbnail` gezeigt werden.

---

## 8. Deck 4: Westalpen SOIUSA

**Datei:** `output/westalpen_soiusa/anki_westalpen_soiusa.apkg`  
**Region:** Westalpen · Bbox: 4.5°O – 9.9°O / 42.8°N – 47.7°N  
**Basemap-Auflösung:** ~4320 × 6704 px (Hochformat, da die Westalpen N-S-gestreckt sind)  
**Klassifikationssystem:** SOIUSA — Alpi Occidentali (SZ 1–14)

Aufbau analog zu Deck 2, jedoch mit Westalpen-spezifischen Sezioni/Sottosezioni.

### Subdeck 4.1: A Gliederung (Sezioni)

**Anki-Deckname:** `Westalpen SOIUSA::A Gliederung`  
**Karten:** 14  
**Datenquelle:** uMap #954288 (`download_soiusa_umap.py`) für SZ 1–14

Sezioni SZ 1–14 entsprechen den Alpi Occidentali: Alpi Graie, Cozie, Marittime,
Liguri, Pennine, Lepontine, Luganeser Alpen, Reiner Alpen usw.

---

### Subdeck 4.2: B Details (Sottosezioni)

**Anki-Deckname:** `Westalpen SOIUSA::B Details`  
**Karten:** 55  
**Datenquelle:** ARPA Piemonte FeatureServer

55 Untersektionen der Westalpen, mit Eltern-Sezione als transparentem Kontext
auf der Rückseite.

---

## 9. Deck 5: Westalpen Marken (POIs)

**Datei:** `output/westalpen_pois/anki_westalpen_pois.apkg`  
**Region:** Westalpen  
**POI-Quelle:** *Peak Soaring* (gleiche Datei `peak_soaring_pois.py`, aber auf Westalpen-Bbox gefiltert)

### Subdeck 5.1: A Puimoisson

**Anki-Deckname:** `Westalpen Marken::A Puimoisson`  
**Zoom-Bbox:** 5.0°O – 7.5°O / 43.1°N – 45.6°N  
**Referenzpunkt:** Aérodrome de Puimoisson (Haute-Provence)

Zoomed Karte um die Seealpen, Hautes-Alpes und Provence. Städte: Digne, Sisteron,
Barcelonnette, Gap, Briançon, Nizza, Grenoble, Manosque u.a.

---

### Subdeck 5.2 – 5.9: Kategorien B–I

Entsprechend Deck 3, aber für die Westalpen-POI-Sammlung:

| Subdeck | Deckname | Kategorie |
|---|---|---|
| 5.2 | `B Gipfel` | `peak` |
| 5.3 | `C Pässe` | `pass` |
| 5.4 | `D Orte` | `town` |
| 5.5 | `E Täler` | `valley` |
| 5.6 | `F Seen` | `lake` |
| 5.7 | `G Landefelder Kat A` | `landefeld_a` |
| 5.8 | `H Landefelder Kat B` | `landefeld_b` |
| 5.9 | `I Flugplätze` | `airstrip` |
