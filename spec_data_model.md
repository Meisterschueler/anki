# Peak Soaring Anki — Datenmodell

> Dieses Dokument ist Teil der [Ideal Specification](ideal_specification.md).

---

## 4. Datenmodell

### Kernobjekte

```python
@dataclass
class Region:
    """Geografischer Bereich (Bounding Box, Projektion, Städteliste)."""
    name: str                    # "ostalpen" | "westalpen"
    bbox_west: float
    bbox_east: float
    bbox_south: float
    bbox_north: float
    projection_params: dict      # für cartopy (central_longitude, standard_parallels …)
    figure_width: float          # Seitenverhältnis der Ausgabebilder in Zoll
    figure_height: float
    cities: list[City]           # Städtebeschriftung (siehe City-Dataclass unten)
    # Pfade zu gemeinsamen Geodaten
    osm_rivers_geojson: Path
    osm_lakes_geojson: Path
    osm_valleys_geojson: Path
    osm_borders_geojson: Path
    dem_tif: Path


@dataclass
class Gebirgsgruppe:
    """Eine Gebirgsgruppe in einem Klassifikationssystem."""
    group_id: str           # "3b", "SZ.15", "T01" …
    name: str               # Deutscher Name
    hauptgruppe: str        # Übergeordnete Hauptgruppe (für Farbe)
    hoechster_gipfel: str   # Höchster Gipfel und Höhe als Anzeigetext
    osm_ref: str            # Wert des OSM-Tags zum Polygon-Matching
    tags: list[str] = field(default_factory=list)  # Anki-Tags (z.B. ["starter", "prominent"])
    memo: str = ""          # Optionaler Mnemotechnik-Hinweis für die Rückseite


@dataclass
class POI:
    """Ein Punkt auf der Karte (Gipfel, Pass, See, Ort, Landewiese …)."""
    poi_id: str             # "peak_01", "os_03" …
    name: str
    category: str           # "peak" | "pass" | "valley" | "town" | "lake"
                            # | "landefeld_a" | "landefeld_b" | "airstrip"
    lat, lon: float         # WGS84
    elevation: int | None   # Meter
    subtitle: str | None    # Zusatzinfo (Klassifikation, Fläche …)
    heading: int | None     # Pistenkurs in Grad (nur für Landewiesen/Flugplätze)
    tags: list[str]         # Anki-Tags
    pics: list[str]         # Eingebettete Bildnamen (nur Landewiesen)


@dataclass
class Classification:
    """Ein Klassifikationssystem für Polygon-Karten (AVE 84, SOIUSA, Täler …)."""
    name: str               # "ave84" | "soiusa_sz" | "taler" …
    title: str
    groups: list[Gebirgsgruppe]
    hauptgruppen: list[str]
    render_config: RenderConfig             # Darstellungsparameter (ausgelagert)
    osm_tag: str            # z.B. "ref:aveo" | "ref:soiusa" | "name"
    osm_fallback_ids: dict  # osm_ref → OSM-ID (Relation oder Way), als Fallback

    @classmethod
    def create(
        cls,
        *,
        groups: list["Gebirgsgruppe"],
        render_config: "RenderConfig | None" = None,
        osm_fallback_ids: "dict | None" = None,
        **kwargs: Any,
    ) -> "Classification":
        """Factory; ermöglicht Override einzelner Felder beim Testen/Rendern.
        Alternativ: dataclasses.replace(CLASSIFICATION, groups=...) verwenden."""
        if render_config is not None:
            kwargs["render_config"] = render_config
        if osm_fallback_ids is not None:
            kwargs["osm_fallback_ids"] = osm_fallback_ids
        return cls(groups=groups, **kwargs)


@dataclass
class RenderConfig:
    """Darstellungsparameter — entkoppelt vom Datenmodell (A5).

    Felder mit None-Default erben den globalen Wert aus config.py.
    Felder mit explizitem Wert überschreiben den globalen Default
    für diese Klassifikation.
    """
    colors: dict[str, dict]           # hauptgruppe → {fill, border, label}
    polygon_alpha: float | None = None  # Default: config.POLYGON_ALPHA (0.55)
    label_font_size: float | None = None  # Default: config.LABEL_FONT_SIZE (8.0)


@dataclass(frozen=True)
class City:
    """Städtebeschriftung auf der Karte."""
    name: str
    lon: float
    lat: float
    dx: float = 0.0    # Textversatz in Grad (horizontal)
    dy: float = 0.0    # Textversatz in Grad (vertikal)


@dataclass
class SubdeckSpec:
    """Typisierte Subdeck-Konfiguration (ersetzt positionale Tupel, A3)."""
    system: str
    label: str
    card_type: str = "default"
    # Gültige Werte: "default" | "neighbor" | "blind_orientation"


@dataclass
class POIClassification:
    """Ein Klassifikationssystem für POI-Karten."""
    name: str
    title: str
    pois: list[POI]
    category_style: dict    # category → {marker, color, size, label}
```

### Deck-Typen

```
BaseDeck (abstrakt)
├── Deck          → Region × Classification  (Polygon-Karten)
└── POIDeck       → Region × POIClassification  (POI-Karten)
```

Beide Deck-Typen verwenden **explizite Properties** statt `__getattr__`-Delegation,
da `__getattr__` von `mypy` nicht prüfbar ist und IDE-Autovervollständigung
unterbindet. Empfohlen: `deck.region.bbox_west` statt magischem `deck.bbox_west`;
oder ein `DeckMixin` mit expliziten Property-Definitionen für häufig verwendete
Attribute (`bbox_west`, `groups`, `pois`, usw.).

### Deck-Registry

Die Registry ist in `registry.py` definiert (nicht mehr in `deck.py` — siehe [Modulaufteilung](spec_pipeline.md#8-dateistruktur)):

```python
VALID_COMBINATIONS = {
    "ostalpen":  ["ave84", "soiusa_sz", "soiusa_sts", "pois", "landewiesen",
                  "taler", "gipfel", "paesse", "seen"],
    "westalpen": ["soiusa_sz", "soiusa_sts", "pois", "landewiesen"],
}
```

Neue Regionen oder Klassifikationssysteme werden ausschließlich durch Hinzufügen
eines Eintrags in die Registry und einer neuen Klassifikations-Datei ergänzt.
