#!/usr/bin/env python3
"""Count entries with descriptions."""
import json, os

DATA = "src/data/unterkuenfte"
count = 0
total = 0
for f in sorted(os.listdir(DATA)):
    fp = os.path.join(DATA, f, "index.json")
    if os.path.exists(fp):
        total += 1
        data = json.load(open(fp, encoding="utf-8"))
        has = bool(data.get("beschreibung","") and len(data.get("beschreibung","").strip()) >= 10)
        if has:
            count += 1

print(f"Total: {total}")
print(f"Have description: {count}")
print(f"Need description: {total - count}")
