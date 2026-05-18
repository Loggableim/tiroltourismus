#!/usr/bin/env python3
"""Analyze unterkunft data quality after scraping."""
import json, os, glob, unicodedata

base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
unterkunft_dir = os.path.join(base, 'src', 'data', 'unterkuenfte')
orte_dir = os.path.join(base, 'src', 'data', 'orte')

# Load orte for fuzzy matching
ortes = {}
for f in glob.glob(os.path.join(orte_dir, '*', 'index.json')):
    with open(f) as fh:
        d = json.load(fh)
    ortes[d['name'].lower()] = d
    norm = unicodedata.normalize('NFKD', d['name'].lower())
    norm = norm.encode('ascii', 'ignore').decode('ascii').strip()
    if norm:
        ortes[norm] = d

# Analyze
no_region = []
has_region = []
no_ort = []
typ_counts = {}

files = list(glob.glob(os.path.join(unterkunft_dir, '*', 'index.json')))
print(f"Total entries: {len(files)}")
print()

for f in files:
    with open(f) as fh:
        d = json.load(fh)
    t = d.get('typ', '?')
    typ_counts[t] = typ_counts.get(t, 0) + 1
    
    if d.get('region'):
        has_region.append(d)
    else:
        no_region.append(d)
    if not d.get('ort'):
        no_ort.append(d)

print(f"With region: {len(has_region)}")
print(f"Without region: {len(no_region)}")
print(f"Without ort: {no_ort}")
print()
print("By type:")
for t, c in sorted(typ_counts.items(), key=lambda x: -x[1]):
    print(f"  {t}: {c}")

print()
print("--- 20 samples without region (ort field focus) ---")
for d in no_region[:20]:
    ort = d.get('ort', '')
    addr = d.get('adresse', '')
    plz = d.get('plz', '')
    name = d.get('name', '')
    # Check if ort matches any orte
    ort_lower = ort.lower().strip()
    matches = [n for n in ortes if (ort_lower and (ort_lower[:5] in n or n[:5] in ort_lower))]
    print(f"  name={name[:35]:35s} ort={ort:25s} plz={plz} addr={addr[:30]}")

print()
print("--- All OSM orte values mentioned ---")
ort_values = {}
for d in no_region:
    ort = d.get('ort', '')
    if ort:
        ort_values[ort] = ort_values.get(ort, 0) + 1
for ort, count in sorted(ort_values.items(), key=lambda x: -x[1])[:30]:
    print(f"  {ort:30s} ({count}x)")
