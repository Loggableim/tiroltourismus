#!/usr/bin/env python3
"""Count how many accommodations have valid descriptions."""
import json, os, glob

data_dir = "src/data/unterkuenfte"
entries = glob.glob(os.path.join(data_dir, "*", "index.json"))

total = len(entries)
with_desc = 0
without = 0

for f in sorted(entries):
    d = json.load(open(f, encoding="utf-8"))
    desc = d.get("beschreibung", "")
    if len(desc.strip("<>p/ ")) >= 10:
        with_desc += 1
    else:
        without += 1

print(f"Total: {total}")
print(f"With description: {with_desc}")
print(f"Without description: {without}")
