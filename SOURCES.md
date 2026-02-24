# Datenquellen / Data Sources

Alle verwendeten Geodaten mit exakten Quellen, Lizenzen und Abrufmethoden.

---

## 1. Gebirgsgruppen-Polygone

### AVE 84 (Ostalpen)

| Eigenschaft | Wert |
|---|---|
| **Quelle** | [OpenStreetMap](https://www.openstreetmap.org/) |
| **Tag** | `ref:aveo` (Alpenvereinseinteilung der Ostalpen 1984) |
| **Abfrage** | Overpass API — `relation["ref:aveo"]` |
| **API-Endpunkt** | `https://overpass-api.de/api/interpreter` |
| **Anzahl Gruppen** | 75 |
| **Format** | GeoJSON (konvertiert aus Overpass JSON) |
| **Lizenz** | [ODbL 1.0](https://opendatacommons.org/licenses/odbl/) — © OpenStreetMap Contributors |
| **Script** | `scripts/01_download_data.py --region ostalpen` |
| **Ausgabedatei** | `data/osm/ostalpen_ave84.geojson` |

### SOIUSA Sezioni (Westalpen) — uMap-Quelle

| Eigenschaft | Wert |
|---|---|
| **Quelle** | [uMap #954288](https://umap.openstreetmap.fr/de/map/soiusa_954288) |
| **Ersteller** | Capleymar (basierend auf homoalpinus.com, offline seit ~2023) |
| **Anzahl Sezioni** | 14 (SZ.1 – SZ.14) |
| **Format** | GeoJSON (konvertiert aus uMap JSON) |
| **Lizenz** | Nicht explizit angegeben; abgeleitet von OSM-basierten Geodaten |
| **Script** | `scripts/download_soiusa_umap.py` |
| **Ausgabedatei** | `data/osm/westalpen_soiusa_sz.geojson` |

### SOIUSA (alle Ebenen) — ARPA Piemonte

| Eigenschaft | Wert |
|---|---|
| **Quelle** | [ARPA Piemonte FeatureServer](https://webgis.arpa.piemonte.it/ags/rest/services/topografia_dati_di_base/SOIUSA/FeatureServer) |
| **Autoren** | Sergio Marazzi et al. (Orographische Einteilung), Massimo Accorsi (Digitalisierung) |
| **Herausgeber** | Arpa Piemonte (Geoservizio) |
| **Typ** | ArcGIS REST FeatureServer |
| **Räumliches Bezugssystem** | EPSG:3857 (Web Mercator) — Abfrage mit `outSR=4326` für WGS84 |
| **Lizenz** | Frei nutzbar mit Pflicht zur Quellenangabe des Autors |
| **Copyright-Text** | „L'autore è Massimo Accorsi — Venezia Italia. L'utilizzo dei dati è libero ma è fatto obbligo di citazione dell'autore" |
| **Script** | `scripts/download_soiusa_arpa.py` |

**Verfügbare Ebenen (Layer):**

| Kürzel | Layer-ID | Name | Features (ca.) |
|--------|----------|------|----------------|
| PT | 1 | Parte (Alpenteil) | 2 |
| SR | 3 | Grande Settore (Großer Sektor) | 5 |
| SZ | 5 | Sezione (Sektion) | 36 |
| STS | 7 | Sottosezione (Untersektion) | ~130 |
| SPG | 9 | Supergruppo (Supergruppe) | ~200 |
| GR | 11 | Gruppo (Gruppe) | ~870 |

**Attributfelder pro Feature:** `OBJECTID`, `ID`, `PT`, `SR`, `SZ`, `STS`, `SPG`, `GR`, `STG`, `CODICE`, `SHAPE_LENG`, `Shape__Area`

**Verwendete Regionsfilter:**

| Region | Filter (`PT`) | Script-Aufruf |
|--------|---------------|---------------|
| Westalpen | `Alpi Occidentali` | `download_soiusa_arpa.py --region westalpen` |
| Ostalpen | `Alpi Orientali` | `download_soiusa_arpa.py --region ostalpen` |

**Erzeugte Dateien:**

| Datei | Region | Ebene | Gruppen |
|-------|--------|-------|---------|
| `data/osm/westalpen_soiusa_sts.geojson` | Westalpen | STS | 55 |
| `data/osm/ostalpen_soiusa_sz.geojson` | Ostalpen | SZ | 22 |
| `data/osm/ostalpen_soiusa_sts.geojson` | Ostalpen | STS | 76 |

---

## 2. Grenzen, Flüsse, Seen (OSM)

### Landesgrenzen

| Eigenschaft | Wert |
|---|---|
| **Quelle** | [OpenStreetMap](https://www.openstreetmap.org/) |
| **Abfrage** | Overpass API — `relation["admin_level"="2"]["boundary"="administrative"]` |
| **Format** | GeoJSON |
| **Lizenz** | [ODbL 1.0](https://opendatacommons.org/licenses/odbl/) — © OpenStreetMap Contributors |
| **Ausgabedateien** | `data/osm/osm_borders_ostalpen.geojson`, `data/osm/osm_borders_westalpen.geojson` |

### Flüsse

| Eigenschaft | Wert |
|---|---|
| **Quelle** | [OpenStreetMap](https://www.openstreetmap.org/) |
| **Abfrage** | Overpass API — `relation["waterway"="river"]` (gefiltert nach Bbox) |
| **Format** | GeoJSON |
| **Lizenz** | [ODbL 1.0](https://opendatacommons.org/licenses/odbl/) — © OpenStreetMap Contributors |
| **Ausgabedateien** | `data/osm/osm_rivers_ostalpen.geojson`, `data/osm/osm_rivers_westalpen.geojson` |

### Seen

| Eigenschaft | Wert |
|---|---|
| **Quelle** | [OpenStreetMap](https://www.openstreetmap.org/) |
| **Abfrage** | Overpass API — `relation["natural"="water"]["water"="lake"]` (gefiltert nach Bbox) |
| **Format** | GeoJSON |
| **Lizenz** | [ODbL 1.0](https://opendatacommons.org/licenses/odbl/) — © OpenStreetMap Contributors |
| **Ausgabedateien** | `data/osm/osm_lakes_ostalpen.geojson`, `data/osm/osm_lakes_westalpen.geojson` |

---

## 3. Höhenmodell (DEM)

| Eigenschaft | Wert |
|---|---|
| **Quelle** | [CGIAR-CSI SRTM 90m v4.1](https://srtm.csi.cgiar.org/) |
| **Originaldaten** | NASA Shuttle Radar Topography Mission (SRTM) |
| **Auflösung** | 90 m (3 Bogensekunden) |
| **Format** | GeoTIFF |
| **Lizenz** | Frei nutzbar für nicht-kommerzielle und kommerzielle Zwecke, Quellenangabe erforderlich |
| **Zitierweise** | Jarvis A., H.I. Reuter, A. Nelson, E. Guevara, 2008, Hole-filled seamless SRTM data V4, International Centre for Tropical Agriculture (CIAT), available from https://srtm.csi.cgiar.org |
| **Tiles** | Gespeichert in `data/dem/tiles/` |

---

## 4. Zusammenfassung der Lizenzen

| Datenquelle | Lizenz | Attribution |
|---|---|---|
| OpenStreetMap | ODbL 1.0 | © OpenStreetMap Contributors |
| ARPA Piemonte SOIUSA | Frei mit Quellenangabe | Massimo Accorsi, Sergio Marazzi et al., Arpa Piemonte |
| uMap SOIUSA | Nicht explizit | Capleymar / homoalpinus.com |
| CGIAR-CSI SRTM | Frei nutzbar | Jarvis et al. 2008, CIAT |
