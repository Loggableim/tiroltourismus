import json, os
from collections import Counter, defaultdict
import re

base = "F:/tiroltourismus/src/data"
unterkuenfte_dir = os.path.join(base, "unterkuenfte")

# Normalize function for ort names
def normalize(s):
    s = s.strip().lower()
    # Remove common suffixes that may cause mismatches
    s = re.sub(r'\s+in\s+tirol$', '', s)
    s = re.sub(r'\s+am\s+arlberg$', '', s)
    s = re.sub(r'\s+im\s+stubaital$', '', s)
    s = re.sub(r'\s+am\s+wilden\s+kaiser$', '', s)
    s = re.sub(r'\s+in\s+tirol$', '', s)
    return s.strip()

# Get gastro orte (normalized)
gastro_data = {}
for slug in os.listdir(os.path.join(base, "gastro")):
    path = os.path.join(base, "gastro", slug, "index.json")
    if os.path.exists(path):
        with open(path) as f:
            g = json.load(f)
        n = normalize(g.get("ort",""))
        gastro_data[n] = g

print("=== GASTRO ORTE (normalized) ===")
for o in sorted(gastro_data.keys()):
    print(f"  {o}")

# Count accommodations per normalized ort
unterkunft_by_ort = defaultdict(list)
region_by_ort = {}

for slug in os.listdir(unterkuenfte_dir):
    path = os.path.join(unterkuenfte_dir, slug, "index.json")
    if os.path.exists(path):
        with open(path) as f:
            u = json.load(f)
        ort_raw = u.get("ort", "")
        if ort_raw:
            n = normalize(ort_raw)
            unterkunft_by_ort[n].append(u)
            if u.get("region"):
                region_by_ort[n] = u.get("region")

# Top places with most accommodations but 0 gastro (after normalization)
print("\n=== TOP PLACES WITH MOST UNTERKUNFTE BUT 0 GASTRO (normalized) ===")
no_gastro_orte = [(ort, len(entries), region_by_ort.get(ort, "?")) 
                  for ort, entries in sorted(unterkunft_by_ort.items(), key=lambda x: -len(x[1]))
                  if ort not in gastro_data]

for ort, cnt, reg in no_gastro_orte[:15]:
    print(f"  {cnt:3d} accommodations | region: {reg:15s} | {ort}")

# Also show all regions and their gastro/accommodation counts, properly
print("\n=== ALL REGIONS WITH DETAILS ===")
accom_by_region = Counter()
gastro_by_region = Counter()

for slug in os.listdir(unterkuenfte_dir):
    path = os.path.join(unterkuenfte_dir, slug, "index.json")
    if os.path.exists(path):
        with open(path) as f:
            u = json.load(f)
        region = u.get("region", "?leer?")
        accom_by_region[region] += 1

for slug in os.listdir(os.path.join(base, "gastro")):
    path = os.path.join(base, "gastro", slug, "index.json")
    if os.path.exists(path):
        with open(path) as f:
            g = json.load(f)
        region = g.get("region", "?leer?")
        gastro_by_region[region] += 1

all_regions = sorted(set(list(accom_by_region.keys()) + list(gastro_by_region.keys())))
for r in all_regions:
    ac = accom_by_region.get(r, 0)
    gc = gastro_by_region.get(r, 0)
    under = " <-- UNTER 3!" if gc < 3 and ac > 0 else ""
    print(f"  {r:20s} | Gastro: {gc:2d} | Unterkünfte: {ac:4d}{under}")

# Let's also check the empty-region accommodations
print("\n=== SAMPLE OF EMPTY-REGION ACCOMMODATIONS (first 10) ===")
count_empty = 0
for slug in os.listdir(unterkuenfte_dir):
    path = os.path.join(unterkuenfte_dir, slug, "index.json")
    if os.path.exists(path):
        with open(path) as f:
            u = json.load(f)
        if not u.get("region"):
            print(f"  {slug}: ort={u.get('ort','?')}, typ={u.get('typ','?')}")
            count_empty += 1
            if count_empty >= 10:
                break

print(f"\nTotal empty-region accommodations: {accom_by_region.get('?leer?', 0)}")

# Check if "Neustift" gastro ort overlaps with "Neustift im Stubaital" accommodations
print("\n=== SPECIFIC CHECK: 'neustift' vs 'neustift im stubaital' ===")
print(f"  Gastro has 'neustift': {'neustift' in gastro_data}")
neustift_accoms = unterkunft_by_ort.get('neustift im stubaital', [])
print(f"  Accommodations with 'neustift im stubaital': {len(neustift_accoms)}")
for u in neustift_accoms[:3]:
    print(f"    - {u.get('name','?')} (region: {u.get('region','?')})")

# Check St. Anton
print("\n=== SPECIFIC CHECK: 'st. anton' ===")
print(f"  Gastro has 'st. anton': {'st. anton' in gastro_data}")
anton_accoms = unterkunft_by_ort.get('st. anton am arlberg', [])
print(f"  Accommodations with 'st. anton am arlberg': {len(anton_accoms)}")
for u in anton_accoms[:3]:
    print(f"    - {u.get('name','?')} (region: {u.get('region','?')})")
