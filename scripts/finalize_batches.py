#!/usr/bin/env python3
"""Update batch files with current hat_beschreibung status and generate final report"""
import json, os, glob

base = "src/data/unterkuenfte"
all_slugs = set(os.path.basename(d) for d in glob.glob(f"{base}/*"))

total_enriched = 0
total_missing = 0
missing_details = []

for i in range(1, 11):
    fn = f"scripts/batches/batch_{i:03d}.json"
    data = json.load(open(fn, encoding="utf-8"))
    
    for item in data:
        fp = item["filepath"]
        exists = os.path.exists(fp)
        has_desc = False
        if exists:
            entry = json.load(open(fp, encoding="utf-8"))
            desc = entry.get("beschreibung", "")
            has_desc = bool(desc and len(desc.strip()) > 10)
            item["hat_beschreibung"] = has_desc
        
        if has_desc:
            total_enriched += 1
        elif not exists:
            total_missing += 1
            missing_details.append(f"  batch_{i:03d}: {item['name']} ({item['ort']}, {item['typ']})")
    
    # Write updated batch file
    json.dump(data, open(fn, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

print(f"✅ Batch files updated")
print(f"\n=== FINAL SUMMARY ===")
print(f"Total entries in batches 1-10: 60")
print(f"Successfully enriched: {total_enriched}")
print(f"Missing data files (not yet in system): {total_missing}")
print(f"\nMissing entries (data not yet created):")
for m in missing_details:
    print(m)

# Also list what was enriched per batch
for i in range(1, 11):
    fn = f"scripts/batches/batch_{i:03d}.json"
    data = json.load(open(fn, encoding="utf-8"))
    e = sum(1 for x in data if x["hat_beschreibung"])
    m = sum(1 for x in data if not x["hat_beschreibung"] and not os.path.exists(x["filepath"]))
    print(f"  batch_{i:03d}: {e} enriched, {m} missing files, {len(data)-e-m} skipped")
