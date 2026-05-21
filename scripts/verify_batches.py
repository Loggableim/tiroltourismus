#!/usr/bin/env python3
"""Verify batch 21-30 entries have descriptions."""
import json

batches = list(range(21, 31))
total_entries = 0
with_desc = 0
missing = []

for b in batches:
    batch_file = f"scripts/batches/batch_{b:03d}.json"
    try:
        batch = json.load(open(batch_file))
    except FileNotFoundError:
        print(f"❌ {batch_file} not found")
        continue
    
    for item in batch:
        total_entries += 1
        fp = item["filepath"]
        slug = item["slug"]
        try:
            entry = json.load(open(fp))
            desc = entry.get("beschreibung", "")
            tags = entry.get("tags", [])
            ausstattung = entry.get("ausstattung", [])
            tier = entry.get("tier", "none")
            
            if len(desc) > 10:
                with_desc += 1
            else:
                missing.append(f"  ❌ {slug}: no description")
            
            # Check other fields
            if not tags:
                missing.append(f"  ⚠️ {slug}: no tags")
            if not ausstattung:
                missing.append(f"  ⚠️ {slug}: no ausstattung")
            if tier == "none":
                missing.append(f"  ⚠️ {slug}: no tier")
                
        except FileNotFoundError:
            missing.append(f"  ❌ {slug}: file not found at {fp}")

print(f"\n=== Batch 21-30 Summary ===")
print(f"Total entries: {total_entries}")
print(f"With description: {with_desc}")
print(f"Issues: {len(missing)}")
for m in missing:
    print(m)
print(f"\nSuccess rate: {with_desc}/{total_entries} ({100*with_desc//total_entries}%)")
