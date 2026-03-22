"""Check what models/card types are in the AVE84 APKG."""
import zipfile, json, sqlite3, tempfile, os

apkg = "output/ostalpen_ave84/anki_ostalpen_ave84.apkg"
with zipfile.ZipFile(apkg) as z:
    tmp_fd, tmp = tempfile.mkstemp(suffix=".db")
    with os.fdopen(tmp_fd, "wb") as f:
        f.write(z.read("collection.anki2"))

conn = sqlite3.connect(tmp)
row = conn.execute("SELECT models FROM col").fetchone()
models = json.loads(row[0])

print("=== Models in APKG ===")
for mid, m in models.items():
    fields = [f["name"] for f in m["flds"]]
    print(f"\nModel ID: {mid}")
    print(f"Model Name: {m['name']}")
    print(f"Fields ({len(fields)}): {fields}")
    for t in m["tmpls"]:
        print(f"  Template: {t['name']}")
        front_preview = t["qfmt"][:300].replace("\n", " ")
        print(f"  Front: {front_preview}")

print("\n=== Notes per model ===")
notes = conn.execute("SELECT mid, COUNT(*) FROM notes GROUP BY mid").fetchall()
for mid, cnt in notes:
    mname = models.get(str(mid), {}).get("name", "???")
    print(f"  {mname} (id={mid}): {cnt} notes")

# Decks
row2 = conn.execute("SELECT decks FROM col").fetchone()
decks = json.loads(row2[0])
print("\n=== Decks ===")
for did, dk in decks.items():
    print(f"  {dk['name']} (id={did})")

conn.close()
os.unlink(tmp)
