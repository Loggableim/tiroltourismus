#!/usr/bin/env python3
"""Add camping data from OSM."""
import json, os, re, unicodedata, glob
import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UNTERKUNFT_DIR = os.path.join(BASE_DIR, 'src', 'data', 'unterkuenfte')
ORTE_DIR = os.path.join(BASE_DIR, 'src', 'data', 'orte')
OVERPAST_API = 'https://overpass.kumi.systems/api/interpreter'

# Load orte
ortes = {}
for f in glob.glob(os.path.join(ORTE_DIR, '*', 'index.json')):
    with open(f) as fh:
        d = json.load(fh)
    ortes[d['name'].lower()] = d

def slugify(text):
    text = unicodedata.normalize('NFKD', text.lower())
    text = text.encode('ascii', 'ignore').decode('ascii')
    return re.sub(r'[^a-z0-9]+', '-', text).strip('-')

def find_region(ort_name, plz):
    if not ort_name:
        return '', '', ''
    key = ort_name.lower().strip()
    if key in ortes:
        info = ortes[key]
        return info['region'], info['name'], info.get('plz', '')
    norm = slugify(ort_name)
    if norm in ortes:
        info = ortes[norm]
        return info['region'], info['name'], info.get('plz', '')
    return '', ort_name, plz or ''

# Query camping
bbox = "47.0,10.0,48.0,13.0"
query = f'[out:json][timeout:60];(node["tourism"="camp_site"]({bbox});way["tourism"="camp_site"]({bbox}););out center body 500;'
resp = requests.post(OVERPAST_API, data={'data': query}, timeout=90)
camping_data = resp.json()

# Process existing slugs to avoid duplicates
existing_slugs = set()
for f in glob.glob(os.path.join(UNTERKUNFT_DIR, '*', 'index.json')):
    slug = os.path.basename(os.path.dirname(f))
    existing_slugs.add(slug)

added = 0
for elem in camping_data.get('elements', []):
    tags = elem.get('tags', {})
    name = tags.get('name', '').strip()
    if not name or len(name) < 3:
        continue
    
    lat = elem.get('lat')
    lng = elem.get('lon')
    if lat is None and 'center' in elem:
        lat = elem['center'].get('lat')
        lng = elem['center'].get('lon')
    if lat is None:
        continue
    
    addr_city = tags.get('addr:city', '') or tags.get('addr:locality', '')
    addr_postcode = tags.get('addr:postcode', '')
    
    region, ort_name, plz = find_region(addr_city, addr_postcode)
    
    slug = slugify(name)
    n = 1
    while slug in existing_slugs:
        n += 1
        slug = f"{slugify(name)}-{n}"
    existing_slugs.add(slug)
    
    entry = {
        'name': name, 'slug': slug, 'typ': 'camping',
        'sterne': None, 'preis_ab': None,
        'ort': ort_name or addr_city or '',
        'region': region or '',
        'plz': plz or addr_postcode or '',
        'adresse': '',
        'telefon': tags.get('phone') or tags.get('contact:phone') or None,
        'email': tags.get('email') or tags.get('contact:email') or None,
        'webseite': tags.get('website') or tags.get('contact:website') or None,
        'beschreibung': '',
        'ausstattung': [],
        'tags': ['camping', 'natur', 'outdoor'],
        'tier': 'basic',
        'koordinaten': {'lat': str(lat), 'lng': str(lng)},
        'status': 'published',
    }
    
    dir_path = os.path.join(UNTERKUNFT_DIR, slug)
    os.makedirs(dir_path, exist_ok=True)
    with open(os.path.join(dir_path, 'index.json'), 'w', encoding='utf-8') as f:
        json.dump(entry, f, ensure_ascii=False, indent=2)
    added += 1

print(f"Added {added} camping entries")

# Final count
total = len(list(glob.glob(os.path.join(UNTERKUNFT_DIR, '*', 'index.json'))))
print(f"Total entries: {total}")

# Type counts
typ_counts = {}
for f in glob.glob(os.path.join(UNTERKUNFT_DIR, '*', 'index.json')):
    d = json.load(open(f))
    t = d.get('typ', '?')
    typ_counts[t] = typ_counts.get(t, 0) + 1
print("Types:", dict(typ_counts))
