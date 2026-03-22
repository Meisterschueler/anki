# Peak Soaring Anki — Setup, Datenquellen & Lernpfad

> Dieses Dokument ist Teil der [Ideal Specification](ideal_specification.md).

---

## 12. Datenquellen & Lizenzen

| Quelle | Verwendung | Lizenz |
|---|---|---|
| **OpenStreetMap / Overpass API** | Polygon-Grenzen (AVE 84, Täler), Flüsse, Seen, Täler, Staatsgrenzen | ODbL 1.0 — © OpenStreetMap Contributors |
| **ARPA Piemonte FeatureServer** | SOIUSA-Polygone (Sezioni + Sottosezioni) | Frei nutzbar, Quellenangabe Pflicht: „Massimo Accorsi, Venezia" |
| **uMap #954288** | SOIUSA Westalpen-Sezioni | Abgeleitet von OSM-Daten |
| **CGIAR-CSI SRTM 90m** | Digitales Höhenmodell | CC BY 4.0 |
| **streckenflug.at CUPX** | Außenlandewiesenkatalog mit Fotos | Nutzung für private/sportliche Zwecke |
| **Nominatim (OpenStreetMap)** | OSM-IDs nachschlagen (Einmalig) | Nutzungsbestimmungen: max. 1 req/s |

**Pflicht:** Quellenangabe für OSM (`© OpenStreetMap Contributors`) und ARPA Piemonte
in der Anki-Deck-Beschreibung.

---

## 13. Setup & Workflow

### Erstinstallation

```bash
git clone <repo>
cd anki
python -m venv .venv

# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Abhängigkeiten aus dem Lockfile installieren (reproduzierbar):
pip install -r requirements.txt
# Alternativ mit uv (schneller):
# uv sync
```

Für Entwickler zusätzlich:

```bash
pip install -e ".[dev]"   # inkl. mypy, ruff, pytest
```

### Vollständiger Build

```bash
# 1. Geodaten herunterladen (einmalig, dauert mehrere Minuten)
python scripts/download_data.py --region ostalpen
python scripts/download_data.py --region westalpen
python tools/download_soiusa_arpa.py   # Einmalig: SOIUSA Ostalpen (ARPA Piemonte)
python tools/download_soiusa_umap.py   # Einmalig: SOIUSA Westalpen (uMap)
python tools/prepare_einzugsgebiete.py  # Einmalig: HydroBASINS → Einzugsgebiet-GeoJSON

# 2–4. Für jedes gewünschte Deck (Schritte 2–4 laufen automatisch wenn nötig)
python scripts/build_deck.py --region ostalpen --system ave84
python scripts/build_deck.py --region ostalpen --system soiusa_sz
python scripts/build_deck.py --region ostalpen --system pois
python scripts/build_deck.py --region westalpen --system soiusa_sz
python scripts/build_deck.py --region westalpen --system pois

# 5. Tests
python scripts/run_tests.py
```

### Tipps für den Alltag

```bash
# Nur ein einzelnes Deck neu rendern (ohne Download)
python scripts/generate_cards.py --region ostalpen --system ave84 --force

# Nur einzelne Gruppen neu rendern
python scripts/generate_cards.py --region ostalpen --system ave84 --ids 3b,40,52

# Nur den Deck-Build wiederholen (ohne Re-Rendering)
python scripts/build_deck.py --region ostalpen --system ave84

# Tests: nur Unit-Tests (ohne gerenderte Ausgaben)
pytest tests/unit/

# Tests: vollständige Integration (nach Build)
python scripts/run_tests.py

# Statische Typprüfung
mypy --strict .
```

### Laufzeiten (Richtwerte, Desktop-PC)

| Schritt | Ostalpen AVE 84 | Kommentar |
|---|---|---|
| Download | 5–20 min | Abhängig von Overpass-Last; bei Wiederholung aus HTTP-Cache <1 min |
| Basemap | ~2 min | Einmalig pro Deck |
| Card-Rendering (75 Gruppen) | ~2–3 min | Parallel (ProcessPoolExecutor, 4 Kerne) |
| .apkg bauen | ~1 min | |
| Tests (Unit) | <5 s | Ohne gerenderte Ausgaben |
| Tests (Integration) | <1 min | |

---

## 14. Empfohlener Lernpfad

### Reihenfolge der Decks

Die Decks sind aufeinander aufgebaut. Große Einheiten zuerst, Details danach:

**Kerndeck (AVE 84 Ostalpen):**
```
1. AVE 84 — A Gebirgsgruppen (Starter-Set, 20 Karten)
2. AVE 84 — A Gebirgsgruppen (vollständig, 55 Karten nachziehen)
3. AVE 84 — C Täler
4. AVE 84 — D Pässe
5. AVE 84 — B Gipfel
6. AVE 84 — E Seen
7. AVE 84 — F Gebirgsgruppen visualisieren (Nachbarn)
8. AVE 84 — G Orientierung (ohne Kompassnadel)
```

**Parallele Decks (je nach Bedarf):**
```
SOIUSA (Ostalpen): nachdem AVE 84 geläufig ist — verfeinert Detailkenntnis
SOIUSA (Westalpen): für Piloten mit regelmäßigen Westalpen-Flügen
Peak Soaring POIs: C–J (spezifische Gebiete wie Königsdorf / Innsbruck zuerst)
Landewiesen: nur bei aktivem Streckenflugtraining sinnvoll
```

### Phasenplan

| Phase | Wochen | Inhalt | Neue Karten/Tag |
|---|---|---|---|
| Einstieg | 1–4 | A Gebirgsgruppen — Starter-Set (20 Karten) | 5 |
| Aufbau | 5–10 | A Gebirgsgruppen — vollständig (55 Karten) | 10 |
| Erweiterung | 11–15 | C Täler + D Pässe | 8 |
| Vertiefung | 16–20 | B Gipfel + E Seen | 8 |
| Vernetzung | ab Woche 21 | F Nachbarn + G Orientierung | 5 |

### Anki-Einstellungen

- **Neue Karten:** "in Reihenfolge" (nicht zufällig) — gibt Kontrolle über den Einstiegspunkt
- **Neue Karten pro Tag:** 5–15 je nach Intensität
- **Filterdecks für Kurzübungen** (Anki-Suchfeld):
  - Einsteiger: `tag:ave84::starter`
  - Tirol-Fokus: `tag:region::nordtirol`
  - Hochalpine Gruppen: `tag:height::4000plus`

### Nutzungshinweis für den Tipp-Button

Der 💡-Tipp-Button auf POI-Karten zeigt die übergeordnete Gebirgsgruppe. Empfehlung:
in der ersten Lernphase großzügig nutzen; in der Vertiefungsphase nur noch bei
echtem Nicht-Wissen einsetzen. Karten mit Tipp als "Nochmal" werten.

### Geräteübergreifende Synchronisation

Der `localStorage`-Zustand (Button-Einstellungen) wird **nicht** über AnkiWeb auf
andere Geräte übertragen. Jedes Gerät merkt sich die zuletzt gewählten Einstellungen
unabhängig.
