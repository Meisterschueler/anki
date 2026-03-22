# Peak Soaring Anki — Decks & Inhalte

> Dieses Dokument ist Teil der [Ideal Specification](ideal_specification.md).

---

## 5. Decks & Inhalte

### Deck-Übersicht

| # | Datei | Karten | Subdecks |
|---|---|---|---|
| 1 | `ostalpen_ave84/anki_ostalpen_ave84.apkg` | ~312 | A–G |
| 2 | `ostalpen_soiusa/anki_ostalpen_soiusa.apkg` | 98 | A–B |
| 3 | `ostalpen_pois/anki_ostalpen_pois.apkg` | ~209 | A–J |
| 4 | `westalpen_soiusa/anki_westalpen_soiusa.apkg` | 69 | A–B |
| 5 | `westalpen_pois/anki_westalpen_pois.apkg` | ~209 | A–I |

### Deck 1: Ostalpen AVE 84 (`ostalpen_ave84`)

Kombiniertes Deck aus 7 Subdecks. Alle Subdecks teilen die gleiche Basemap und den
gleichen Context-Layer. Der ▦-Einteilung-Button zeigt in allen Subdecks die
AVE-84-Farbpartition.

| Subdeck | Typ | Karten | Klassifikation |
|---|---|---|---|
| A Einzugsgebiete | Polygon | 10 | ~10 Flusssysteme (HydroBASINS), nach Mündungsgebiet gefärbt |
| B Gebirgsgruppen | Polygon | 75 | AVE 84 (Alpenvereinseinteilung 1984) |
| C Gipfel | POI | 21 | Kuratierte Hauptgipfel (Ostalpen) |
| D Täler | Polygon | 20 | 20 Haupttäler, nach Einzugsgebiet gefärbt |
| E Pässe | POI | 20 | Wichtigste Alpenübergänge |
| F Seen | POI | 16 | Bedeutende Seen der Ostalpen |
| G Gebirgsgruppen visualisieren | Nachbar | 75 | AVE 84 (Nachbarkarten-Modus) |

**Subdeck A — Einzugsgebiete (neu):**

10 Polygon-Karten der großen Flusssysteme der Ostalpen. Die Polygone stammen aus
HydroBASINS (HydroSHEDS, Level 8) und bilden eine lückenlose Partition der Karte —
jeder Punkt gehört zu genau einem Flusssystem. Aufbereitung durch
`tools/prepare_einzugsgebiete.py`.

| Mündungsgebiet | Farbe | Flusssysteme |
|---|---|---|
| Nordsee | `#2E86C1` | Rhein |
| Schwarzes Meer | `#FF9500` | Inn, Salzach/Saalach, Traun, Enns, Mur, Drau |
| Adriatisches Meer | `#DC3545` | Etsch, Brenta/Sarca, Tagliamento/Piave |

> **Lernziel Subdeck A:** Der Lernende kann die 3 Entwässerungsrichtungen der
> Ostalpen (Nordsee, Schwarzes Meer, Adria) benennen und die ~10 großen
> Flusssysteme auf der Karte lokalisieren. Fundament für die 20 Einzeltäler
> in Subdeck D.

**Starter-Set (C1):** In Subdeck B sind 20 besonders markante Gruppen mit dem Tag
`ave84::starter` markiert (hohe touristische Bekanntheit, klare Silhouette, zentrale
Lage). Anki-Empfehlung: diese Karten zuerst lernen, bevor die restlichen 55 Gruppen
hinzugefügt werden. Empfohlene Anki-Einstellung: neue Karten „in Reihenfolge".

Die 20 Starter-Gruppen:
Karwendel, Wettersteingebirge, Zugspitzgruppe, Lechtaler Alpen, Allgäuer Alpen,
Berchtesgadener Alpen, Hohe Tauern (Glocknergruppe), Stubaier Alpen, Ötztaler Alpen,
Brennergebirge/Tuxer Alpen, Dachstein, Gesäuseberge, Kaisergebirge, Nordtiroler
Kalkalpen-Kern, Karnische Alpen, Dolomiten-Kern (Cadorische Alpen), Ortlergruppe,
Berninakette, Adamello-Presanella, Silvretta.

*(Die genaue Auswahl wird in `classifications/ave84.py` per `tags=["starter"]`
festgelegt und kann dort jederzeit angepasst werden.)*

**Anki-Tags (C2):** Jede Gebirgsgruppe erhält systematische Tags zur Filterung:

| Tag | Bedeutung |
|---|---|
| `ave84::starter` | Empfohlen für Einsteiger (20 Gruppen) |
| `ave84::prominent` | Bekannte, touristische Gruppen |
| `region::nordtirol` | Geografische Teilregion (Beispiel) |
| `drainage::inn` | Einzugsgebiet (nur Täler-Deck) |
| `height::4000plus` | Mindestens ein 4000-m-Gipfel |

**AVE 84 — Hauptgruppen:**

| Hauptgruppe | Farbe | Gruppen |
|---|---|---|
| Nördliche Ostalpen | `#4A90D9` | 27 (Nr. 1–24) |
| Zentrale Ostalpen | `#FF9500` | 27 (Nr. 25–47) |
| Südliche Ostalpen | `#27AE60` | 15 (Nr. 48–60) |
| Westliche Ostalpen | `#E74C3C` | 6 (Nr. 63–68) |

**Täler — Einzugsgebiete:**

| Einzugsgebiet | Farbe | Täler |
|---|---|---|
| Inn-System | `#2E86C1` | Inntal, Oberinntal, Unterinntal, Lechtal, Ötztal, Zillertal, Stubaital |
| Salzach-System | `#28A745` | Salzachtal, Gasteinertal |
| Enns/Mur-System | `#FF9500` | Ennstal, Murtal |
| Drau-System | `#8E44AD` | Drautal, Mölltal, Gailtal |
| Etsch/Adria-System | `#DC3545` | Wipptal, Eisacktal, Pustertal, Vinschgau |
| Rhein-System | `#6C757D` | Alpenrheintal, Montafon |

**Nachbarn-Modus (Subdeck G):** Die Rückseite zeigt alle direkt angrenzenden Gruppen
gleichzeitig hellgrau hervorgehoben (statt nur der einzelnen abgefragten Gruppe).

> **Lernziel Subdeck G (C8):** Der Lernende kann für eine hervorgehobene
> Gebirgsgruppe alle angrenzenden Gruppen nennen, ohne auf die Partition-Karte zu
> schauen. Zielkompetenz: mentale Karte des AVE-84-Rasters als Navigationshilfe auf
> Streckenflügen. Die Rückseite listet die Nachbargruppen alphabetisch geordnet
> auf, damit der Lernende seine Antwort präzise vergleichen kann.

### Deck 2: Ostalpen SOIUSA (`ostalpen_soiusa`)

| Subdeck | Karten | System |
|---|---|---|
| A Gliederung | 22 | SOIUSA Sezioni (SZ 15–36) |
| B Details | 76 | SOIUSA Sottosezioni (STS) |

Datenquelle: ARPA Piemonte FeatureServer. Die Rückseite der Sottosezioni-Karten zeigt
zusätzlich das übergeordnete Sezione-Polygon als transparenten Kontext.

### Deck 3: Ostalpen Marken (`ostalpen_pois`)

POIs aus *Peak Soaring* (Bachmaier) + streckenflug.at-Landewiesen.

| Subdeck | Typ | Karten | Zoom |
|---|---|---|---|
| A Königsdorf | Sub-Region | variiert | Bbox 10.8–12.3°O / 47.23–47.78°N |
| B Innsbruck | Sub-Region | variiert | Bbox 10.8–11.9°O / 46.9–47.5°N |
| C Gipfel | Kategorie | ~82 | Gesamtkarte |
| D Pässe | Kategorie | ~59 | Gesamtkarte |
| E Orte | Kategorie | ~24 | Gesamtkarte |
| F Täler | Kategorie | ~43 | Gesamtkarte |
| G Seen | Kategorie | ~7 | Gesamtkarte |
| H Landefelder Kat A | Kategorie | ~327 | Gesamtkarte |
| I Landefelder Kat B | Kategorie | ~288 | Gesamtkarte |
| J Flugplätze | Kategorie | ~65 | Gesamtkarte |

Sub-Region-Karten enthalten ein **Thumbnail** (Übersichtskarte mit rotem Rechteck).
POIs innerhalb 10 % des Randes einer Sub-Region-Bbox werden ausschließlich im
Subdeck dieser Sub-Region geführt (nicht im Hauptdeck der Gesamtkarte).

### Decks 4 & 5: Westalpen

Analoge Struktur für `westalpen_soiusa` (69 Karten, A–B) und `westalpen_pois`
(A Puimoisson + B–I Kategorien). Gleiche Pipeline, andere Region-Bbox und Städteliste.
