import json, os
from collections import Counter

base = "F:/tiroltourismus/src/data"

# --- Analyze gastro entries ---
gastro_dir = os.path.join(base, "gastro")
gastro_regions = Counter()
gastro_orte = Counter()
gastro_by_region = {}
gastro_data = []

for slug in os.listdir(gastro_dir):
    path = os.path.join(gastro_dir, slug, "index.json")
    if os.path.exists(path):
        with open(path) as f:
            g = json.load(f)
        region = g.get("region", "?")
        ort = g.get("ort", "?")
        gastro_regions[region] += 1
        gastro_orte[ort] += 1
        gastro_by_region.setdefault(region, []).append(g)
        gastro_data.append(g)

print("=== GASTRO REGIONS ===")
for r, c in gastro_regions.most_common():
    print(f"  {r}: {c}")

print("\n=== GASTRO ORTE ===")
for r, c in gastro_orte.most_common():
    print(f"  {r}: {c}")

print(f"\nTotal gastro entries: {len(gastro_data)}")

# --- Analyze accommodations by region ---
unterkuenfte_dir = os.path.join(base, "unterkuenfte")
unterkunft_regions = Counter()
unterkunft_orte = Counter()
unterkunft_by_region = {}

for slug in os.listdir(unterkuenfte_dir):
    path = os.path.join(unterkuenfte_dir, slug, "index.json")
    if os.path.exists(path):
        with open(path) as f:
            u = json.load(f)
        region = u.get("region", "?")
        ort = u.get("ort", "?")
        unterkunft_regions[region] += 1
        unterkunft_orte[ort] += 1
        unterkunft_by_region.setdefault(region, []).append(u)

print("\n=== UNTERKUNFT REGIONS ===")
for r, c in unterkunft_regions.most_common():
    print(f"  {r}: {c}")

print(f"\nTotal unterkunft entries: {sum(unterkunft_regions.values())}")

# --- Identify regions with < 3 gastro entries ---
print("\n=== REGIONS WITH < 3 GASTRO ENTRIES ===")
under_3 = []
for r in sorted(set(list(gastro_regions.keys()) + list(unterkunft_regions.keys()))):
    gc = gastro_regions.get(r, 0)
    uc = unterkunft_regions.get(r, 0)
    if gc < 3:
        print(f"  {r}: {gc} gastro, {uc} accommodations")
        under_3.append(r)

print(f"\nTotal regions under 3 gastro: {len(under_3)}")

# --- Top-10 places with most accommodations but 0 gastro ---
print("\n=== TOP PLACES WITH MANY UNTERKUNFTE BUT 0 GASTRO ===")
orte_with_gastro = set(gastro_orte.keys())
orte_unterkunft_count = Counter()
for slug in os.listdir(unterkuenfte_dir):
    path = os.path.join(unterkuenfte_dir, slug, "index.json")
    if os.path.exists(path):
        with open(path) as f:
            u = json.load(f)
        ort = u.get("ort", "?")
        orte_unterkunft_count[ort] += 1

no_gastro_orte = [(ort, cnt) for ort, cnt in orte_unterkunft_count.most_common() if ort not in orte_with_gastro]
for ort, cnt in no_gastro_orte[:15]:
    print(f"  {ort}: {cnt} accommodations, 0 gastro")

# --- Also show which regions/orte have gastro and how many ---
print("\n=== ALL ORTE WITH GASTRO (for reference) ===")
for o, c in gastro_orte.most_common():
    uc = orte_unterkunft_count.get(o, 0)
    print(f"  {o}: {c} gastro, {uc} accommodations")
