#!/usr/bin/env python3
import json

# Check entries from each batch
slugs_to_check = [
    ("batch 021", "bauernhof-ferienwohnung-grasweberhof"),
    ("batch 021", "bauernhof-ferienwohnung-hecherhof"),
    ("batch 025", "bauernhof-lechnerbauer"),
    ("batch 026", "bauernhof-stockl"),
    ("batch 028", "berggasthof-moosbauer"),
    ("batch 030", "best-western-plus-hotel-alpenrose"),
]

for batch, slug in slugs_to_check:
    try:
        e = json.load(open(f"src/data/unterkuenfte/{slug}/index.json"))
        d = e.get("beschreibung", "")
        print(f"[{batch}] {slug}: desc len={len(d)}")
        if len(d) > 10:
            print(f"  Content: {d[:150]}...")
        else:
            print(f"  NO DESCRIPTION (or too short)")
        print(f"  Tags: {e.get('tags', [])}")
        print(f"  Ausstattung: {e.get('ausstattung', [])}")
        print()
    except Exception as ex:
        print(f"[{batch}] {slug}: ERROR: {ex}")
        print()
