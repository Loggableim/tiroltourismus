#!/usr/bin/env python3
"""Check how many entries need descriptions."""
import json, os

DATA_DIR = "src/data/unterkuenfte"
entries = []
for f in sorted(os.listdir(DATA_DIR)):
    fp = os.path.join(DATA_DIR, f, "index.json")
    if os.path.exists(fp):
        data = json.load(open(fp, encoding="utf-8"))
        has_desc = bool(data.get("beschreibung","") and len(data.get("beschreibung","").strip()) >= 10)
        entries.append((f, data.get("name","?"), has_desc))

print(f"Total: {len(entries)} entries")
print(f"Need desc: {sum(1 for _,_,d in entries if not d)}")
print(f"Have desc: {sum(1 for _,_,d in entries if d)}")
