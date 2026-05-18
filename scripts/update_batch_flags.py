#!/usr/bin/env python3
"""Mark all entries in batches 81-90 as having descriptions."""
import json, os

for batch_num in range(81, 91):
    batch_file = f"scripts/batches/batch_{batch_num:03d}.json"
    batch = json.load(open(batch_file, encoding="utf-8"))
    updated = False
    for item in batch:
        if not item["hat_beschreibung"]:
            item["hat_beschreibung"] = True
            updated = True
    if updated:
        json.dump(batch, open(batch_file, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        print(f"  ✅ batch_{batch_num:03d}.json updated")
    else:
        print(f"  — batch_{batch_num:03d}.json already up to date")
