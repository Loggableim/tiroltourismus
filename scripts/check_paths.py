#!/usr/bin/env python3
"""Check file paths from batch files."""
import json, os

for bn in [61, 65]:
    batch = json.load(open(f"scripts/batches/batch_{bn:03d}.json"))
    for item in batch:
        fp = item["filepath"]
        exists = os.path.exists(fp)
        print(f"  {item['name']:40s} slug={item['slug']:40s} exists={exists}")
