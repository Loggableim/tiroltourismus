#!/usr/bin/env python
"""Check which batch entries have missing data directories."""
import json, os

data_dir = "F:/tiroltourismus/src/data/unterkuenfte"
existing = {d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))}

all_missing = {}
for bn in range(131, 141):
    batch_file = f"F:/tiroltourismus/scripts/batches/batch_{bn}.json"
    if not os.path.exists(batch_file):
        continue
    batch = json.load(open(batch_file))
    missing = [e for e in batch if e["slug"] not in existing]
    if missing:
        all_missing[bn] = [(m["slug"], m["name"]) for m in missing]

for bn, items in sorted(all_missing.items()):
    print(f"Batch {bn}: {len(items)} missing directories:")
    for slug, name in items:
        print(f"  - {slug} ({name})")

if not all_missing:
    print("All directories exist!")
