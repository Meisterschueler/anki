"""
04_build_deck.py — Build Anki .apkg deck
=========================================
Generates a ready-to-import .apkg package with CSS-layered WebP maps
(opaque basemap + transparent overlays).

Usage:
    python scripts/04_build_deck.py --region ostalpen
    python scripts/04_build_deck.py --region westalpen

Images are auto-generated on first run if not already cached.
To regenerate manually:
    python scripts/03_generate_cards.py --region <r>
"""

import argparse
import hashlib
import sys
from datetime import date
from pathlib import Path

import genanki

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))
import deck as D
from deck import Deck, POIDeck


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _ensure_images(d: Deck) -> None:
    """Auto-generate basemap + overlays if they don't exist yet."""
    from importlib import import_module
    if isinstance(d, POIDeck):
        mod = import_module("03b_generate_poi_cards")
    else:
        mod = import_module("03_generate_cards")
    mod._generate_basemap(d, force=False)
    mod.generate_all(d, force=False)


# ─── APKG Export ─────────────────────────────────────────────────────────────

# CSS for Anki cards — flat structure, all <img> are direct children of .card-map
_BASE_CSS = """\
.card {
    font-family: "Segoe UI", Arial, Helvetica, sans-serif;
    font-size: 16px;
    text-align: center;
    color: #222;
    background: #fff;
}
.card-map {
    position: relative;
    display: inline-block;
    line-height: 0;
    margin: 8px 0;
}
.card-map img {
    max-width: 100%;
}
.card-map img.basemap {
    display: block;
}
.card-map img.overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
}
.answer-info {
    margin: 10px 0;
    font-size: 18px;
}
.answer-info .name {
    font-weight: bold;
    font-size: 20px;
}
.hint-btn {
    position: absolute;
    top: 8px;
    left: 8px;
    padding: 5px 12px;
    font-size: 12px;
    color: #2E86C1;
    background: rgba(235,245,251,0.9);
    border: 1px solid #AED6F1;
    border-radius: 5px;
    cursor: pointer;
    z-index: 5;
    line-height: normal;
}
.hint-btn:hover {
    background: rgba(212,230,241,0.95);
}
.compass-btn {
    position: absolute;
    top: 10px;
    right: 10px;
    width: 44px;
    height: 44px;
    border-radius: 50%;
    background: rgba(255,255,255,0.78);
    border: 1px solid #aaa;
    cursor: pointer;
    z-index: 5;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: transform 0.3s ease;
    box-shadow: 0 1px 3px rgba(0,0,0,0.25);
    line-height: 0;
    padding: 0;
}
.compass-btn:hover {
    background: rgba(255,255,255,0.95);
}
.compass-btn svg {
    width: 34px;
    height: 38px;
}
"""

_APKG_CSS = _BASE_CSS + """\
.card-map img.basemap-rot {
    display: none;
}
.card-map img.partition,
.card-map img.context {
    display: none;
}
.answer-info .gipfel {
    color: #555;
    font-size: 15px;
}
"""

# Compact JS for the compass onclick handler (shared across group + POI).
# Toggles between 0° (north-up) and 180° (south-up).
# Basemap is stored north-up; basemap-rot has azimuth 135° (also north-up).
# CSS rotate(180deg) is applied to active basemap + all overlays.
_COMPASS_ONCLICK = (
    "var c=this.parentNode;"
    "var bm=c.querySelector('img.basemap');"
    "var br=c.querySelector('img.basemap-rot');"
    "var r=bm&&bm.style.display==='none';"
    "if(bm)bm.style.display=r?'':'none';"
    "if(br)br.style.display=r?'none':'block';"
    "var ang=r?'':'rotate(180deg)';"
    "if(br)br.style.transform=r?'':'rotate(180deg)';"
    "c.querySelectorAll('img.overlay,img.allpois,img.partition,img.context')"
    ".forEach(function(i){i.style.transform=ang;});"
    "this.style.transform=ang;"
    "sessionStorage.setItem('ps_rot',r?'0':'1');"
)

# Compact JS for session restore — group decks (Einteilung + Kontext + rotation).
_SESSION_RESTORE_GROUP = (
    "(function(){"
    "var c=document.querySelector('.card-map');"
    "if(!c)return;"
    "var bs=c.querySelectorAll('.hint-btn');"
    "if(sessionStorage.getItem('ps_et')==='1'){"
    "var p=c.querySelector('img.partition');"
    "if(p)p.style.display='block';"
    "if(bs[0])bs[0].textContent='\\u2716 Einteilung';}"
    "if(sessionStorage.getItem('ps_ctx')==='1'){"
    "var x=c.querySelector('img.context');"
    "if(x)x.style.display='block';"
    "if(bs[1])bs[1].textContent='\\u2716 Kontext';}"
    "if(sessionStorage.getItem('ps_rot')==='1'){"
    "var bm=c.querySelector('img.basemap');"
    "var br=c.querySelector('img.basemap-rot');"
    "if(bm)bm.style.display='none';"
    "if(br){br.style.display='block';br.style.transform='rotate(180deg)';}"
    "c.querySelectorAll('img.overlay,img.partition,img.context')"
    ".forEach(function(i){i.style.transform='rotate(180deg)';});"
    "var cb=c.querySelector('.compass-btn');"
    "if(cb)cb.style.transform='rotate(180deg)';}"
    "})();"
)

# Compact JS for session restore — POI decks (POIs + Kontext + rotation).
_SESSION_RESTORE_POI = (
    "(function(){"
    "var c=document.querySelector('.card-map');"
    "if(!c)return;"
    "var bs=c.querySelectorAll('.hint-btn');"
    "if(sessionStorage.getItem('ps_pois')==='1'){"
    "var a=c.querySelector('img.allpois');"
    "if(a)a.style.display='block';"
    "if(bs[0])bs[0].textContent='\\u2716 POIs';}"
    "if(sessionStorage.getItem('ps_ctx')==='1'){"
    "var x=c.querySelector('img.context');"
    "if(x)x.style.display='block';"
    "if(bs[1])bs[1].textContent='\\u2716 Kontext';}"
    "if(sessionStorage.getItem('ps_rot')==='1'){"
    "var bm=c.querySelector('img.basemap');"
    "var br=c.querySelector('img.basemap-rot');"
    "if(bm)bm.style.display='none';"
    "if(br){br.style.display='block';br.style.transform='rotate(180deg)';}"
    "c.querySelectorAll('img.overlay,img.allpois,img.context')"
    ".forEach(function(i){i.style.transform='rotate(180deg)';});"
    "var cb=c.querySelector('.compass-btn');"
    "if(cb)cb.style.transform='rotate(180deg)';}"
    "})();"
)

_NORDPFEIL_SVG = '<svg viewBox="0 0 40 48"><polygon points="20,2 8,28 20,22" fill="none" stroke="#333" stroke-width="1.8" stroke-linejoin="round"/><polygon points="20,2 32,28 20,22" fill="#333" stroke="#333" stroke-width="1.8" stroke-linejoin="round"/><text x="20" y="44" text-anchor="middle" font-size="14" font-weight="bold" fill="#333" font-family="sans-serif">N</text></svg>'

_TMPL_FRONT = (
    '<div class="card-map">\n'
    '{{Basemap}}\n'
    '{{BasemapRot}}\n'
    '{{Partition}}\n'
    '{{Context}}\n'
    '{{FrontOverlay}}\n'
    '<button class="hint-btn" onclick="var i=this.parentNode.querySelector(\'img.partition\');var v=i.style.display!==\'block\';i.style.display=v?\'block\':\'none\';this.textContent=v?\'\\u2716 Einteilung\':\'\\u25a6 Einteilung\';sessionStorage.setItem(\'ps_et\',v?\'1\':\'0\');">&#9638; Einteilung</button>\n'
    '<button class="hint-btn" style="left:110px;" onclick="var i=this.parentNode.querySelector(\'img.context\');var v=i.style.display!==\'block\';i.style.display=v?\'block\':\'none\';this.textContent=v?\'\\u2716 Kontext\':\'\\u25a6 Kontext\';sessionStorage.setItem(\'ps_ctx\',v?\'1\':\'0\');">&#9638; Kontext</button>\n'
    '<div class="compass-btn" onclick="' + _COMPASS_ONCLICK + '">' + _NORDPFEIL_SVG + '</div>\n'
    '</div>\n'
    '<script>' + _SESSION_RESTORE_GROUP + '</script>\n'
)

_TMPL_BACK = (
    '<div class="answer-info">\n'
    '<div class="name">{{Name}} ({{Group_ID}})</div>\n'
    '<div class="gipfel">{{Hoechster_Gipfel}}</div>\n'
    '</div>\n'
    '<hr>\n'
    '<div class="card-map">\n'
    '{{Basemap}}\n'
    '{{BasemapRot}}\n'
    '{{Partition}}\n'
    '{{Context}}\n'
    '{{BackOverlay}}\n'
    '<button class="hint-btn" onclick="var i=this.parentNode.querySelector(\'img.partition\');var v=i.style.display!==\'block\';i.style.display=v?\'block\':\'none\';this.textContent=v?\'\\u2716 Einteilung\':\'\\u25a6 Einteilung\';sessionStorage.setItem(\'ps_et\',v?\'1\':\'0\');">&#9638; Einteilung</button>\n'
    '<button class="hint-btn" style="left:110px;" onclick="var i=this.parentNode.querySelector(\'img.context\');var v=i.style.display!==\'block\';i.style.display=v?\'block\':\'none\';this.textContent=v?\'\\u2716 Kontext\':\'\\u25a6 Kontext\';sessionStorage.setItem(\'ps_ctx\',v?\'1\':\'0\');">&#9638; Kontext</button>\n'
    '<div class="compass-btn" onclick="' + _COMPASS_ONCLICK + '">' + _NORDPFEIL_SVG + '</div>\n'
    '</div>\n'
    '<script>' + _SESSION_RESTORE_GROUP + '</script>\n'
)


# ─── Shared Group model & helpers ─────────────────────────────────────────────

def _group_model(model_id: int, model_name: str) -> genanki.Model:
    """Create the shared Anki model for polygon-group cards (AVE, SOIUSA)."""
    return genanki.Model(
        model_id,
        model_name,
        fields=[
            {"name": "Group_ID"},
            {"name": "Name"},
            {"name": "Hoechster_Gipfel"},
            {"name": "Basemap"},
            {"name": "BasemapRot"},
            {"name": "FrontOverlay"},
            {"name": "BackOverlay"},
            {"name": "Partition"},
            {"name": "Context"},
        ],
        templates=[
            {
                "name": "Gebirgsgruppe",
                "qfmt": _TMPL_FRONT,
                "afmt": _TMPL_BACK,
            },
        ],
        css=_APKG_CSS,
    )


def _collect_group_layers(d: Deck, media_files: list) -> dict:
    """Validate and collect shared layer image paths for a group deck.

    Returns a dict with HTML strings for basemap, partition, and context,
    or None if any required file is missing.
    """
    result = {}

    basemap_file = d.filename_basemap()
    basemap_path = d.output_images_dir / basemap_file
    if not basemap_path.exists():
        print(f"[APKG] ERROR: Basemap not found: {basemap_path}")
        return None
    media_files.append(str(basemap_path))
    result["basemap_html"] = f'<img class="basemap" src="{basemap_file}">'

    basemap_rot_file = d.filename_basemap_rot()
    basemap_rot_path = d.output_images_dir / basemap_rot_file
    if not basemap_rot_path.exists():
        print(f"[APKG] ERROR: Rotated basemap not found: {basemap_rot_path}")
        return None
    media_files.append(str(basemap_rot_path))
    result["basemap_rot_html"] = f'<img class="basemap-rot" src="{basemap_rot_file}">'

    partition_file = d.filename_partition(".webp")
    partition_path = d.output_images_dir / partition_file
    if not partition_path.exists():
        print(f"[APKG] ERROR: Partition not found: {partition_path}")
        return None
    media_files.append(str(partition_path))
    result["partition_html"] = f'<img class="overlay partition" src="{partition_file}">'

    context_file = d.filename_context()
    context_path = d.output_images_dir / context_file
    if not context_path.exists():
        print(f"[APKG] ERROR: Context not found: {context_path}")
        return None
    media_files.append(str(context_path))
    result["context_html"] = f'<img class="overlay context" src="{context_file}">'

    return result


def _build_group_notes(
    d: Deck,
    model: genanki.Model,
    groups: list,
    layers: dict,
    media_files: list,
) -> tuple:
    """Build genanki.Note objects for a list of mountain groups.

    Args:
        d: Deck configuration (provides filenames).
        model: Shared Anki model.
        groups: List of Gebirgsgruppe objects to create notes for.
        layers: Dict from _collect_group_layers (basemap/partition/context HTML).
        media_files: Accumulator list for media file paths.

    Returns:
        (notes, skipped) — list of notes and count of skipped groups.
    """
    notes = []
    skipped = 0

    for group in groups:
        front_file = d.filename_group_front(group.group_id, ".webp")
        back_file = d.filename_group_back(group.group_id, ".webp")
        front_path = d.output_images_dir / front_file
        back_path = d.output_images_dir / back_file

        if not front_path.exists() or not back_path.exists():
            skipped += 1
            print(f"[APKG] WARN: Missing overlay for group "
                  f"{group.group_id} ({group.name})")
            continue

        media_files.append(str(front_path))
        media_files.append(str(back_path))

        note = genanki.Note(
            model=model,
            fields=[
                group.group_id,
                group.name,
                group.hoechster_gipfel,
                layers["basemap_html"],
                layers["basemap_rot_html"],
                f'<img class="overlay" src="{front_file}">',
                f'<img class="overlay" src="{back_file}">',
                layers["partition_html"],
                layers["context_html"],
            ],
        )
        notes.append(note)

    return notes, skipped


# ─── Shared APKG writer ──────────────────────────────────────────────────────

def _write_apkg(
    apkg_path: Path,
    decks,
    media_files: list,
    *,
    label: str = "APKG",
    title: str = "",
) -> None:
    """Write one or more decks to an .apkg file and print a summary.

    Args:
        apkg_path: Output path for the .apkg file.
        decks: A single genanki.Deck or a list of decks (for multi-deck).
        media_files: List of media file paths to include.
        label: Log prefix (e.g. "APKG", "APKG-POI").
        title: Human-readable deck title for the summary line.
    """
    apkg_path.parent.mkdir(parents=True, exist_ok=True)

    is_multi = isinstance(decks, list)
    package = genanki.Package(decks)
    package.media_files = media_files
    package.write_to_file(str(apkg_path))

    if is_multi:
        total_notes = sum(len(dk.notes) for dk in decks)
        n_subdecks = len(decks)
        n_media = len(media_files)
        size_mb = apkg_path.stat().st_size / (1024 * 1024)
        print(f"\n[{label}] {title}")
        print(f"[{label}] {total_notes} notes in {n_subdecks} subdecks, "
              f"{n_media} media files, {size_mb:.1f} MB")
    else:
        n_notes = len(decks.notes)
        n_media = len(media_files)
        size_mb = apkg_path.stat().st_size / (1024 * 1024)
        print(f"\n[{label}] {title}")
        print(f"[{label}] {n_notes} notes, {n_media} media files, {size_mb:.1f} MB")

    print(f"[{label}] -> {apkg_path}")
    print(f"\n  Import in Anki:  File -> Import -> {apkg_path.name}")


# ─── Single group deck ────────────────────────────────────────────────────────

def generate_apkg(d: Deck) -> None:
    """Generate a ready-to-import .apkg file for a single classification."""
    _ensure_images(d)

    region_label = d.region.name.capitalize()
    deck_title = f"Gebirgsgruppen der {region_label}"

    base = f"peak_soaring_{d.name}"
    _MODEL_VER = 5
    model_id = int(hashlib.sha256(f"{base}_model_v{_MODEL_VER}".encode()).hexdigest()[:8], 16)
    deck_id = int(hashlib.sha256(f"{base}_deck".encode()).hexdigest()[:8], 16)

    model = _group_model(model_id, deck_title)
    anki_deck = genanki.Deck(deck_id, deck_title)
    media_files: list[str] = []

    layers = _collect_group_layers(d, media_files)
    if layers is None:
        return

    notes, skipped = _build_group_notes(d, model, d.groups, layers, media_files)
    for n in notes:
        anki_deck.add_note(n)

    if skipped:
        print(f"[APKG] WARNING: {skipped} groups skipped (missing overlays).")
        print("       Run:  python scripts/03_generate_cards.py "
              f"--region {d.region.name} --force")

    _write_apkg(
        d.output_csv_dir / f"{d.anki_csv_name}.apkg",
        anki_deck, media_files,
        label="APKG", title=deck_title,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# COMBINED SUBDECK — merge multiple classification levels into one .apkg
# ═══════════════════════════════════════════════════════════════════════════════

def generate_apkg_combined(region_name: str, merge_key: str) -> None:
    """Build a single .apkg containing multiple subdecks.

    Uses the SUBDECK_MERGE config from deck.py to determine which systems
    to merge and what to name each subdeck.  Media is deduplicated: the
    basemap from the first subdeck is shared across all subdecks.
    """
    merge_entries = D.SUBDECK_MERGE[merge_key]
    sub_decks_cfg = [
        (D.get_deck(region_name, system), label)
        for system, label in merge_entries
    ]

    for d_sub, _ in sub_decks_cfg:
        _ensure_images(d_sub)

    # ── Shared identity ────────────────────────────────────────────────────
    d_primary = sub_decks_cfg[0][0]
    region_label = d_primary.region.name.capitalize()
    parent_title = f"Gebirgsgruppen der {region_label}"

    base = f"peak_soaring_{merge_key}"
    _MODEL_VER = 5
    model_id = int(hashlib.sha256(f"{base}_combined_model_v{_MODEL_VER}".encode()).hexdigest()[:8], 16)
    model = _group_model(model_id, parent_title)

    media_files: list[str] = []
    anki_subdecks: list = []
    total_skipped = 0

    # ── Build each subdeck ───────────────────────────────────────────────
    for d_sub, label in sub_decks_cfg:
        subdeck_title = f"{parent_title}::{label}"
        subdeck_id = int(hashlib.sha256(
            f"{base}_{label}_deck".encode()
        ).hexdigest()[:8], 16)

        anki_deck = genanki.Deck(subdeck_id, subdeck_title)

        layers = _collect_group_layers(d_sub, media_files)
        if layers is None:
            return

        notes, skipped = _build_group_notes(
            d_sub, model, d_sub.groups, layers, media_files,
        )
        for n in notes:
            anki_deck.add_note(n)

        total_skipped += skipped
        print(f"[APKG]   {label}: {len(anki_deck.notes)} notes")
        anki_subdecks.append(anki_deck)

    if total_skipped:
        print(f"[APKG] WARNING: {total_skipped} groups skipped (missing overlays).")

    _write_apkg(
        d_primary.output_csv_dir / f"{d_primary.anki_csv_name}.apkg",
        anki_subdecks, media_files,
        label="APKG", title=parent_title,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# POI DECK — APKG Export
# ═══════════════════════════════════════════════════════════════════════════════

_POI_APKG_CSS = _BASE_CSS + """\
.card-map img.basemap-rot {
    display: none;
}
.card-map img.allpois,
.card-map img.context {
    display: none;
}
.card-map img.thumbnail {
    position: absolute;
    bottom: 8px;
    right: 8px;
    width: 18%;
    min-width: 80px;
    height: auto;
    border: 2px solid #666;
    border-radius: 4px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.3);
    z-index: 10;
    opacity: 0.92;
}
.answer-info .detail {
    color: #555;
    font-size: 15px;
}
.cupx-pics {
    position: relative;
    display: block;
    line-height: normal;
    margin: 8px 0 0 0;
    text-align: center;
}
.cupx-pics img {
    position: relative;
    display: block;
    width: 100%;
    height: auto;
    margin: 6px 0;
    border-radius: 4px;
    border: 1px solid #ddd;
}
.cupx-pics .pic-label {
    font-size: 11px;
    color: #888;
    margin-bottom: 4px;
}
"""

# Template: "Welcher Gipfel/Pass/... ist das?"  (identify a highlighted POI)
# {{#Thumbnail}}…{{/Thumbnail}} conditionally renders the overview thumbnail
# only for sub-region decks (field is empty for category decks).
_POI_TMPL_IDENTIFY_FRONT = (
    '<div class="card-map">\n'
    '{{Basemap}}\n'
    '{{BasemapRot}}\n'
    '{{AllPois}}\n'
    '{{Highlight}}\n'
    '{{Context}}\n'
    '{{#Thumbnail}}{{Thumbnail}}{{/Thumbnail}}\n'
    '<button class="hint-btn" onclick="var i=this.parentNode.querySelector(\'img.allpois\');var v=i.style.display!==\'block\';i.style.display=v?\'block\':\'none\';this.textContent=v?\'\\u2716 POIs\':\'\\u25a6 POIs\';sessionStorage.setItem(\'ps_pois\',v?\'1\':\'0\');">&#9638; POIs</button>\n'
    '<button class="hint-btn" style="left:80px;" onclick="var i=this.parentNode.querySelector(\'img.context\');var v=i.style.display!==\'block\';i.style.display=v?\'block\':\'none\';this.textContent=v?\'\\u2716 Kontext\':\'\\u25a6 Kontext\';sessionStorage.setItem(\'ps_ctx\',v?\'1\':\'0\');">&#9638; Kontext</button>\n'
    '<div class="compass-btn" onclick="' + _COMPASS_ONCLICK + '">' + _NORDPFEIL_SVG + '</div>\n'
    '</div>\n'
    '<script>' + _SESSION_RESTORE_POI + '</script>\n'
)

_POI_TMPL_IDENTIFY_BACK = (
    '<div class="answer-info">\n'
    '<div class="name">{{Name}}</div>\n'
    '<div class="detail">{{Category}} &middot; {{Info}}</div>\n'
    '</div>\n'
    '<hr>\n'
    '<div class="card-map">\n'
    '{{Basemap}}\n'
    '{{BasemapRot}}\n'
    '{{AllPois}}\n'
    '{{BackOverlay}}\n'
    '{{Context}}\n'
    '{{#Thumbnail}}{{Thumbnail}}{{/Thumbnail}}\n'
    '<button class="hint-btn" onclick="var i=this.parentNode.querySelector(\'img.allpois\');var v=i.style.display!==\'block\';i.style.display=v?\'block\':\'none\';this.textContent=v?\'\\u2716 POIs\':\'\\u25a6 POIs\';sessionStorage.setItem(\'ps_pois\',v?\'1\':\'0\');">&#9638; POIs</button>\n'
    '<button class="hint-btn" style="left:80px;" onclick="var i=this.parentNode.querySelector(\'img.context\');var v=i.style.display!==\'block\';i.style.display=v?\'block\':\'none\';this.textContent=v?\'\\u2716 Kontext\':\'\\u25a6 Kontext\';sessionStorage.setItem(\'ps_ctx\',v?\'1\':\'0\');">&#9638; Kontext</button>\n'
    '<div class="compass-btn" onclick="' + _COMPASS_ONCLICK + '">' + _NORDPFEIL_SVG + '</div>\n'
    '</div>\n'
    '{{#OsmPic}}\n'
    '<div class="cupx-pics">\n'
    '<div class="pic-label">Satellitenbild</div>\n'
    '{{OsmPic}}\n'
    '{{#FieldPic}}\n'
    '<div class="pic-label">Feldfoto</div>\n'
    '{{FieldPic}}\n'
    '{{/FieldPic}}\n'
    '</div>\n'
    '{{/OsmPic}}\n'
    '<script>' + _SESSION_RESTORE_POI + '</script>\n'
)


# ─── Shared POI model ─────────────────────────────────────────────────────────

def _poi_model(model_id: int, model_name: str) -> genanki.Model:
    """Create the shared Anki model for POI cards.

    Fields:
        POI_ID, Name, Category, Info,
        Basemap, BasemapRot,
        AllPois, Highlight, BackOverlay, Context,
        Thumbnail  (empty string for full-map decks, filename for sub-regions)
        OsmPic     (CUPX satellite image, Landewiesen only)
        FieldPic   (CUPX field photo, Landewiesen only — may be empty)
    """
    return genanki.Model(
        model_id,
        model_name,
        fields=[
            {"name": "POI_ID"},
            {"name": "Name"},
            {"name": "Category"},
            {"name": "Info"},
            {"name": "Basemap"},
            {"name": "BasemapRot"},
            {"name": "AllPois"},
            {"name": "Highlight"},
            {"name": "BackOverlay"},
            {"name": "Context"},
            {"name": "Thumbnail"},
            {"name": "OsmPic"},
            {"name": "FieldPic"},
        ],
        templates=[
            {
                "name": "Was ist das?",
                "qfmt": _POI_TMPL_IDENTIFY_FRONT,
                "afmt": _POI_TMPL_IDENTIFY_BACK,
            },
        ],
        css=_POI_APKG_CSS,
    )


# ─── Shared POI note construction ─────────────────────────────────────────────

def _poi_info_str(poi) -> str:
    """Build the Info field string for a POI note."""
    parts = []
    if poi.elevation:
        parts.append(f"{poi.elevation} m")
    if poi.subtitle:
        parts.append(poi.subtitle)
    return " · ".join(parts) if parts else ""


def _collect_shared_layers(d: POIDeck, media_files: list) -> dict:
    """Validate and collect shared layer image paths for a POI deck.

    Returns a dict with HTML strings for basemap, all_pois, and context,
    or None if any required file is missing.
    """
    result = {}

    basemap_file = d.filename_basemap()
    basemap_path = d.output_images_dir / basemap_file
    if not basemap_path.exists():
        print(f"[APKG-POI] ERROR: Basemap not found: {basemap_path}")
        return None
    media_files.append(str(basemap_path))
    result["basemap_html"] = f'<img class="basemap" src="{basemap_file}">'

    basemap_rot_file = d.filename_basemap_rot()
    basemap_rot_path = d.output_images_dir / basemap_rot_file
    if not basemap_rot_path.exists():
        print(f"[APKG-POI] ERROR: Rotated basemap not found: {basemap_rot_path}")
        return None
    media_files.append(str(basemap_rot_path))
    result["basemap_rot_html"] = f'<img class="basemap-rot" src="{basemap_rot_file}">'

    context_file = d.filename_context()
    context_path = d.output_images_dir / context_file
    if not context_path.exists():
        print(f"[APKG-POI] ERROR: Context not found: {context_path}")
        return None
    media_files.append(str(context_path))
    result["context_html"] = f'<img class="overlay context" src="{context_file}">'

    all_pois_file = d.filename_all_pois_overlay(".webp")
    all_pois_path = d.output_images_dir / all_pois_file
    if not all_pois_path.exists():
        print(f"[APKG-POI] ERROR: All-POIs overlay not found: {all_pois_path}")
        return None
    media_files.append(str(all_pois_path))
    result["all_pois_html"] = f'<img class="overlay allpois" src="{all_pois_file}">'

    return result


def _build_poi_notes(
    d: POIDeck,
    model: genanki.Model,
    pois: list,
    layers: dict,
    media_files: list,
    thumbnail_file: str = "",
    guid_prefix: str = "",
    extra_tags: list = None,
) -> tuple:
    """Build genanki.Note objects for a list of POIs.

    Args:
        d: POI deck (provides filenames and category styles).
        model: Shared Anki model.
        pois: List of POI objects to create notes for.
        layers: Dict from _collect_shared_layers (basemap/allpois/context HTML).
        media_files: Accumulator list for media file paths.
        thumbnail_file: Filename for the overview thumbnail (empty = none).
        guid_prefix: Prefix for deterministic GUIDs (avoids collisions
                     when the same POI appears in multiple subdecks).
        extra_tags: Additional Anki tags beyond the POI category.

    Returns:
        (notes, skipped) — list of notes and count of skipped POIs.
    """
    cat_labels = {
        cat: style.get("label", cat.capitalize())
        for cat, style in d.category_style.items()
    }

    notes = []
    skipped = 0

    for poi in pois:
        highlight_file = d.filename_poi_highlight(poi.poi_id, ".webp")
        back_file = d.filename_poi_back(poi.poi_id, ".webp")
        highlight_path = d.output_images_dir / highlight_file
        back_path = d.output_images_dir / back_file

        if not highlight_path.exists() or not back_path.exists():
            skipped += 1
            missing = []
            if not highlight_path.exists():
                missing.append("highlight")
            if not back_path.exists():
                missing.append("back")
            print(f"[APKG-POI] WARN: Missing {', '.join(missing)} "
                  f"for {poi.poi_id} ({poi.name})")
            continue

        media_files.append(str(highlight_path))
        media_files.append(str(back_path))

        tags = [poi.category]
        if extra_tags:
            tags.extend(extra_tags)

        # CUPX pics (Landewiesen only — empty for other POI decks)
        osm_pic_html = ""
        field_pic_html = ""
        if hasattr(poi, 'pics') and poi.pics:
            from classifications.landewiesen import pic_path
            for pic_name in poi.pics:
                pp = pic_path(pic_name)
                if pp.exists():
                    media_files.append(str(pp))
                    if '_osm' in pic_name:
                        osm_pic_html = f'<img src="{pic_name}">'
                    else:
                        field_pic_html = f'<img src="{pic_name}">'

        note = genanki.Note(
            model=model,
            fields=[
                poi.poi_id,
                poi.name,
                cat_labels.get(poi.category, poi.category),
                _poi_info_str(poi),
                layers["basemap_html"],
                layers["basemap_rot_html"],
                layers["all_pois_html"],
                f'<img class="overlay" src="{highlight_file}">',
                f'<img class="overlay" src="{back_file}">',
                layers["context_html"],
                f'<img class="thumbnail" src="{thumbnail_file}">' if thumbnail_file else "",
                osm_pic_html,
                field_pic_html,
            ],
            tags=tags,
        )
        # Custom GUID to avoid Anki treating same POI in different
        # subdecks as duplicates
        if guid_prefix:
            note.guid = genanki.guid_for(f"{guid_prefix}_{poi.poi_id}")

        notes.append(note)

    return notes, skipped


# ─── Single POI deck (flat, no subdecks) ──────────────────────────────────────

def generate_apkg_poi(d: POIDeck) -> None:
    """Generate a ready-to-import .apkg file for a single flat POI deck.

    Used when no POI_MULTI_DECK config is defined for this region.
    """
    _ensure_images(d)

    today = date.today().isoformat()
    region_label = d.region.name.capitalize()
    system_label = d.poi_classification.title
    deck_title = f"{region_label} {system_label} (Beta {today})"

    base = f"peak_soaring_{d.name}"
    _MODEL_VER = 6
    model_id = int(hashlib.sha256(f"{base}_poi_model_v{_MODEL_VER}".encode()).hexdigest()[:8], 16)
    deck_id = int(hashlib.sha256(f"{base}_poi_deck".encode()).hexdigest()[:8], 16)

    model = _poi_model(model_id, f"{region_label} {system_label}")
    anki_deck = genanki.Deck(deck_id, deck_title)
    media_files: list[str] = []

    layers = _collect_shared_layers(d, media_files)
    if layers is None:
        return

    notes, skipped = _build_poi_notes(d, model, d.pois, layers, media_files)
    for n in notes:
        anki_deck.add_note(n)

    if skipped:
        print(f"\n[APKG-POI] WARNING: {skipped} POIs skipped (missing overlays).")

    _write_apkg(
        d.output_csv_dir / f"{d.anki_csv_name}.apkg",
        anki_deck, media_files,
        label="APKG-POI", title=deck_title,
    )


# ─── Multi-deck POI — subdecks by sub-region + category ──────────────────────

def generate_apkg_poi_multi(d: POIDeck, region_name: str) -> None:
    """Build a single .apkg with multiple POI subdecks.

    Structure (example for ostalpen):
        Parent Title
        ├── A Königsdorf    (zoomed sub-region, all POI types, with thumbnail)
        ├── B Innsbruck     (zoomed sub-region, all POI types, with thumbnail)
        ├── C Gipfel        (full map, peaks only)
        ├── D Pässe         (full map, passes only)
        ├── E Orte          (full map, towns only)
        ├── F Täler         (full map, valleys only)
        └── G Seen          (full map, lakes only)

    Sub-region decks use their own zoomed basemap + overlays and show
    a small thumbnail of the full Ostalpen map with a red rectangle.
    Category decks use the full-region basemap and filter by POI type.
    """
    multi_key = f"{region_name}_pois"
    multi_cfg = D.POI_MULTI_DECK.get(multi_key)
    if not multi_cfg:
        print(f"[APKG-POI] No multi-deck config for {multi_key}")
        return

    _ensure_images(d)

    parent_title = multi_cfg["parent_title"]
    base = f"peak_soaring_{multi_key}"
    # Bump _MODEL_VER when fields or templates change to force Anki
    # to create a fresh note-type on re-import (otherwise the old
    # model is kept and new fields like Thumbnail are invisible).
    _MODEL_VER = 6
    model_id = int(hashlib.sha256(
        f"{base}_multi_model_v{_MODEL_VER}".encode()
    ).hexdigest()[:8], 16)
    model = _poi_model(model_id, parent_title)

    anki_subdecks: list = []
    media_files: list[str] = []
    media_set: set[str] = set()  # deduplicate media paths

    def _add_media(path_str: str):
        if path_str not in media_set:
            media_set.add(path_str)
            media_files.append(path_str)

    # ── A) Sub-region subdecks (zoomed map + thumbnail) ──────────────────
    for sub_key, sub_label in multi_cfg.get("sub_regions", []):
        subdeck_title = f"{parent_title}::{sub_label}"
        subdeck_id = int(hashlib.sha256(
            f"{base}_{sub_label}_deck".encode()
        ).hexdigest()[:8], 16)

        anki_deck = genanki.Deck(subdeck_id, subdeck_title)

        # Build sub-region POIDeck
        sub_deck = D.get_sub_region_poi_deck(region_name, sub_key)
        _ensure_images(sub_deck)

        # Collect sub-region shared layers (zoomed basemap + overlays)
        sub_media: list[str] = []
        layers = _collect_shared_layers(sub_deck, sub_media)
        if layers is None:
            print(f"[APKG-POI] WARN: Skipping sub-region {sub_key} (missing layers)")
            continue
        for m in sub_media:
            _add_media(m)

        # Thumbnail: overview of full Ostalpen with red rect
        thumb_file = f"{d.prefix}_thumb_{sub_key}.webp"
        thumb_path = d.output_images_dir / thumb_file
        if thumb_path.exists():
            _add_media(str(thumb_path))
        else:
            print(f"[APKG-POI] WARN: Thumbnail not found: {thumb_file}")
            thumb_file = ""

        notes, skipped = _build_poi_notes(
            sub_deck, model, sub_deck.pois, layers, media_files,
            thumbnail_file=thumb_file,
            guid_prefix=f"sub_{sub_key}",
            extra_tags=[sub_key],
        )
        # Deduplicate media from notes
        for n in notes:
            anki_deck.add_note(n)

        n = len(anki_deck.notes)
        print(f"[APKG-POI]   {sub_label}: {n} notes ({len(sub_deck.pois)} POIs)")
        anki_subdecks.append(anki_deck)

    # ── B) Category subdecks (full map, filter by POI type) ──────────────
    # Exclude POIs that already appear in a sub-region deck
    sub_poi_ids = D.get_all_sub_region_poi_ids(region_name)
    if sub_poi_ids:
        print(f"[APKG-POI] Excluding {len(sub_poi_ids)} sub-region POIs "
              f"from category decks")

    # Collect full-region shared layers once
    full_media: list[str] = []
    full_layers = _collect_shared_layers(d, full_media)
    if full_layers is None:
        print("[APKG-POI] ERROR: Cannot build category decks (missing layers)")
        return
    for m in full_media:
        _add_media(m)

    for cat_key, cat_label in multi_cfg.get("categories", []):
        subdeck_title = f"{parent_title}::{cat_label}"
        subdeck_id = int(hashlib.sha256(
            f"{base}_{cat_label}_deck".encode()
        ).hexdigest()[:8], 16)

        anki_deck = genanki.Deck(subdeck_id, subdeck_title)

        cat_pois = [p for p in d.poi_classification.pois_by_category(cat_key)
                     if p.poi_id not in sub_poi_ids]
        if not cat_pois:
            print(f"[APKG-POI]   {cat_label}: 0 POIs (skipped)")
            continue

        notes, skipped = _build_poi_notes(
            d, model, cat_pois, full_layers, media_files,
            thumbnail_file="",  # no thumbnail for full-map decks
            guid_prefix=f"cat_{cat_key}",
            extra_tags=[cat_key],
        )
        for n in notes:
            anki_deck.add_note(n)

        n = len(anki_deck.notes)
        print(f"[APKG-POI]   {cat_label}: {n} notes")
        anki_subdecks.append(anki_deck)

    _write_apkg(
        d.output_csv_dir / f"{d.anki_csv_name}.apkg",
        anki_subdecks, media_files,
        label="APKG-POI", title=parent_title,
    )


def main():
    parser = argparse.ArgumentParser(description="Build Anki .apkg deck")
    D.add_deck_arguments(parser)
    args = parser.parse_args()

    d = D.get_deck(args.region, args.system)

    # ── Check for subdeck-merge redirect ─────────────────────────────────
    actual_system = args.system or D.REGION_DEFAULTS[args.region]
    merge_key = D._merge_key_for(args.region, actual_system)

    if merge_key and merge_key in D.SUBDECK_MERGE:
        primary_system = D.SUBDECK_MERGE[merge_key][0][0]
        if actual_system != primary_system:
            print(f"[INFO] '{actual_system}' is part of the combined "
                  f"'{merge_key}' deck.")
            print(f"       Use:  python scripts/04_build_deck.py "
                  f"--region {args.region} --system {primary_system}")
            sys.exit(0)

    if isinstance(d, POIDeck):
        # Check for multi-deck config
        multi_key = f"{args.region}_{actual_system}"
        if multi_key in D.POI_MULTI_DECK:
            cfg = D.POI_MULTI_DECK[multi_key]
            labels = [lbl for _, lbl in cfg.get("sub_regions", [])] + \
                     [lbl for _, lbl in cfg.get("categories", [])]
            print(f"=== Building multi-deck POI APKG "
                  f"({len(labels)} subdecks) for: {d.title} ===\n")
            generate_apkg_poi_multi(d, args.region)
        else:
            print(f"=== Building POI APKG for: {d.title} ===\n")
            generate_apkg_poi(d)
    elif merge_key:
        labels = " + ".join(lbl for _, lbl in D.SUBDECK_MERGE[merge_key])
        print(f"=== Building combined APKG ({labels}) for: {d.title} ===\n")
        generate_apkg_combined(args.region, merge_key)
    else:
        print(f"=== Building APKG for: {d.title} ===\n")
        generate_apkg(d)


if __name__ == "__main__":
    main()
