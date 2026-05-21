#!/usr/bin/env python3
"""Verify specific batch entries."""
import json, os, sys, glob

# Collect slugs from batches 41-44
slugs = set()
for batch_num in [41, 42, 43, 44]:
    path = f"scripts/batches/batch_{batch_num:03d}.json"
    data = json.load(open(path, encoding="utf-8"))
    for item in data:
        slugs.add(item["slug"])

print(f"Checking {len(slugs)} entries from batches 41-44:")
ok = 0
empty = 0
not_found = 0
for slug in sorted(slugs):
    path = f"src/data/unterkuenfte/{slug}/index.json"
    if not os.path.exists(path):
        print(f"  ❌ NOT FOUND: {slug}")
        not_found += 1
        continue
    d = json.load(open(path, encoding="utf-8"))
    desc = d.get("beschreibung", "")
    has_real_desc = len(desc.strip("<>p/ ")) >= 10
    if has_real_desc:
        ok += 1
    else:
        empty += 1
        print(f"  ❌ EMPTY: {d.get('name','?')} ({slug}) desc='{desc[:60]}'")

print(f"\n✅ Valid: {ok}  |  ❌ Empty: {empty}  |  ❌ Not found: {not_found}")
