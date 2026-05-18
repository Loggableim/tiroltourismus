#!/usr/bin/env python3
"""Check status of batches 31-40."""
import json, os

BATCH_DIR = "scripts/batches"
DATA_DIR = "src/data/unterkuenfte"

for bn in range(31, 41):
    bf = os.path.join(BATCH_DIR, f"batch_{bn:03d}.json")
    data = json.load(open(bf, encoding="utf-8"))
    
    done = 0
    missing = 0
    pending = 0
    
    for item in data:
        slug = item["slug"]
        fp = os.path.join(DATA_DIR, slug, "index.json")
        if not os.path.exists(fp):
            missing += 1
            continue
        entry = json.load(open(fp, encoding="utf-8"))
        has = bool(entry.get("beschreibung","") and len(entry.get("beschreibung","").strip()) >= 10)
        if has:
            done += 1
        else:
            pending += 1
    
    print(f"Batch {bn:03d}: {len(data)} entries, {done} done, {pending} pending, {missing} missing")

# Overall for batches 31-40
total_all = 0
total_done = 0
total_pending = 0
total_missing = 0

for bn in range(31, 41):
    bf = os.path.join(BATCH_DIR, f"batch_{bn:03d}.json")
    data = json.load(open(bf, encoding="utf-8"))
    for item in data:
        total_all += 1
        slug = item["slug"]
        fp = os.path.join(DATA_DIR, slug, "index.json")
        if not os.path.exists(fp):
            total_missing += 1
            continue
        entry = json.load(open(fp, encoding="utf-8"))
        has = bool(entry.get("beschreibung","") and len(entry.get("beschreibung","").strip()) >= 10)
        if has:
            total_done += 1
        else:
            total_pending += 1

print(f"\nBatches 31-40 total: {total_all}")
print(f"Done: {total_done}")
print(f"Pending: {total_pending}")
print(f"Missing: {total_missing}")
