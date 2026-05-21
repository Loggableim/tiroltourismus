#!/usr/bin/env python3
"""Quick stats after adding camping."""
import json, os, glob
from collections import defaultdict

base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
unterkunft_dir = os.path.join(base, 'src', 'data', 'unterkuenfte')

typ_counts = defaultdict(int)
region_counts = defaultdict(int)
no_region = 0

for f in glob.glob(os.path.join(unterkunft_dir, '*', 'index.json')):
    d = json.load(open(f))
    typ_counts[d.get('typ', '?')] += 1
    if d.get('region'):
        region_counts[d['region']] += 1
    else:
        no_region += 1

print("Types:")
for t, c in sorted(typ_counts.items(), key=lambda x: -x[1]):
    print(f"  {t}: {c}")

print(f"\nWith region: {sum(region_counts.values())}")
print(f"No region: {no_region}")
print(f"\nRegion distribution:")
for r, c in sorted(region_counts.items(), key=lambda x: -x[1]):
    print(f"  {r}: {c}")
