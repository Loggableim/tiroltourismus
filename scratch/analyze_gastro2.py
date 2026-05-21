import json, os
from collections import Counter

base = "F:/tiroltourismus/src/data"
unterkuenfte_dir = os.path.join(base, "unterkuenfte")

# Get all gastro orte (normalized)
gastro_orte_set = set()
for slug in os.listdir(os.path.join(base, "gastro")):
    path = os.path.join(base, "gastro", slug, "index.json")
    if os.path.exists(path):
        with open(path) as f:
            g = json.load(f)
        gastro_orte_set.add(g.get("ort","").strip().lower())

print("=== GASTRO ORTE (normalized) ===")
for o in sorted(gastro_orte_set):
    print(f"  {o}")

# Get all unique ort names from accommodations with counts
unterkunft_orte = Counter()
unterkunft_orte_detail = {}  # ort -> list of slugs showing variations

for slug in os.listdir(unterkuenfte_dir):
    path = os.path.join(unterkuenfte_dir, slug, "index.json")
    if os.path.exists(path):
        with open(path) as f:
            u = json.load(f)
        ort_raw = u.get("ort", "")
        if ort_raw:
            unterkunft_orte[ort_raw] += 1
            unterkunft_orte_detail.setdefault(ort_raw.strip().lower(), []).append((ort_raw, slug))

# Check for variations
print("\n=== ORT NAME VARIATIONS (potential dupes) ===")
seen = {}
for slug in os.listdir(unterkuenfte_dir):
    path = os.path.join(unterkuenfte_dir, slug, "index.json")
    if os.path.exists(path):
        with open(path) as f:
            u = json.load(f)
        ort_raw = u.get("ort", "")
        if ort_raw:
            key = ort_raw.strip().lower()
            seen.setdefault(key, set()).add(ort_raw)

for key, variants in sorted(seen.items()):
    if len(variants) > 1:
        print(f"  '{key}': {variants}")

# Also check ort-region pairs to see which regions have which ort
print("\n=== ORTE WITH ORT/REGION MAPPING (sample) ===")
for slug in os.listdir(unterkuenfte_dir):
    path = os.path.join(unterkuenfte_dir, slug, "index.json")
    if os.path.exists(path):
        with open(path) as f:
            u = json.load(f)
        ort = u.get("ort", "")
        region = u.get("region", "")
        if ort and region:
            print(f"  {ort} -> region: {region}")
            break  # just one sample

# Let's map what gastro covers vs what's needed
print("\n=== DETAILED GASTRO COVERAGE ===")
for r, cnt in sorted(unterkunft_orte.most_common(30)):
    rl = r.strip().lower()
    has = "YES" if rl in gastro_orte_set else " NO"
    print(f"  {has} | {cnt:3d} accommodations | {r}")
