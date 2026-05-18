#!/usr/bin/env python3
"""Summary of batch processing results"""
import json, os

total_enriched = 0
total_missing = 0
total_existing = 0

for i in range(1, 11):
    fn = f"scripts/batches/batch_{i:03d}.json"
    data = json.load(open(fn, encoding="utf-8"))
    batch_enriched = 0
    batch_missing = 0
    batch_existing = 0
    
    for item in data:
        fp = item["filepath"]
        exists = os.path.exists(fp)
        if exists:
            entry = json.load(open(fp, encoding="utf-8"))
            has_desc = bool(entry.get("beschreibung") and len(entry["beschreibung"].strip()) > 10)
            if has_desc:
                batch_enriched += 1
            else:
                batch_existing += 1
        else:
            batch_missing += 1
    
    print(f"batch_{i:03d}: {len(data)} entries | enriched={batch_enriched} | file_missing={batch_missing} | no_desc={batch_existing}")
    total_enriched += batch_enriched
    total_missing += batch_missing
    total_existing += batch_existing

print(f"\nTOTAL across 10 batches: {total_enriched + total_missing + total_existing}")
print(f"  Enriched (have description): {total_enriched}")
print(f"  File not found (missing data): {total_missing}")
print(f"  File exists but no description: {total_existing}")
