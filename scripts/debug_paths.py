#!/usr/bin/env python3
"""Debug file paths"""
import json, os

batch_file = "scripts/batches/batch_001.json"
data = json.load(open(batch_file, encoding="utf-8"))

for item in data:
    fp = item["filepath"]
    exists = os.path.exists(fp)
    print(f"  {item['name']:40s} | path={repr(fp):70s} | exists={exists}")
    if exists:
        fsize = os.path.getsize(fp)
        print(f"    size={fsize}")
