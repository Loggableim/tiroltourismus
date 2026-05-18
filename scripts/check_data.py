#!/usr/bin/env python
"""Quick check of existing data structure."""
import json, os, glob

base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Build ort lookup
ortes = {}
for f in glob.glob(os.path.join(base, 'src', 'data', 'orte', '*', 'index.json')):
    with open(f) as fh:
        d = json.load(fh)
    ortes[d['name'].lower()] = d
print(f'Total orte: {len(ortes)}')
regions = set(d['region'] for d in ortes.values())
print(f'Regions ({len(regions)}): {sorted(regions)}')

# Check existing unterkunfte & what regions they use
existing = {}
for f in glob.glob(os.path.join(base, 'src', 'data', 'unterkuenfte', '*', 'index.json')):
    with open(f) as fh:
        d = json.load(fh)
    slug = d.get('slug', os.path.basename(os.path.dirname(f)))
    existing[slug] = d
print(f'Existing unterkuenfte: {len(existing)}')

# Check what regions the existing ones use
regions_used = set()
has_coords = 0
for s, d in existing.items():
    slug = d.get('slug', os.path.basename(os.path.dirname(f)))
    if 'region' in d:
        regions_used.add(d['region'])
    if 'koordinaten' in d:
        has_coords += 1
print(f'Regions used by unterkuenfte: {sorted(regions_used)}')
print(f'With coordinates: {has_coords}/{len(existing)}')

# Test ort lookup for some OSM-matched names
test_names = ['neustift im stubaital', 'kaunertal', 'fügen', 'lienz', 'innsbruck', 'kitzbühel']
for t in test_names:
    key = t.lower()
    if key in ortes:
        print(f'  {t:30s} -> region={ortes[key]["region"]}')
    else:
        alt = key.replace('\u00fc','ue').replace('\u00f6','oe').replace('\u00e4','ae').replace('\u00df','ss')
        if alt in ortes:
            print(f'  {t:30s} -> (as {alt}) -> region={ortes[alt]["region"]}')
        else:
            # check if any ort key contains the name
            matches = [k for k in ortes if t.lower()[:8] in k]
            if matches:
                print(f'  {t:30s} -> partial matches: {matches[:3]}')
            else:
                print(f'  {t:30s} -> NOT FOUND')
