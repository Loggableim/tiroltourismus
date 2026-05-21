#!/usr/bin/env python3
"""Quick spot check on the delegate-repaired entries + overall stats."""
import json, os, glob

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "data", "unterkuenfte")

# Check the 4 repaired entries
repaired = [
    "bauernhof-ferienwohnung-hecherhof",
    "bauernhof-ferienwohnung-mayrhof", 
    "bauernhof-ferienwohnung-schwoicher-bauer",
    "bauernhof-maisfeld",
]

print("=== Repaired entries ===")
for slug in repaired:
    fp = os.path.join(DATA, slug, "index.json")
    e = json.load(open(fp))
    d = e.get("beschreibung", "")
    print(f"{slug}: {len(d)} chars — {d[:100]}...")
    print(f"  Tags: {e.get('tags',[])}")
    print()

# Overall stats from our batches
stats_desc_true = 0
stats_desc_false = 0
stats_no_file = 0
for b in range(21, 31):
    bf = os.path.join(os.path.dirname(os.path.abspath(__file__)), "batches", f"batch_{b:03d}.json")
    batch = json.load(open(bf))
    for item in batch:
        fp = item["filepath"]
        if not os.path.exists(fp):
            stats_no_file += 1
            print(f"MISSING: {item['slug']} ({item['name']})")
            continue
        e = json.load(open(fp))
        desc = e.get("beschreibung", "")
        if len(desc.strip("<>p/ ")) >= 10:
            stats_desc_true += 1
        else:
            stats_desc_false += 1
            print(f"  Still missing desc: {item['slug']} ({len(desc)} chars: {repr(desc[:50])})")

print(f"\n=== Final Batch 21-30 Stats ===")
print(f"With description: {stats_desc_true}")
print(f"Without description: {stats_desc_false}")
print(f"File not found: {stats_no_file}")
print(f"Total: {stats_desc_true + stats_desc_false + stats_no_file}")
