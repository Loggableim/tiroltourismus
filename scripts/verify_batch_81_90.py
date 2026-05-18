#!/usr/bin/env python3
"""Verify that all 60 entries in batches 81-90 have descriptions."""
import json, os

DATA_DIR = "src/data/unterkuenfte"

bad = 0
good = 0
for batch_num in range(81, 91):
    batch_file = f"scripts/batches/batch_{batch_num:03d}.json"
    batch = json.load(open(batch_file))
    for item in batch:
        slug = item["slug"]
        path = os.path.join(DATA_DIR, slug, "index.json")
        if os.path.exists(path):
            data = json.load(open(path, encoding="utf-8"))
            desc = data.get("beschreibung", "")
            needs = (not desc or len(desc.strip()) < 10)
            if needs:
                print(f"  ❌ {slug} (batch {batch_num}): NO description")
                bad += 1
            else:
                good += 1
        else:
            print(f"  ❌ {slug} (batch {batch_num}): FILE NOT FOUND")
            bad += 1

print(f"\n✅ {good} entries enriched, ❌ {bad} still need work")
