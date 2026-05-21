#!/usr/bin/env python3
"""Check if batch file paths actually exist."""
import json, os

for batch_num in [41, 42, 43, 44, 45, 46, 47, 48, 49, 50]:
    path = f"scripts/batches/batch_{batch_num:03d}.json"
    if not os.path.exists(path):
        print(f"Batch {batch_num}: file not found")
        continue
    data = json.load(open(path, encoding="utf-8"))
    found = 0
    missing = 0
    for item in data:
        fp = item["filepath"]
        if os.path.exists(fp):
            found += 1
        else:
            missing += 1
            print(f"  MISSING: {item['name']} ({item['slug']})")
    print(f"Batch {batch_num}: {found} found, {missing} missing")
