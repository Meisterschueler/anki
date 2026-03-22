# Peak Soaring Anki — Pipeline & Dateistruktur

> Dieses Dokument ist Teil der [Ideal Specification](ideal_specification.md).

---

## 6. Technischer Stack

### Sprache & Laufzeit

- **Python 3.11+** (empfohlen: aktuellste 3.x-Version, pyenv zur Versionsverwaltung)
- **Virtuelle Umgebung:** `venv` (Standard-Library, kein Conda nötig)

### Pflicht-Bibliotheken

| Bibliothek | Version (min.) | Zweck |
|---|---|---|
| `numpy` | 1.26 | Hillshade-Berechnung, Array-Operationen |
| `rasterio` | 1.3 | DEM (GeoTIFF) einlesen und neu samplen |
| `Pillow` | 10.0 | Basemap compositing, WebP-Export, Kompassnadel |
| `matplotlib` | 3.8 | Figur-/Axes-Verwaltung, Overlay-Rendering |
| `cartopy` | 0.23 | Kartenprojektion (PlateCarree / LCC) |
| `geopandas` | 0.14 | GeoJSON laden, Shapely-Operationen auf DataFrames |
| `shapely` | 2.0 | Polygon-Geometrie, Topologie-Reparatur (`make_valid`) |
| `genanki` | >=0.13,<1.0 | Anki-`.apkg`-Erzeugung (Notizen, Modelle, Decks) |
| `requests` | 2.31 | HTTP (Overpass API, SRTM-Tiles, ARPA) |
| `requests-cache` | 1.2 | Transparenter Disk-Cache für HTTP-Anfragen (Overpass) |
| `tqdm` | 4.66 | Fortschrittsanzeige beim Download |
| `pytest` | 7.4 | Test-Framework |
| `mypy` | 1.8 | Statische Typprüfung (Development-Abhängigkeit) |
| `ruff` | 0.4 | Linter + Formatter (Development-Abhängigkeit) |

### Paket-Verwaltung

- **`pyproject.toml`** als primäre Paketkonfiguration (PEP 621). Damit sind
  Abhängigkeiten, Mindestversionen und Metadaten an einem Ort definiert.
- **Lockfile** per `uv lock` oder `pip-compile` (pip-tools) erzeugen und ins
  Repository committen. Das Lockfile garantiert reproduzierbare Builds.
- `requirements.txt` wird aus `pyproject.toml` generiert (z.B. `uv export`) und
  bleibt als Fallback für einfache `pip install` Workflows erhalten.
- Entwicklungs-Abhängigkeiten (`mypy`, `pytest`, `ruff`) in einer separaten
  `[project.optional-dependencies]`-Gruppe `dev`.

### Typ-Annotierungen & statische Analyse

Alle Funktionen in Skripten und Hilfsdateien tragen vollständige Typ-Annotierungen:

```python
def _osm_json_to_geojson(
    data: dict[str, Any],
    name_field: str,
    fallback_ids: dict[str, int] | None = None,
) -> dict[str, Any]: ...
```

`mypy --strict` (oder `pyright`) läuft als pre-commit Hook und im CI. Dataclasses
verwenden `from __future__ import annotations`.

### Logging

Skripte verwenden `logging` statt `print()`. Standardlevel: `INFO`. Das CLI-Flag
`--verbose` schaltet auf `DEBUG` um:

```python
import logging
log = logging.getLogger(__name__)
log.info("Downloading %d valleys...", len(groups))
log.warning("Fallback to OSM-ID for %s", name)
log.debug("Overpass response: %d elements", len(data["elements"]))
```

### Keine optionalen Abhängigkeiten

Alle Abhängigkeiten sind in `pyproject.toml` festzuhalten. Optionale Extras
(`[dev]`) dürfen nur Testing/Linting enthalten.

### Virtuelle Umgebung einrichten

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

---

## 7. Pipeline

Die Pipeline besteht aus 5 nummerierten Skripten, die in Reihenfolge ausgeführt werden.
Jedes Skript ist idempotent: bereits vorhandene Ausgaben werden übersprungen (außer bei
`--force`).

### Schritt 1 — Geodaten herunterladen (`download_data.py`)

```
python scripts/download_data.py --region ostalpen [--system ave84] [--skip-dem]
```

**Ausgaben:**

| Datei | Quelle | Inhalt |
|---|---|---|
| `data/osm/{region}_{system}.geojson` | Overpass API | Polygon-Grenzen der Gebirgsgruppen/Täler |
| `data/osm/osm_rivers_{region}.geojson` | Overpass API | Flüsse ≥ 20 km |
| `data/osm/osm_lakes_{region}.geojson` | Overpass API | Seen ≥ 0.2 km² |
| `data/osm/osm_valleys_{region}.geojson` | Overpass API | Täler (für Overlay) |
| `data/osm/osm_borders_{region}.geojson` | Overpass API | Staatsgrenzen |
| `data/dem/{region}_dem.tif` | SRTM 90m (CGIAR-CSI) | Digitales Höhenmodell |

**Robustheit:** 3 automatische Retries mit 10 s Pause. Polygon-Download in zwei Phasen:
1. Primär: Query nach OSM-Tag (z.B. `ref:aveo`) im Bbox-Bereich
2. Fallback: OSM-IDs direkt abrufen (`osm_fallback_ids` in der Classification-Klasse)

**HTTP-Cache (B3):** Alle Overpass-Anfragen werden transparent gecacht
(`requests-cache`, SQLite-Backend, TTL: 30 Tage). `--force` erzwingt das
Neu-Rendering von Bildern, umgeht aber **nicht** den HTTP-Cache für
Overpass-Abfragen (Geodaten bleiben gecacht). Um auch den Cache zu umgehen:
`--clear-cache`-Flag verwenden oder `data/.http_cache/` manuell löschen.
Cache-Pfad: `data/.http_cache/overpass.sqlite`.

Für Täler-Polygone (keine einheitlichen OSM-Tags): gezielte Query pro Talname statt
Bbox-Scan (Timeout-Vermeidung), Fallback auf Way-IDs falls keine Relation gefunden.

**POI-Decks** haben keine zu downloadenden Polygon-Dateien; hier wird nur
DEM/Flüsse/Seen/Grenzen heruntergeladen.

### Schritt 2 — Basemap rendern (`generate_basemap.py`)

```
python scripts/generate_basemap.py --region ostalpen [--system ave84]
```

Die Basemap ist eine opake RGB-WebP-Datei. Sie wird rein rasterbasiert erzeugt
(kein Matplotlib für den Basemap-Hintergrund — nur für Overlays):

1. **DEM laden** (rasterio) → auf ≤ 7680 px Kantenlänge downsampeln (falls nötig)
2. **Höhen kappen** bei 4200 m (verhindert Überbelichtung schneebedeckter Gipfel)
3. **Hillshade** (numpy LightSource): Azimut 315°, Altitude 45°, vertikale Überhöhung 0.05
4. **Terrain-Colormap** (grün → braun → weiß) mit Soft-Blending über Hillshade
5. **Ozean-Maske** in `#c6ddf0` compositen (Flächen außerhalb NE Land-Polygon)
6. **Seen** rasterisieren aus OSM-GeoJSON (Farbe `#7FAFCF`, Kontur `#4A7FB5`)
7. **Flüsse** rasterisieren (blau, 2× Anti-Aliasing)
8. **Kompassnadel** einbrennen (oben rechts, 2 % der kurzen Kante)
9. Als opake WebP (Quality 90) speichern

Zweite Variante (BasemapRot): Azimut 135°, danach Pillow `rotate(180°)`, Kompassnadel N↓.

Dritte Variante (BasemapBlind): Identisch zur normalen Basemap, aber **ohne**
Kompassnadel-Rendering. Wird für Subdeck G (Orientierungsmodus) benötigt.

**Grund für rasterbasiertes Compositing:** matplotlib/cartopy-Renderer haben für
8K-UHD-Bilder einen zu hohen Speicher- und Zeitaufwand für Raster-Hintergründe.

### Schritt 3a — Polygon-Overlays (`generate_cards.py`)

```
python scripts/generate_cards.py --region ostalpen --system ave84 [--force] [--ids 3b,40]
```

Rendert transparente RGBA-WebP-Overlays mit Matplotlib + Cartopy:

| Bild | Inhalt |
|---|---|
| `partition.webp` | Alle Gruppen farbig (nach Hauptgruppe) + ID-Labels |
| `context.webp` | Staatsgrenzen (rot, gestrichelt) + Städtenamen |
| `group_{id}_front.webp` | Rotes Fragezeichen im Polygon (Greedy Circle Packing) |
| `group_{id}_back.webp` | Farbiges ausgefülltes Polygon (α = 0.55); bei hierarchischen Systemen + Eltern-Polygon transparent |

**Fragezeichen-Algorithmus (Circle Packing):**
1. Polylabel (größter einbeschriebener Kreis) des Polygons berechnen
2. Fragezeichen in diesen Kreis setzen, Kreis aus Polygon herausschneiden
3. Wiederholen auf dem Rest, bis Radius < 45 % des Maximalradius oder Rest < 40 % der Fläche
4. Fontgröße proportional zum Kreisradius (in Grad → Punkte umgerechnet)
5. Vor dem Start: `shapely.make_valid()` aufrufen, um OSM-Topologiefehler zu reparieren

**Paralleles Rendering (B4):** Alle Gruppen werden parallel mit `ProcessPoolExecutor`
gerendert (je Gruppe ein eigener Prozess — matplotlib ist nicht thread-safe). Die Basemap
muss vollständig vorliegen, bevor paralleles Overlay-Rendering beginnt. Erwarteter
Speedup auf einem 4-Core-System: 3–4× (statt ~8 min dann ~2–3 min für 75 Gruppen).

### Schritt 3b — POI-Overlays (`generate_poi_cards.py`)

```
python scripts/generate_poi_cards.py --region ostalpen --system gipfel [--force]
```

| Bild | Inhalt |
|---|---|
| `context.webp` | Staatsgrenzen + Städte (wie Polygon-Decks) |
| `all_pois.webp` | Alle POI-Marker der Klassifikation gleichzeitig |
| `all_pois_group_{id}.webp` | Nur POIs der jeweiligen Hauptgruppe (Gruppenfilter-Toggle, C4) |
| `badge_{cat}.webp` | Kleines Kategorie-Icon (Dreick für peak, ○ für pass …) |
| `highlight_{cat}.webp` | Highlight-Ring-Sprite geteilt für eine Kategorie |
| `poi_{id}_highlight.(webp\|json)` | Highlight-Kreis / Positionsring für diesen POI |
| `poi_{id}_back.webp` | Rückseiten-Overlay: AVE-84-Kontextpolygone für diesen POI |

Die AVE-84-Rückseite zeigt:
- **Enthaltende Gruppe:** α = 0.75 (stark hervorgehoben)
- **Angrenzende Gruppen:** α = 0.35 (als Kontext)
- **Roter Highlight-Ring** am genauen POI-Standort

**Paralleles Rendering (B4):** Analog zu Schritt 3a können POI-Overlays parallel
gerendert werden (ProcessPoolExecutor, max_workers = CPU-Kerne).

### Schritt 4 — `.apkg` bauen (`build_deck.py`)

```
python scripts/build_deck.py --region ostalpen --system ave84
```

Erzeugt ein genanki-basiertes Anki-Paket. Bilder werden automatisch generiert wenn
nicht vorhanden (ruft Schritt 3a oder 3b auf).

**Kartenvorlagen** für HTML/CSS sind aus dem Python-Code ausgelagert und liegen als
eigene Dateien in `templates/` (siehe [Dateistruktur](#8-dateistruktur)). Das Skript
lädt sie per `Path("templates/...").read_text()`. Vorteil: IDE-Syntax-Highlighting,
separates CSS-Linting und bessere Git-Diffs.

**Zwei Anki-Kartenmodelle** (zentral in `build_deck.py` definiert, versioniert):

*Modell A — Gebirgsgruppe (10 Felder):*

| Feld | Inhalt |
|---|---|
| `Group_ID` | z.B. `3b` |
| `Name` | z.B. `Lechtaler Alpen` |
| `Hoechster_Gipfel` | z.B. `Parseierspitze (3036 m)` |
| `Basemap` | `<img class="basemap" src="ps_…_basemap.webp">` |
| `BasemapRot` | `<img class="basemap-rot" src="ps_…_basemap_rot.webp">` |
| `BasemapBlind` | `<img class="basemap-blind" src="ps_…_basemap_blind.webp">` |
| `FrontOverlay` | `<img class="overlay" src="ps_…_group_3b_front.webp">` |
| `BackOverlay` | `<img class="overlay" src="ps_…_group_3b_back.webp">` |
| `Partition` | `<img class="overlay partition" src="ps_…_partition.webp">` |
| `Context` | `<img class="overlay context" src="ps_…_context.webp">` |

*Modell B — POI (12 Felder):*

| Feld | Inhalt |
|---|---|
| `POI_ID` | z.B. `og_01` |
| `Name` | z.B. `Großglockner` |
| `Category` | z.B. `Gipfel` |
| `Info` | z.B. `3798 m · AVE 84 Nr. 40 · Glocknergruppe` |
| `Hint` | z.B. `Zentralalpen / Tirol` (optional, leer wenn nicht befüllt) |
| `Basemap` | `<img class="basemap" …>` |
| `BasemapRot` | `<img class="basemap-rot" …>` |
| `AllPois` | `<img class="overlay allpois" …>` |
| `Highlight` | `<img class="overlay" …>` |
| `BackOverlay` | `<img class="overlay" …>` |
| `Context` | `<img class="overlay context" …>` |
| `Thumbnail` | `<img class="thumbnail" …>` oder leer (Mustache-Konditional) |

**Subdeck-Zusammenführung:** Mehrere Systeme können als Subdecks in ein `.apkg` gebündelt
werden. Die Konfiguration erfolgt durch `SUBDECK_MERGE` in `registry.py` (typisiert via
`SubdeckSpec` — ersetzt positionale Tupel):

```python
SUBDECK_MERGE["ostalpen_ave84"] = [
    SubdeckSpec("ave84",  "A Gebirgsgruppen"),
    SubdeckSpec("gipfel", "B Gipfel"),
    SubdeckSpec("taler",  "C Täler"),
    SubdeckSpec("paesse", "D Pässe"),
    SubdeckSpec("seen",   "E Seen"),
    SubdeckSpec("ave84",  "F Gebirgsgruppen visualisieren", card_type="neighbor"),
    SubdeckSpec("ave84",  "G Orientierung",                card_type="blind_orientation"),
]
```

Anki-Deck-Bezeichnung: `"Ostalpen AVE 84::A Gebirgsgruppen"` usw.

### Schritt 5 — Tests (`run_tests.py`)

```
python scripts/run_tests.py
```

Delegiert an pytest. Einzelne Testklassen können mit `-k` gefiltert werden.

---

## 8. Dateistruktur

```
anki/
├── pyproject.toml               # Paket-Metadaten, Abhängigkeiten (ersetzt requirements.txt)
├── requirements.txt             # Generiert aus pyproject.toml (Fallback für pip install)
├── uv.lock                      # Lockfile (reproduzierbare Builds; im Git)
│
├── config.py                    # Globale Rendering-Konstanten (A1):
│                                #   FIGURE_DPI, BASEMAP_LONG_EDGE, HILLSHADE_AZIMUTH …
├── registry.py                  # Deck-Registry (A1):
│                                #   VALID_COMBINATIONS, SUBDECK_MERGE (SubdeckSpec)
│                                #   _REGION_REGISTRY, _CLASSIFICATION_REGISTRY
├── deck.py                      # Schlanke API-Schicht (A1):
│                                #   get_deck(), get_region(), get_classification()
├── models.py                    # Dataclasses Region, Classification, Deck,
│                                #   POI, RenderConfig, SubdeckSpec, Gebirgsgruppe
│
├── regions/                     # Eine Datei pro geografische Region
│   ├── __init__.py
│   ├── ostalpen.py              # REGION-Objekt: Bbox, Projektion, Städte, Pfade
│   └── westalpen.py
│
├── classifications/             # Eine Datei pro Klassifikationssystem
│   ├── ave84.py                 # CLASSIFICATION + get_classification() — 75 AVE-84-Gruppen
│   ├── ostalpen_soiusa_sz.py    # CLASSIFICATION — 22 Sezioni
│   ├── ostalpen_soiusa_sts.py   # CLASSIFICATION — 76 Sottosezioni
│   ├── westalpen_soiusa_sz.py   # CLASSIFICATION — 14 Sezioni
│   ├── westalpen_soiusa_sts.py  # CLASSIFICATION — 55 Sottosezioni
│   ├── ostalpen_taler.py        # CLASSIFICATION — 20 Täler
│   ├── ostalpen_einzugsgebiete.py # CLASSIFICATION — ~10 Einzugsgebiete (HydroBASINS)
│   ├── ostalpen_gipfel.py       # CLASSIFICATION (POI) — 21 Gipfel
│   ├── ostalpen_paesse.py       # CLASSIFICATION (POI) — 20 Pässe
│   ├── ostalpen_seen.py         # CLASSIFICATION (POI) — 16 Seen
│   ├── peak_soaring_pois.py     # ~215 POIs aus dem Buch "Peak Soaring"
│   └── landewiesen.py           # ~615 Außenlandewiesen (streckenflug.at CUPX)
│
├── templates/                   # Anki-Kartenvorlagen (A6) — HTML/CSS ausgelagert
│   ├── card_model_a.front.html  # Polygon-Karten Vorderseite
│   ├── card_model_a.back.html   # Polygon-Karten Rückseite
│   ├── card_model_a.css         # Gemeinsames CSS (Basemap, Overlays, Buttons)
│   ├── card_model_b.front.html  # POI-Karten Vorderseite
│   ├── card_model_b.back.html   # POI-Karten Rückseite
│   └── card_model_b.css
│
├── scripts/                     # Pipeline-Skripte (A2 — keine führenden Ziffern)
│   ├── download_data.py         # Schritt 1
│   ├── generate_basemap.py      # Schritt 2
│   ├── generate_cards.py        # Schritt 3a (Polygon-Decks)
│   ├── generate_poi_cards.py    # Schritt 3b (POI-Decks)
│   ├── build_deck.py            # Schritt 4
│   ├── run_tests.py             # Schritt 5
│   └── render_utils.py          # Geteilte Hilfsfunktionen (save_figure, context)
│
├── tools/                       # Einmalige Werkzeuge (A7 — nicht Teil der Pipeline)
│   ├── download_soiusa_arpa.py  # Einmalig: SOIUSA von ARPA laden
│   ├── download_soiusa_umap.py  # Einmalig: SOIUSA Westalpen von uMap laden
│   ├── prepare_einzugsgebiete.py # Einmalig: HydroBASINS → Einzugsgebiet-GeoJSON
│   └── lookup_town_elevations.py # Einmalig: Höhen für Ortsnamen nachschlagen
│
├── data/                        # Heruntergeladene Quelldaten (nicht im Git)
│   ├── osm/                     # GeoJSON-Dateien
│   ├── dem/                     # DEM GeoTIFF + Tile-Cache
│   └── .http_cache/             # requests-cache SQLite-Datenbank (B3)
│       └── overpass.sqlite
│
├── output/                      # Erzeugte Bilder und .apkg (nicht im Git)
│   ├── ostalpen_ave84/
│   │   ├── anki_ostalpen_ave84.apkg
│   │   ├── manifest.json        # Deck-Manifest mit SHA256-Hashes (B9)
│   │   └── images/
│   ├── ostalpen_soiusa/
│   ├── ostalpen_pois/
│   ├── westalpen_soiusa/
│   └── westalpen_pois/
│
└── tests/
    ├── unit/                    # Kein Pre-built-Output erforderlich (B6)
    │   ├── test_config.py       # Konstanten, VALID_COMBINATIONS Konsistenz
    │   ├── test_filename_schema.py
    │   ├── test_registry.py     # get_deck(), get_region() mit Mock-Daten
    │   └── test_geometry_helpers.py
    └── integration/             # Setzt gerenderte Ausgaben voraus
        ├── conftest.py          # Fixtures: deck, image_dir, apkg_path
        ├── test_deck_media.py   # .apkg enthält alle referenzierten Bilder (via manifest.json)
        ├── test_deck_size.py    # Kartenanzahl je Deck korrekt
        └── test_image_dimensions.py # Alle Layer-Bilder eines Decks gleich groß
```

**`.gitignore` — was nicht ins Repository gehört:**

```
data/dem/
data/osm/
data/.http_cache/
output/
.venv/
__pycache__/
*.pyc
```

---

## 9. Konfiguration & Erweiterbarkeit

### Neue Region hinzufügen

1. Neue Datei `regions/{name}.py` mit `REGION`-Objekt anlegen
2. In `registry.py` zu `_REGION_REGISTRY` und `VALID_COMBINATIONS` hinzufügen
3. Klassifikationsdatei(en) für diese Region anlegen (s.u.)

### Neue Klassifikation hinzufügen

1. Neue Datei `classifications/{region}_{name}.py` mit `CLASSIFICATION`-Objekt anlegen
2. In `registry.py` zu `_CLASSIFICATION_REGISTRY` und `VALID_COMBINATIONS` hinzufügen
3. Falls es ein kombinierbares Subdeck ist: Eintrag in `SUBDECK_MERGE` (`registry.py`) ergänzen
4. Download-Logik: Standard-`download_polygons()` wählen oder eigene Funktion
   (wie `download_taler_polygons()` für Täler ohne einheitliches OSM-Tag)

**Factory-Muster (A4):** Jede Klassifikationsdatei exportiert ein Modul-Level-Singleton
`CLASSIFICATION` für den Normalfall sowie eine `get_classification(override=None)`-Fabrik-
funktion für parametrisiertes Laden (Tests, Rendering-Overrides). Damit bleibt
Rückwärtskompatibilität erhalten, während gezieltes Mocking möglich ist.

### Neue POI-Klassifikation hinzufügen

1. Neue Datei `classifications/{name}.py` mit `POIClassification`-Objekt
2. In `registry.py` zu `_POI_SYSTEMS` und `_POI_CLASSIFICATION_MODULE_REGISTRY` hinzufügen
3. In `VALID_COMBINATIONS` ergänzen

### Globale Rendering-Konstanten

Alle Rendering-Parameter (Hillshade-Azimut, Bildauflösung, Polygon-Alpha, Fluss-Mindestlänge
usw.) sind als Modulkonstanten in `config.py` zentralisiert (A1, nicht mehr in `deck.py`).
Beispiele:

```python
FIGURE_DPI = 480
BASEMAP_LONG_EDGE = 7680     # px — maximale Kantenlänge (8K UHD)
HILLSHADE_AZIMUTH = 315      # Grad
POLYGON_ALPHA = 0.55
RIVER_MIN_LENGTH_KM = 20
LAKE_MIN_AREA_KM2 = 0.2
QMARK_MIN_RADIUS_RATIO = 0.45

# Anki-Modell-IDs (B6): bei jedem Feld-Änderung ANKI_MODEL_VERSION erhöhen;
# bestehende Decks müssen danach neu importiert werden.
ANKI_MODEL_VERSION = 2
ANKI_MODEL_ID_A = 1607392315 + ANKI_MODEL_VERSION
ANKI_MODEL_ID_B = 1607392316 + ANKI_MODEL_VERSION
```
