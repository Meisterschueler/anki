# Peak Soaring Anki — Konzept & Architektur

**Version:** 2.1  
**Datum:** März 2026  
**Sprache:** Dieses Dokument ist auf Deutsch, da es sich an deutschsprachige Nutzer richtet.

> Dieses Dokument ist Teil der [Ideal Specification](ideal_specification.md).

---

## 1. Projektziel

Das System generiert **Anki-Lerndecks** für die Alpen, primär für Segelflieger, die
Geländekenntnisse erlernen oder festigen möchten.

**Lernziele:**

- Gebirgsgruppen auf einer Reliefkarte erkennen und benennen (Klassifikationssysteme AVE 84, SOIUSA)
- Täler, Gipfel, Pässe und Seen identifizieren und geografisch einordnen
- Außenlandewiesen nach ihrer Lage kennen

**Nicht-Zielt** des Systems:

- Navigation oder Flugrouten-Planung
- Echtzeit-Wetterdaten
- Mobile App oder Webdienst

---

## 2. Lernkarten-Konzept

### Grundprinzip

Jede Karte enthält eine **Reliefkarte der Alpen** (Hillshade-Rendering aus SRTM-Höhendaten).
Über die Basemap werden transparente WebP-Overlays in Anki gestapelt (CSS `position: absolute`).

**Vorderseite:** Die geografische Einheit (Gebirgsgruppe, Tal, Gipfel, …) ist markiert,
aber nicht beschriftet — der Lernende muss sie benennen.

**Rückseite:** Name, ID/Kategorie und Kenndaten werden angezeigt, das markierte
Objekt ist farbig hervorgehoben.

### Interaktive Ebenen

Polygon-Karten haben drei Toggle-Buttons; POI-Karten haben vier:

| Button | Funktion | Standardzustand |
|---|---|---|
| **▦ Einteilung** | Zeigt die vollständige Farbpartition aller Gruppen mit IDs | aus |
| **▦ Kontext** | Zeigt Staatsgrenzen (rot gestrichelt) und Städtenamen | aus |
| **↻ Drehen** | Tauscht die Karte zu Süd-oben (erschwerter Modus) | aus |

Der Button-Zustand wird per `localStorage` zwischen Vorder- und Rückseite sowie über
Lernsitzungen hinweg persistiert (bleibt auf dem Gerät erhalten; wird nicht über
AnkiWeb-Sync auf andere Geräte übertragen — dieses Verhalten in der Deck-Beschreibung
dokumentieren).

**Drehen-Mechanismus:** Es gibt zwei Basemap-Varianten: eine normale (Norden oben,
Hillshade-Azimut 315°) und eine vorrotiert gespeicherte Variante (Süden oben, Azimut 135°,
Bild bereits um 180° rotiert gespeichert). Beim Drehen werden Basemap ↔ BasemapRot
getauscht und alle Overlay-Bilder per CSS um 180° rotiert. Da BasemapRot bereits als
Süd-oben-Bild gespeichert ist, bleibt die Schattenrichtung des Hillshade korrekt.
In jede Basemap ist eine Kompassnadel eingebrannt (N↑ bzw. N↓ für BasemapRot).

### Kartentypen

Es gibt zwei grundlegend verschiedene Kartentypen:

**Typ A — Polygon-Karte** (für Gebirgsgruppen und Täler):  
Vorderseite: rotes Fragezeichen im Polygon-Inneren (Greedy Circle Packing).  
Rückseite: farbig ausgefülltes Polygon, optional mit übergeordnetem Kontext-Polygon.

**Typ B — POI-Karte** (für Gipfel, Pässe, Seen, Orte, Landewiesen):  
Vorderseite: roter Highlight-Ring am Zielort.  
Rückseite: alle POIs der Kategorie als Marker + Zielort hervorgehoben +
optional AVE-84-Kontextpolygone (welche Gebirgsgruppe liegt hier?).

---

## 3. Systemüberblick

```
┌──────────────────────────────────────────────────────────────────┐
│                         Datenquellen                             │
│  OSM/Overpass  │  ARPA Piemonte  │  uMap  │  SRTM 90m  │  CUPX  │
└───────┬─────────────────┬─────────────┬──────────────┬──────────┘
        │                 │             │              │
        ▼                 ▼             ▼              ▼
┌──────────────────────────────────────────────────────────┐
│  Schritt 1: Download  (download_data.py)                 │
│  → data/osm/*.geojson          → data/dem/*.tif          │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│  Schritt 2: Basemap  (generate_basemap.py)               │
│  → ps_{region}_{system}_basemap.webp      (opak)         │
│  → ps_{region}_{system}_basemap_rot.webp  (opak, S-oben) │
└────────────────────────┬─────────────────────────────────┘
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
┌─────────────────────┐   ┌──────────────────────┐
│  Schritt 3a         │   │  Schritt 3b           │
│  generate_          │   │  generate_poi_        │
│  cards.py           │   │  cards.py             │
│  (Polygon-Decks)    │   │  (POI-Decks)          │
│  → partition.webp   │   │  → all_pois.webp      │
│  → context.webp     │   │  → context.webp       │
│  → group_*_front    │   │  → poi_*_highlight    │
│  → group_*_back     │   │  → poi_*_back         │
└──────────┬──────────┘   └──────────┬────────────┘
           └──────────────┬──────────┘
                          ▼
┌──────────────────────────────────────────────────────────┐
│  Schritt 4: Deck bauen  (build_deck.py)                  │
│  → output/{region}_{system}/anki_{region}_{system}.apkg  │
└──────────────────────────────────────────────────────────┘
```
