# Peak Soaring Anki — Bildqualität & Tests

> Dieses Dokument ist Teil der [Ideal Specification](ideal_specification.md).

---

## 10. Anforderungen an Bildqualität

### Basemap

- **Format:** WebP (opak, Lossy Quality 90)
- **Auflösung:** max. 7680 × 4320 px (8K UHD) bei 480 DPI
- **Projektion:** PlateCarree (WGS 84) — kein Regridding nötig
- **DEM-Quelle:** SRTM 90m, Höhen gekappt bei 4200 m (Schutz vor Überbelichtung)

### Overlays

- **Format:** WebP (transparent, Lossless)
- **Auflösung:** identisch zur Basemap des gleichen Decks (wichtig!)
- Abweichende Dimensionen werden durch den Test `test_image_dimensions.py` erkannt

### Dateinamen-Schema

```
ps_{region}_{system}_{layer}.webp
```

Beispiele:

```
ps_ostalpen_ave84_basemap.webp
ps_ostalpen_ave84_basemap_rot.webp
ps_ostalpen_ave84_basemap_blind.webp
ps_ostalpen_ave84_partition.webp
ps_ostalpen_ave84_context.webp
ps_ostalpen_ave84_group_3b_front.webp
ps_ostalpen_ave84_group_3b_back.webp
ps_ostalpen_ave84_group_3b_neighbors.webp
ps_ostalpen_gipfel_poi_og_01_highlight.webp
ps_ostalpen_gipfel_poi_og_01_back.webp
ps_ostalpen_pois_all_pois.webp
ps_ostalpen_pois_thumb_koenigsdorf.webp
```

Sonderzeichen in IDs (z.B. `/` in `05/1`) werden durch `_` ersetzt.

### Deck-Manifest

Pro gebautem Deck wird eine `manifest.json` im Output-Verzeichnis erzeugt (B9):

```json
// output/ostalpen_ave84/manifest.json
{
  "generated_at": "2026-03-19T10:23:00Z",
  "deck_version": "2.0.0",
  "files": {
    "ps_ostalpen_ave84_basemap.webp": {
      "sha256": "abc123...",
      "deps_hash": "def456..."
    }
  }
}
```

Das Manifest ersetzt individuelle `*.deps.json`-Sidecar-Dateien. `test_deck_media.py`
validiert das Manifest statt Sidecars zu scannen.

---

## 11. Tests

Die Test-Suite liegt unter `tests/` und wird mit pytest ausgeführt.

### Zweigeteilte Architektur (B6)

```
tests/
  unit/                     # Keine Pre-build-Outputs erforderlich; läuft in CI
    test_config.py           # VALID_COMBINATIONS Konsistenz, Konstanten
    test_filename_schema.py  # Dateinamen-Generierungsfunktionen
    test_registry.py         # get_deck(), get_region() mit Mock-Daten
    test_geometry_helpers.py # _osm_json_to_geojson, make_valid()-Logik
  integration/              # Setzt gerenderte Ausgaben voraus
    conftest.py              # Fixtures mit skip-if-no-output
    test_deck_media.py
    test_deck_size.py
    test_image_dimensions.py
```

Unit-Tests brauchen keine Geodaten und laufen in < 5 Sekunden in jedem
leeren CI-Job. Integration-Tests werden lokal nach vollständigem Build ausgeführt.

### Testfälle (Integration)

| Datei | Was wird geprüft |
|---|---|
| `test_image_dimensions.py` | Alle Layer-Bilder eines Decks haben identische Dimensionen; Basemap-Layer-PNGs sind gleich groß; lakes.png und rivers.png enthalten nicht-transparente Pixel |
| `test_deck_media.py` | Alle in Anki-Notizen referenzierten `src=`-Bilder sind im `.apkg`-Archiv enthalten |
| `test_deck_size.py` | Jedes `.apkg` enthält die erwartete Anzahl an Notizen |

### Fixtures (`conftest.py`)

- `deck` — parametrisiert über alle Einträge in `VALID_COMBINATIONS`
- `image_dir` — Pfad zum `output/{region}_{system}/images/`-Verzeichnis
- `apkg_path` — Pfad zur `.apkg`-Datei

### CI-Hinweis

Unit-Tests (`tests/unit/`) können ohne Geodaten oder gerenderte Bilder ausgeführt
werden und sind für den Einsatz in einer schlanken CI-Pipeline geeignet.
Integrations-Tests (`tests/integration/`) setzen voraus, dass Schritte 1–4 ausgeführt
wurden; sie werden nur lokal nach dem vollständigen Build ausgeführt.

**Empfohlene CI-Konfiguration** (z.B. GitHub Actions, bei jedem Push):

```yaml
# .github/workflows/ci.yml
on: [push, pull_request]
jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -e ".[dev]"
      - run: mypy --strict .
      - run: ruff check .
      - run: pytest tests/unit/
```

Integrations-Tests laufen manuell (lokaler Build erforderlich), nicht in CI.
