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
_APKG_CSS = """\
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
.card-map img.partition,
.card-map img.context {
    display: none;
}
.answer-info {
    margin: 10px 0;
    font-size: 18px;
}
.answer-info .name {
    font-weight: bold;
    font-size: 20px;
}
.answer-info .gipfel {
    color: #555;
    font-size: 15px;
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
"""

_TMPL_FRONT = """\
<div class="card-map">
{{Basemap}}
{{Partition}}
{{Context}}
{{FrontOverlay}}
<button class="hint-btn" onclick="var i=this.parentNode.querySelector('img.partition');var v=i.style.display!=='block';i.style.display=v?'block':'none';this.textContent=v?'\u2716 Einteilung':'\u25a6 Einteilung';sessionStorage.setItem('ps_et',v?'1':'0');">&#9638; Einteilung</button>
<button class="hint-btn" style="left:110px;" onclick="var i=this.parentNode.querySelector('img.context');var v=i.style.display!=='block';i.style.display=v?'block':'none';this.textContent=v?'\u2716 Kontext':'\u25a6 Kontext';sessionStorage.setItem('ps_ctx',v?'1':'0');">&#9638; Kontext</button>
</div>
<script>(function(){var c=document.querySelector('.card-map');if(!c)return;var bs=c.querySelectorAll('.hint-btn');if(sessionStorage.getItem('ps_et')==='1'){var p=c.querySelector('img.partition');if(p)p.style.display='block';if(bs[0])bs[0].textContent='\u2716 Einteilung';}if(sessionStorage.getItem('ps_ctx')==='1'){var x=c.querySelector('img.context');if(x)x.style.display='block';if(bs[1])bs[1].textContent='\u2716 Kontext';}})();</script>
"""

_TMPL_BACK = """\
<div class="answer-info">
<div class="name">{{Name}} ({{Group_ID}})</div>
<div class="gipfel">{{Hoechster_Gipfel}}</div>
</div>
<hr>
<div class="card-map">
{{Basemap}}
{{Partition}}
{{Context}}
{{BackOverlay}}
<button class="hint-btn" onclick="var i=this.parentNode.querySelector('img.partition');var v=i.style.display!=='block';i.style.display=v?'block':'none';this.textContent=v?'\u2716 Einteilung':'\u25a6 Einteilung';sessionStorage.setItem('ps_et',v?'1':'0');">&#9638; Einteilung</button>
<button class="hint-btn" style="left:110px;" onclick="var i=this.parentNode.querySelector('img.context');var v=i.style.display!=='block';i.style.display=v?'block':'none';this.textContent=v?'\u2716 Kontext':'\u25a6 Kontext';sessionStorage.setItem('ps_ctx',v?'1':'0');">&#9638; Kontext</button>
</div>
<script>(function(){var c=document.querySelector('.card-map');if(!c)return;var bs=c.querySelectorAll('.hint-btn');if(sessionStorage.getItem('ps_et')==='1'){var p=c.querySelector('img.partition');if(p)p.style.display='block';if(bs[0])bs[0].textContent='\u2716 Einteilung';}if(sessionStorage.getItem('ps_ctx')==='1'){var x=c.querySelector('img.context');if(x)x.style.display='block';if(bs[1])bs[1].textContent='\u2716 Kontext';}})();</script>
"""


def generate_apkg(d: Deck) -> None:
    """Generate a ready-to-import .apkg file for a single classification."""
    _ensure_images(d)

    region_label = d.region.name.capitalize()
    deck_title = f"Gebirgsgruppen der {region_label}"

    # Stable IDs (deterministic from deck identity, not date)
    base = f"peak_soaring_{d.name}"
    model_id = int(hashlib.sha256(f"{base}_model".encode()).hexdigest()[:8], 16)
    deck_id = int(hashlib.sha256(f"{base}_deck".encode()).hexdigest()[:8], 16)

    model = genanki.Model(
        model_id,
        deck_title,
        fields=[
            {"name": "Group_ID"},
            {"name": "Name"},
            {"name": "Hoechster_Gipfel"},
            {"name": "Basemap"},
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

    anki_deck = genanki.Deck(deck_id, deck_title)
    media_files: list[str] = []

    # ── Check basemap ──────────────────────────────────────────────────────────
    basemap_file = d.filename_basemap()
    basemap_path = d.output_images_dir / basemap_file
    if not basemap_path.exists():
        print(f"[APKG] ERROR: Basemap not found: {basemap_path}")
        print("       Run:  python scripts/03_generate_cards.py "
              f"--region {d.region.name}")
        return
    media_files.append(str(basemap_path))
    basemap_html = f'<img class="basemap" src="{basemap_file}">'

    # ── Partition image (Einteilung, shared, toggle via hint button) ─────────
    partition_file = d.filename_partition(".webp")
    partition_path = d.output_images_dir / partition_file
    if not partition_path.exists():
        print(f"[APKG] ERROR: Partition not found: {partition_path}")
        print("       Run:  python scripts/03_generate_cards.py "
              f"--region {d.region.name}")
        return
    media_files.append(str(partition_path))
    partition_html = f'<img class="overlay partition" src="{partition_file}">'

    # ── Context image (borders + cities, toggle via hint button) ─────────────
    context_file = d.filename_context()
    context_path = d.output_images_dir / context_file
    if not context_path.exists():
        print(f"[APKG] ERROR: Context not found: {context_path}")
        print("       Run:  python scripts/03_generate_cards.py "
              f"--region {d.region.name}")
        return
    media_files.append(str(context_path))
    context_html = f'<img class="overlay context" src="{context_file}">'

    # ── Build notes ──────────────────────────────────────────────────────────
    skipped = 0
    for group in d.groups:
        front_file = d.filename_group_front(group.group_id, ".webp")
        back_file = d.filename_group_back(group.group_id, ".webp")
        front_path = d.output_images_dir / front_file
        back_path = d.output_images_dir / back_file

        if not front_path.exists() or not back_path.exists():
            skipped += 1
            print(f"[APKG] WARN: Missing overlay for group {group.group_id} "
                  f"({group.name})")
            continue

        media_files.append(str(front_path))
        media_files.append(str(back_path))

        # Embed <img> tags directly in the fields so Anki's media
        # scanner picks them up during import.
        note = genanki.Note(
            model=model,
            fields=[
                group.group_id,
                group.name,
                group.hoechster_gipfel,
                basemap_html,
                f'<img class="overlay" src="{front_file}">',
                f'<img class="overlay" src="{back_file}">',
                partition_html,
                context_html,
            ],
        )
        anki_deck.add_note(note)

    if skipped:
        print(f"[APKG] WARNING: {skipped} groups skipped (missing overlays).")
        print("       Run:  python scripts/03_generate_cards.py "
              f"--region {d.region.name} --force")

    # ── Write .apkg ──────────────────────────────────────────────────────────
    apkg_path = d.output_csv_dir / f"{d.anki_csv_name}.apkg"
    apkg_path.parent.mkdir(parents=True, exist_ok=True)

    package = genanki.Package(anki_deck)
    package.media_files = media_files
    package.write_to_file(str(apkg_path))

    n_notes = len(anki_deck.notes)
    n_media = len(media_files)
    size_mb = apkg_path.stat().st_size / (1024 * 1024)
    print(f"\n[APKG] {deck_title}")
    print(f"[APKG] {n_notes} notes, {n_media} media files, {size_mb:.1f} MB")
    print(f"[APKG] -> {apkg_path}")
    print(f"\n  Import in Anki:  File -> Import -> {apkg_path.name}")


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
    d_primary = sub_decks_cfg[0][0]           # first deck drives naming
    region_label = d_primary.region.name.capitalize()
    parent_title = f"Gebirgsgruppen der {region_label}"

    # One model for all subdecks (fields / templates / CSS are identical)
    base = f"peak_soaring_{merge_key}"
    model_id = int(hashlib.sha256(f"{base}_combined_model".encode()).hexdigest()[:8], 16)

    model = genanki.Model(
        model_id,
        parent_title,
        fields=[
            {"name": "Group_ID"},
            {"name": "Name"},
            {"name": "Hoechster_Gipfel"},
            {"name": "Basemap"},
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

    # ── Shared basemap (from first sub-deck, identical raster for all) ───
    basemap_file = d_primary.filename_basemap()
    basemap_path = d_primary.output_images_dir / basemap_file
    if not basemap_path.exists():
        print(f"[APKG] ERROR: Basemap not found: {basemap_path}")
        return

    media_files: list[str] = [str(basemap_path)]
    basemap_html = f'<img class="basemap" src="{basemap_file}">'
    anki_subdecks: list = []
    total_notes = 0
    total_skipped = 0

    # ── Build each subdeck ───────────────────────────────────────────────
    for d_sub, label in sub_decks_cfg:
        subdeck_title = f"{parent_title}::{label}"
        subdeck_id = int(hashlib.sha256(
            f"{base}_{label}_deck".encode()
        ).hexdigest()[:8], 16)

        anki_deck = genanki.Deck(subdeck_id, subdeck_title)

        # Partition (per-classification — different groupings)
        partition_file = d_sub.filename_partition(".webp")
        partition_path = d_sub.output_images_dir / partition_file
        if not partition_path.exists():
            print(f"[APKG] ERROR: Partition not found: {partition_path}")
            return
        media_files.append(str(partition_path))
        partition_html = f'<img class="overlay partition" src="{partition_file}">'

        # Context (per-classification)
        context_file = d_sub.filename_context()
        context_path = d_sub.output_images_dir / context_file
        if not context_path.exists():
            print(f"[APKG] ERROR: Context not found: {context_path}")
            return
        media_files.append(str(context_path))
        context_html = f'<img class="overlay context" src="{context_file}">'

        # Notes
        skipped = 0
        for group in d_sub.groups:
            front_file = d_sub.filename_group_front(group.group_id, ".webp")
            back_file = d_sub.filename_group_back(group.group_id, ".webp")
            front_path = d_sub.output_images_dir / front_file
            back_path = d_sub.output_images_dir / back_file

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
                    basemap_html,
                    f'<img class="overlay" src="{front_file}">',
                    f'<img class="overlay" src="{back_file}">',
                    partition_html,
                    context_html,
                ],
            )
            anki_deck.add_note(note)

        n = len(anki_deck.notes)
        total_notes += n
        total_skipped += skipped
        print(f"[APKG]   {label}: {n} notes")
        anki_subdecks.append(anki_deck)

    if total_skipped:
        print(f"[APKG] WARNING: {total_skipped} groups skipped (missing overlays).")

    # ── Write combined .apkg ─────────────────────────────────────────────
    apkg_path = d_primary.output_csv_dir / f"{d_primary.anki_csv_name}.apkg"
    apkg_path.parent.mkdir(parents=True, exist_ok=True)

    package = genanki.Package(anki_subdecks)
    package.media_files = media_files
    package.write_to_file(str(apkg_path))

    n_media = len(media_files)
    size_mb = apkg_path.stat().st_size / (1024 * 1024)
    print(f"\n[APKG] {parent_title}")
    print(f"[APKG] {total_notes} notes in {len(anki_subdecks)} subdecks, "
          f"{n_media} media files, {size_mb:.1f} MB")
    print(f"[APKG] -> {apkg_path}")
    print(f"\n  Import in Anki:  File -> Import -> {apkg_path.name}")


# ═══════════════════════════════════════════════════════════════════════════════
# POI DECK — APKG Export
# ═══════════════════════════════════════════════════════════════════════════════

_POI_APKG_CSS = """\
.card {
    font-family: "Segoe UI", Arial, Helvetica, sans-serif;
    font-size: 16px;
    text-align: center;
    color: #222;
    background: #fff;
    margin: 0;
    padding: 0;
}
.question {
    font-size: 20px;
    font-weight: bold;
    color: #CC0000;
    margin: 10px 0 2px;
}
.info {
    font-size: 14px;
    color: #666;
    margin-bottom: 6px;
}
.answer-info {
    margin: 10px 0;
    font-size: 18px;
}
.answer-info .name {
    font-weight: bold;
    font-size: 20px;
    color: #CC0000;
}
.answer-info .detail {
    color: #555;
    font-size: 15px;
}
.card-map {
    position: relative;
    display: inline-block;
    line-height: 0;
    margin: 4px 0;
    overflow: hidden;
    cursor: pointer;
    -webkit-user-select: none;
    user-select: none;
}
.card-map img {
    max-width: 100%;
    transition: width 0.2s ease;
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
.card-map img.context {
    display: none;
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
"""

# Pinch-to-zoom + double-tap JavaScript for Anki cards
_POI_ZOOM_JS = """\
<script>
(function(){
  document.querySelectorAll('.card-map').forEach(function(mc){
    var scale = 1;
    var lastTap = 0;
    mc.addEventListener('touchend', function(e) {
      var now = Date.now();
      if (now - lastTap < 300) {
        e.preventDefault();
        scale = scale > 1 ? 1 : 2.5;
        applyZoom(mc, scale);
      }
      lastTap = now;
    });
    mc.addEventListener('dblclick', function(e) {
      e.preventDefault();
      scale = scale > 1 ? 1 : 2.5;
      applyZoom(mc, scale);
    });
  });
  function applyZoom(mc, s) {
    mc.querySelectorAll('img').forEach(function(img) {
      img.style.width = s > 1 ? (s * 100) + '%' : '';
      img.style.maxWidth = s > 1 ? 'none' : '100%';
    });
    mc.style.overflow = s > 1 ? 'auto' : 'hidden';
    if (s <= 1) { mc.scrollLeft = 0; mc.scrollTop = 0; }
  }
})();
</script>
"""

# Template 1: "Wo ist X?"  (locate a named POI on the blank map)
_POI_TMPL_LOCATE_FRONT = """\
<div class="question">Wo ist: {{Name}}?</div>
<div class="info">{{Category}} · {{Info}}</div>
<hr>
<div class="card-map">
{{Basemap}}
{{Context}}
<button class="hint-btn" onclick="var i=this.parentNode.querySelector('img.context');var v=i.style.display!=='block';i.style.display=v?'block':'none';this.textContent=v?'\u2716 Kontext':'\u25a6 Kontext';sessionStorage.setItem('ps_ctx',v?'1':'0');">&#9638; Kontext</button>
</div>
<script>(function(){var c=document.querySelector('.card-map');if(!c)return;if(sessionStorage.getItem('ps_ctx')==='1'){var x=c.querySelector('img.context');if(x)x.style.display='block';var b=c.querySelector('.hint-btn');if(b)b.textContent='\u2716 Kontext';}})();</script>
""" + _POI_ZOOM_JS

_POI_TMPL_LOCATE_BACK = """\
<div class="answer-info">
<span class="name">{{Name}}</span>
<span class="detail"> · {{Category}} · {{Info}}</span>
</div>
<hr>
<div class="card-map">
{{Basemap}}
{{AllPois}}
{{BackOverlay}}
{{Context}}
<button class="hint-btn" onclick="var i=this.parentNode.querySelector('img.context');var v=i.style.display!=='block';i.style.display=v?'block':'none';this.textContent=v?'\u2716 Kontext':'\u25a6 Kontext';sessionStorage.setItem('ps_ctx',v?'1':'0');">&#9638; Kontext</button>
</div>
<script>(function(){var c=document.querySelector('.card-map');if(!c)return;if(sessionStorage.getItem('ps_ctx')==='1'){var x=c.querySelector('img.context');if(x)x.style.display='block';var b=c.querySelector('.hint-btn');if(b)b.textContent='\u2716 Kontext';}})();</script>
""" + _POI_ZOOM_JS

# Template 2: "Was ist das?"  (identify a highlighted POI)
_POI_TMPL_IDENTIFY_FRONT = """\
<div class="question">Was ist das?</div>
<div class="info">{{Category}}</div>
<hr>
<div class="card-map">
{{Basemap}}
{{AllPois}}
{{Highlight}}
{{Context}}
<button class="hint-btn" onclick="var i=this.parentNode.querySelector('img.context');var v=i.style.display!=='block';i.style.display=v?'block':'none';this.textContent=v?'\u2716 Kontext':'\u25a6 Kontext';sessionStorage.setItem('ps_ctx',v?'1':'0');">&#9638; Kontext</button>
</div>
<script>(function(){var c=document.querySelector('.card-map');if(!c)return;if(sessionStorage.getItem('ps_ctx')==='1'){var x=c.querySelector('img.context');if(x)x.style.display='block';var b=c.querySelector('.hint-btn');if(b)b.textContent='\u2716 Kontext';}})();</script>
""" + _POI_ZOOM_JS

_POI_TMPL_IDENTIFY_BACK = """\
<div class="answer-info">
<span class="name">{{Name}}</span><br>
<span class="detail">{{Category}} · {{Info}}</span>
</div>
<hr>
<div class="card-map">
{{Basemap}}
{{AllPois}}
{{BackOverlay}}
{{Context}}
<button class="hint-btn" onclick="var i=this.parentNode.querySelector('img.context');var v=i.style.display!=='block';i.style.display=v?'block':'none';this.textContent=v?'\u2716 Kontext':'\u25a6 Kontext';sessionStorage.setItem('ps_ctx',v?'1':'0');">&#9638; Kontext</button>
</div>
<script>(function(){var c=document.querySelector('.card-map');if(!c)return;if(sessionStorage.getItem('ps_ctx')==='1'){var x=c.querySelector('img.context');if(x)x.style.display='block';var b=c.querySelector('.hint-btn');if(b)b.textContent='\u2716 Kontext';}})();</script>
""" + _POI_ZOOM_JS


def generate_apkg_poi(d: POIDeck) -> None:
    """Generate a ready-to-import .apkg file for a POI deck.

    Two card templates:
      1. "Wo ist X?"     — front: question + basemap,
                            back: basemap + all_pois + back; Kontext button toggles context
      2. "Was ist das?"   — front: basemap + all_pois + highlight circle,
                            back: basemap + all_pois + back; Kontext button toggles context

    Supports double-tap / pinch-to-zoom via embedded JavaScript.
    """
    _ensure_images(d)

    today = date.today().isoformat()
    region_label = d.region.name.capitalize()
    system_label = d.poi_classification.title
    deck_title = f"{region_label} {system_label} (Beta {today})"

    # Stable IDs (deterministic from deck identity)
    base = f"peak_soaring_{d.name}"
    model_id = int(hashlib.sha256(f"{base}_poi_model".encode()).hexdigest()[:8], 16)
    deck_id = int(hashlib.sha256(f"{base}_poi_deck".encode()).hexdigest()[:8], 16)

    model = genanki.Model(
        model_id,
        f"{region_label} {system_label}",
        fields=[
            {"name": "POI_ID"},
            {"name": "Name"},
            {"name": "Category"},
            {"name": "Info"},
            {"name": "Basemap"},
            {"name": "AllPois"},
            {"name": "Highlight"},
            {"name": "BackOverlay"},
            {"name": "Context"},
        ],
        templates=[
            {
                "name": "Wo ist X?",
                "qfmt": _POI_TMPL_LOCATE_FRONT,
                "afmt": _POI_TMPL_LOCATE_BACK,
            },
            {
                "name": "Was ist das?",
                "qfmt": _POI_TMPL_IDENTIFY_FRONT,
                "afmt": _POI_TMPL_IDENTIFY_BACK,
            },
        ],
        css=_POI_APKG_CSS,
    )

    anki_deck = genanki.Deck(deck_id, deck_title)
    media_files: list[str] = []

    # ── Shared layers ──────────────────────────────────────────────────────
    basemap_file = d.filename_basemap()
    basemap_path = d.output_images_dir / basemap_file
    if not basemap_path.exists():
        print(f"[APKG-POI] ERROR: Basemap not found: {basemap_path}")
        return
    media_files.append(str(basemap_path))

    context_file = d.filename_context()
    context_path = d.output_images_dir / context_file
    if not context_path.exists():
        print(f"[APKG-POI] ERROR: Context not found: {context_path}")
        return
    media_files.append(str(context_path))

    all_pois_file = d.filename_all_pois_overlay(".webp")
    all_pois_path = d.output_images_dir / all_pois_file
    if not all_pois_path.exists():
        print(f"[APKG-POI] ERROR: All-POIs overlay not found: {all_pois_path}")
        return
    media_files.append(str(all_pois_path))

    basemap_html = f'<img class="basemap" src="{basemap_file}">'
    all_pois_html = f'<img class="overlay" src="{all_pois_file}">'
    context_html = f'<img class="overlay context" src="{context_file}">'

    # ── Category labels ────────────────────────────────────────────────────
    cat_labels = {}
    for cat, style in d.category_style.items():
        cat_labels[cat] = style.get("label", cat.capitalize())

    # ── Build notes ────────────────────────────────────────────────────────
    skipped = 0
    for poi in d.pois:
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

        # Info string
        info_parts = []
        if poi.elevation:
            info_parts.append(f"{poi.elevation} m")
        if poi.subtitle:
            info_parts.append(poi.subtitle)
        info_str = " · ".join(info_parts) if info_parts else ""

        # Category label
        cat_label = cat_labels.get(poi.category, poi.category)

        note = genanki.Note(
            model=model,
            fields=[
                poi.poi_id,
                poi.name,
                cat_label,
                info_str,
                basemap_html,
                all_pois_html,
                f'<img class="overlay" src="{highlight_file}">',
                f'<img class="overlay" src="{back_file}">',
                context_html,
            ],
            tags=[poi.category],
        )
        anki_deck.add_note(note)

    if skipped:
        print(f"\n[APKG-POI] WARNING: {skipped} POIs skipped (missing overlays).")
        print("           Run:  python scripts/03b_generate_poi_cards.py "
              f"--region {d.region.name} --system {d.poi_classification.name} "
              "--force")

    # ── Write .apkg ────────────────────────────────────────────────────────
    apkg_path = d.output_csv_dir / f"{d.anki_csv_name}.apkg"
    apkg_path.parent.mkdir(parents=True, exist_ok=True)

    package = genanki.Package(anki_deck)
    package.media_files = media_files
    package.write_to_file(str(apkg_path))

    n_notes = len(anki_deck.notes)
    n_cards = n_notes * 2  # 2 templates
    n_media = len(media_files)
    size_mb = apkg_path.stat().st_size / (1024 * 1024)
    print(f"\n[APKG-POI] {deck_title}")
    print(f"[APKG-POI] {n_notes} notes x 2 templates = {n_cards} cards")
    print(f"[APKG-POI] {n_media} media files, {size_mb:.1f} MB")
    print(f"[APKG-POI] -> {apkg_path}")
    print(f"\n  Import in Anki:  File -> Import -> {apkg_path.name}")
    print(f"  Double-tap or pinch to zoom into the map.")


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
