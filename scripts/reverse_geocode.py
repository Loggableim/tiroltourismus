#!/usr/bin/env python3
"""
Batch reverse geocode missing ort/region from coordinates.
"""
import json, os, glob, re, unicodedata
from collections import defaultdict
import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UNTERKUNFT_DIR = os.path.join(BASE_DIR, 'src', 'data', 'unterkuenfte')
ORTE_DIR = os.path.join(BASE_DIR, 'src', 'data', 'orte')

OVERPAST_API = 'https://overpass.kumi.systems/api/interpreter'

def slugify(text):
    text = unicodedata.normalize('NFKD', text.lower())
    text = text.encode('ascii', 'ignore').decode('ascii')
    return re.sub(r'[^a-z0-9]+', '-', text).strip('-')

# Load orte
ortes = {}
for f in glob.glob(os.path.join(ORTE_DIR, '*', 'index.json')):
    with open(f) as fh:
        d = json.load(fh)
    ortes[d['name'].lower()] = d
    norm = slugify(d['name'])
    ortes[norm] = d

# Find entries with coords but no ort
candidates = []
for f in glob.glob(os.path.join(UNTERKUNFT_DIR, '*', 'index.json')):
    with open(f) as fh:
        d = json.load(fh)
    ort = d.get('ort', '') or ''
    region = d.get('region', '') or ''
    koords = d.get('koordinaten', {})
    lat = koords.get('lat', '')
    lng = koords.get('lng', '')
    if (not ort or not region) and lat and lng:
        try:
            candidates.append((f, d, float(lat), float(lng)))
        except ValueError:
            pass

print(f"Entries needing reverse geocode: {len(candidates)}")

if not candidates:
    print("None found!")
    exit(0)

# Process in batches to reduce API calls
BATCH_SIZE = 50
found = 0
not_found = 0

for batch_start in range(0, len(candidates), BATCH_SIZE):
    batch = candidates[batch_start:batch_start + BATCH_SIZE]
    
    # Build a multi-point reverse geocode query
    queries = []
    for fpath, entry, lat, lng in batch:
        q = f'is_in({lat},{lng});area._[admin_level=8];out tags 1;'
        queries.append(f'node(around:{lat},{lng},200)["place"]["name"];')
    
    # Single query with multiple around searches
    around_parts = []
    for fpath, entry, lat, lng in batch:
        around_parts.append(f'node(around:{lat},{lng},200)["place"~"city|town|village|hamlet"];')
    
    query = f'[out:json][timeout:60];(\n'
    query += '\n'.join(around_parts)
    query += '\n);out tags 5;'
    
    try:
        resp = requests.post(OVERPAST_API, data={'data': query}, timeout=60)
        if resp.status_code == 200:
            results = resp.json().get('elements', [])
            # Map results back to entries
            for elem in results:
                tags = elem.get('tags', {})
                name = tags.get('name', '')
                if not name:
                    continue
                lat_elem = elem.get('lat', 0)
                lon_elem = elem.get('lon', 0)
                # Find the closest entry
                for fpath, entry, lat, lng in batch:
                    dist = ((float(lat) - lat_elem)**2 + (float(lng) - lon_elem)**2)**0.5
                    if dist < 0.05:  # ~5km
                        # Check name against orte
                        name_lower = name.lower().strip()
                        if name_lower in ortes:
                            info = ortes[name_lower]
                            entry['ort'] = info['name']
                            entry['region'] = info['region']
                            if info.get('plz'):
                                entry['plz'] = info['plz']
                            with open(fpath, 'w', encoding='utf-8') as f:
                                json.dump(entry, f, ensure_ascii=False, indent=2)
                            found += 1
                            break
    except Exception as e:
        print(f"  Batch error: {e}")
    
    if (batch_start // BATCH_SIZE) % 5 == 0:
        print(f"  Progress: {batch_start + len(batch)}/{len(candidates)}, found={found}")

# Single-point queries for remaining
print(f"\nFound {found}/{len(candidates)} via batch")
print(f"Remaining: {not_found}")

# Final stats
with_region = 0
for f in glob.glob(os.path.join(UNTERKUNFT_DIR, '*', 'index.json')):
    d = json.load(open(f))
    if d.get('region'):
        with_region += 1

all_entries = len(list(glob.glob(os.path.join(UNTERKUNFT_DIR, '*', 'index.json'))))
print(f"\nTotal with region: {with_region}/{all_entries}")
