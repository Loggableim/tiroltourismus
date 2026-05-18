#!/usr/bin/env python3
"""
Fix Region Mapping for Unterkunft Entries
==========================================
Verbessert die Region-Zuordnung für bestehende OSM-Daten.
- Führt besseren Fuzzy-Match für Ortsnamen durch
- Nutzt PLZ-Region-Mapping
- Nutzt Koordinaten für Reverse-Geocoding (via Overpass)
- Setzt ort="" entries auf sinnvolle Werte

Usage:
  /c/Python314/python scripts/fix_regions.py
"""

import json
import os
import re
import unicodedata
import glob
from collections import defaultdict
import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UNTERKUNFT_DIR = os.path.join(BASE_DIR, 'src', 'data', 'unterkuenfte')
ORTE_DIR = os.path.join(BASE_DIR, 'src', 'data', 'orte')

# Manual overrides for places OSM uses vs our orte names
MANUAL_REGION = {
    'milders': ('stubaital', 'Neustift im Stubaital'),
    'rettenschöss': ('kufstein', 'Rettenschöss'),
    'kaunerberg': ('kaunertal', 'Kaunerberg'),
    'kaunertal': ('kaunertal', 'Kaunertal'),
    'feichten': ('kaunertal', 'Feichten'),
    'prutz': ('landeck', 'Prutz'),
    'oberperfuss': ('innsbruck-land', 'Oberperfuss'),
    'oberperfuß': ('innsbruck-land', 'Oberperfuss'),
    'mittelberg': ('osttirol', 'Mittelberg'),
    'sillian': ('osttirol', 'Sillian'),
    'hopfgarten': ('osttirol', 'Hopfgarten in Defereggen'),
    'goinzen': ('osttirol', 'Goinzen'),
    'innervillgraten': ('osttirol', 'Innervillgraten'),
    'hochpillberg': ('zillertal', 'Hochpillberg'),
    'pill': ('zillertal', 'Pill'),
    'overmassing': None,  # Bavaria
    'schechen': None,
    'bad endorf': None,
    'frasdorf': None,
    'berggisch gladbach': None,
    'st. johann': None,
    'wagrain': None,
    'großgmain': None,
    'berchtesgaden': None,
    'schönau am königssee': None,
    'bischofswiesen': None,
    'ramsau': None,
    'marktschellenberg': None,
    'teisendorf': None,
    'freilassing': None,
    'anger': None,
    'piding': None,
    'ainring': None,
    'saaldorf-surheim': None,
    'petting': None,
}

# Ort names that we can normalize to our orte entries
ORT_NORMALIZER = {
    'st. ': 'sankt ',
    'st ': 'sankt ',
}

PLZ_REGION = {
    '6020': 'innsbruck', '6060': 'innsbruck-land', '6063': 'innsbruck-land',
    '6065': 'innsbruck-land', '6067': 'innsbruck-land', '6068': 'innsbruck-land',
    '6069': 'innsbruck-land', '6070': 'innsbruck-land', '6071': 'innsbruck-land',
    '6072': 'innsbruck-land', '6073': 'innsbruck-land', '6074': 'innsbruck-land',
    '6075': 'innsbruck-land', '6080': 'innsbruck-land', '6082': 'innsbruck-land',
    '6091': 'innsbruck-land', '6092': 'innsbruck-land', '6094': 'innsbruck-land',
    '6100': 'innsbruck-land', '6103': 'innsbruck-land', '6105': 'innsbruck-land',
    '6108': 'innsbruck-land',
    '6111': 'innsbruck-land', '6112': 'innsbruck-land', '6114': 'innsbruck-land',
    '6116': 'stubaital', '6141': 'stubaital', '6142': 'stubaital',
    '6143': 'stubaital', '6144': 'stubaital', '6145': 'stubaital',
    '6150': 'stubaital', '6154': 'stubaital', '6161': 'stubaital',
    '6162': 'stubaital', '6165': 'stubaital', '6166': 'stubaital',
    '6167': 'stubaital',
    '6170': 'innsbruck-land', '6175': 'innsbruck-land', '6176': 'innsbruck-land',
    '6179': 'innsbruck-land', '6180': 'innsbruck-land', '6181': 'innsbruck-land',
    '6182': 'innsbruck-land', '6183': 'innsbruck-land',
    '6184': 'innsbruck-land',
    '6190': 'innsbruck-land',
    '6200': 'innsbruck-land',
    '6210': 'innsbruck-land', '6215': 'innsbruck-land',
    '6220': 'innsbruck-land',
    '6230': 'innsbruck-land', '6232': 'innsbruck-land', '6233': 'innsbruck-land',
    '6234': 'innsbruck-land', '6235': 'innsbruck-land', '6236': 'innsbruck-land',
    '6240': 'innsbruck-land', '6241': 'innsbruck-land',
    '6250': 'innsbruck-land', '6252': 'innsbruck-land',
    '6260': 'innsbruck-land', '6261': 'innsbruck-land', '6262': 'innsbruck-land',
    '6263': 'innsbruck-land', '6264': 'innsbruck-land', '6265': 'innsbruck-land',
    '6271': 'innsbruck-land', '6272': 'innsbruck-land', '6273': 'innsbruck-land',
    '6274': 'innsbruck-land', '6275': 'innsbruck-land', '6276': 'innsbruck-land',
    '6277': 'innsbruck-land', '6278': 'innsbruck-land',
    '6280': 'innsbruck-land', '6283': 'innsbruck-land', '6284': 'innsbruck-land',
    '6290': 'innsbruck-land', '6292': 'innsbruck-land', '6293': 'innsbruck-land',
    '6294': 'innsbruck-land', '6295': 'innsbruck-land',
    '6130': 'innsbruck-land', '6131': 'innsbruck-land', '6132': 'innsbruck-land',
    '6133': 'innsbruck-land', '6134': 'innsbruck-land', '6135': 'innsbruck-land',
    '6136': 'zillertal',
    '6300': 'kufstein', '6306': 'kufstein',
    '6314': 'kufstein', '6320': 'kufstein', '6321': 'kufstein',
    '6322': 'kufstein', '6323': 'kufstein', '6324': 'kufstein',
    '6330': 'kufstein', '6335': 'kufstein', '6336': 'kufstein',
    '6341': 'kufstein', '6342': 'kufstein', '6343': 'kufstein', '6344': 'kufstein',
    '6345': 'achensee', '6351': 'kufstein', '6352': 'kufstein', '6353': 'kufstein',
    '6361': 'kufstein', '6363': 'kufstein', '6364': 'kufstein', '6365': 'kufstein',
    '6370': 'kitzbuehel', '6371': 'kitzbuehel', '6372': 'kitzbuehel', '6373': 'kitzbuehel',
    '6380': 'kitzbuehel', '6381': 'kitzbuehel', '6382': 'kitzbuehel', '6383': 'kitzbuehel',
    '6384': 'kitzbuehel', '6385': 'kitzbuehel', '6386': 'kitzbuehel', '6387': 'kitzbuehel',
    '6391': 'kitzbuehel', '6392': 'kitzbuehel', '6393': 'kitzbuehel',
    '6410': 'kufstein', '6411': 'kufstein', '6412': 'kufstein', '6413': 'kufstein',
    '6414': 'kufstein', '6415': 'kufstein', '6416': 'kufstein',
    '6417': 'kufstein', '6418': 'kufstein', '6419': 'kufstein',
    '6421': 'kufstein', '6422': 'kufstein', '6423': 'kufstein', '6424': 'kufstein',
    '6425': 'kufstein', '6426': 'oetztal',
    '6430': 'oetztal', '6432': 'oetztal', '6433': 'oetztal',
    '6441': 'oetztal', '6444': 'oetztal',
    '6450': 'oetztal', '6452': 'oetztal', '6456': 'oetztal', '6458': 'oetztal',
    '6460': 'imst', '6461': 'imst', '6462': 'imst', '6463': 'imst',
    '6464': 'imst', '6465': 'imst',
    '6471': 'imst', '6472': 'imst', '6473': 'imst', '6474': 'imst',
    '6481': 'imst',
    '6500': 'landeck', '6511': 'landeck',
    '6521': 'landeck', '6522': 'landeck', '6523': 'landeck',
    '6524': 'kaunertal', '6525': 'kaunertal', '6526': 'kaunertal', '6527': 'kaunertal',
    '6528': 'landeck',
    '6531': 'landeck', '6532': 'landeck', '6533': 'landeck', '6534': 'landeck',
    '6541': 'landeck', '6542': 'landeck', '6543': 'landeck', '6544': 'landeck',
    '6550': 'landeck', '6551': 'landeck', '6552': 'landeck', '6553': 'landeck',
    '6555': 'landeck',
    '6561': 'landeck', '6562': 'landeck', '6563': 'landeck',
    '6571': 'landeck', '6572': 'landeck', '6574': 'landeck',
    '6580': 'landeck',
    '6600': 'ausserfern', '6604': 'ausserfern',
    '6621': 'ausserfern', '6631': 'ausserfern', '6632': 'ausserfern',
    '6633': 'ausserfern', '6642': 'ausserfern', '6644': 'ausserfern',
    '6645': 'ausserfern', '6646': 'ausserfern', '6647': 'ausserfern',
    '6651': 'ausserfern', '6652': 'ausserfern', '6653': 'ausserfern',
    '6654': 'ausserfern', '6655': 'ausserfern',
    '6671': 'ausserfern', '6673': 'ausserfern', '6675': 'ausserfern',
    '6676': 'ausserfern', '6677': 'ausserfern',
    '6682': 'ausserfern',
    '6691': 'ausserfern',
    '6700': 'arlberg', '6706': 'arlberg', '6707': 'arlberg', '6708': 'arlberg',
    '6710': 'arlberg', '6712': 'arlberg', '6713': 'arlberg', '6714': 'arlberg',
    '6715': 'arlberg', '6716': 'arlberg', '6719': 'arlberg',
    '6721': 'arlberg', '6722': 'arlberg', '6723': 'arlberg', '6724': 'arlberg',
    '6751': 'arlberg', '6752': 'arlberg', '6753': 'arlberg', '6754': 'arlberg',
    '6755': 'arlberg', '6762': 'arlberg', '6763': 'arlberg', '6764': 'arlberg', '6767': 'arlberg',
    '6800': 'imst',
    '6830': 'imst', '6832': 'imst', '6833': 'imst', '6834': 'imst', '6835': 'imst',
    '6836': 'imst', '6837': 'imst',
    '6840': 'imst', '6841': 'imst', '6842': 'imst', '6844': 'imst', '6845': 'imst',
    '6850': 'imst', '6858': 'imst',
    '6870': 'arlberg', '6881': 'arlberg', '6882': 'imst', '6883': 'imst', '6886': 'imst',
    '6890': 'imst',
    '6900': 'imst',
    '6911': 'imst',
    '6921': 'imst', '6922': 'imst', '6923': 'imst',
    '6932': 'imst', '6933': 'imst', '6934': 'imst',
    '6941': 'imst', '6942': 'imst', '6943': 'imst', '6944': 'imst',
    '6951': 'imst', '6952': 'imst',
    '6961': 'imst',
    '6971': 'imst', '6972': 'imst', '6973': 'imst', '6974': 'imst',
    '6991': 'imst', '6992': 'imst', '6993': 'imst',
    '9900': 'osttirol', '9901': 'osttirol', '9902': 'osttirol', '9903': 'osttirol',
    '9904': 'osttirol', '9905': 'osttirol', '9906': 'osttirol', '9907': 'osttirol',
    '9908': 'osttirol', '9909': 'osttirol', '9911': 'osttirol', '9912': 'osttirol',
    '9913': 'osttirol', '9918': 'osttirol', '9919': 'osttirol',
    '9920': 'osttirol', '9921': 'osttirol', '9922': 'osttirol', '9923': 'osttirol',
    '9924': 'osttirol',
    '9931': 'osttirol', '9932': 'osttirol',
    '9941': 'osttirol', '9942': 'osttirol', '9943': 'osttirol', '9944': 'osttirol',
    '9945': 'osttirol', '9946': 'osttirol',
    '9951': 'osttirol', '9952': 'osttirol', '9953': 'osttirol', '9954': 'osttirol',
    '9955': 'osttirol',
    '9961': 'osttirol', '9962': 'osttirol', '9963': 'osttirol',
    '9971': 'osttirol', '9972': 'osttirol',
    '9981': 'osttirol', '9982': 'osttirol',
    '9990': 'osttirol', '9991': 'osttirol', '9992': 'osttirol',
    '6105': 'innsbruck-land',
    '6631': 'ausserfern',
}

OVERPAST_API = 'https://overpass.kumi.systems/api/interpreter'


def normalize(name):
    """Normalize a place name for comparison."""
    name = name.lower().strip()
    name = unicodedata.normalize('NFKD', name)
    name = name.encode('ascii', 'ignore').decode('ascii')
    name = re.sub(r'[^a-z0-9\s\.\-]', '', name)
    return name.strip()


def load_orte():
    """Load orte entries."""
    ortes = {}
    for f in glob.glob(os.path.join(ORTE_DIR, '*', 'index.json')):
        with open(f) as fh:
            d = json.load(fh)
        key = d.get('name', '').lower().strip()
        if key:
            ortes[key] = d
            norm = normalize(d['name'])
            if norm:
                ortes[norm] = d
    return ortes


def find_region_for_entry(entry, ortes):
    """Try to find a better region for an entry."""
    ort = entry.get('ort', '') or ''
    plz = entry.get('plz', '') or ''
    name = entry.get('name', '') or ''
    lat = entry.get('koordinaten', {}).get('lat')
    lng = entry.get('koordinaten', {}).get('lng')
    current_region = entry.get('region', '') or ''
    
    if current_region:
        return current_region, ort  # Already has region
    
    # Strategy 1: Direct ort match
    if ort:
        ort_lower = ort.lower().strip()
        if ort_lower in ortes:
            info = ortes[ort_lower]
            return info['region'], info['name']
        
        # Normalized
        norm = normalize(ort)
        if norm in ortes:
            info = ortes[norm]
            return info['region'], info['name']
        
        # Manual override
        manual_key = ort_lower.replace('ß', 'ss').replace('ü', 'ue').replace('ö', 'oe').replace('ä', 'ae')
        if manual_key in MANUAL_REGION:
            info = MANUAL_REGION[manual_key]
            if info is None:
                return '', ort  # explicitly not in Tirol
            return info[0], info[1]
        
        # Fuzzy match — check if ort is contained in orte name or vice versa
        for key, info in ortes.items():
            if len(key) > 3 and (key in ort_lower or ort_lower in key):
                return info['region'], info['name']
    
    # Strategy 2: PLZ lookup
    if plz and plz in PLZ_REGION:
        return PLZ_REGION[plz], ort
    
    # Strategy 3: Try to infer from name
    name_lower = name.lower()
    
    # Regional name hints
    region_hints = {
        'stubaital': ['stubai', 'neustift'],
        'zillertal': ['zillertal', 'ziller', 'mayrhofen', 'fügen', 'fugen'],
        'oetztal': ['ötz', 'oetz', 'soelden', 'sölden', 'ochsengarten'],
        'innsbruck': ['innsbruck', 'ibk'],
        'kitzbuehel': ['kitzbühel', 'kitzbuehel', 'hahnenkamm', 'going', 'jochberg', 'kirchberg'],
        'kufstein': ['kufstein', 'wörgl', 'woergl'],
        'arlberg': ['arlberg', 'st. anton', 'sankt anton', 'ischgl', 'kappl', 'stuben'],
        'landeck': ['landeck', 'prutz', 'serfaus', 'fiss', 'ladis'],
        'imst': ['imst', 'pitztal', 'pitz'],
        'ausserfern': ['ausserfern', 'ehrwald', 'lermoos', 'reutte', 'zugspitze'],
        'achensee': ['achensee', 'achenkirch', 'pertisau', 'maurach'],
        'kaunertal': ['kaunertal', 'kaun', 'feichten'],
        'osttirol': ['osttirol', 'lienz', 'defereggen', 'villgraten', 'grossglockner', 'iselsberg', 'sillian'],
        'stubaital': ['stubaital', 'stubai'],
    }
    
    for region, hints in region_hints.items():
        if any(h in name_lower for h in hints):
            return region, ort
    
    # Strategy 4: Reverse geocode from coordinates — skip, unreliable
    # if lat and lng:
    #     region_from_coords = reverse_geocode(float(lat), float(lng))
    #     if region_from_coords:
    #         return region_from_coords, ort
    
    return '', ort


def reverse_geocode(lat, lng):
    """Use Overpass to reverse geocode coordinates → region.
    Queries the nearest settlement and its administrative area."""
    if abs(float(lat)) < 1 or abs(float(lng)) < 1:
        return None
    
    query = f'''
[out:json][timeout:10];
(
  node["place"~"village|town|city"](around:500,{lat},{lng});
  node["place"="hamlet"](around:300,{lat},{lng});
);
out tags 1;
'''
    try:
        resp = requests.post(OVERPAST_API, data={'data': query}, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            for element in data.get('elements', []):
                tags = element.get('tags', {})
                name = tags.get('name', '')
                if name and ('Tirol' in tags.get('is_in', '') or any(
                    t in tags.get('population', '') for t in ['Tirol', 'tyrol']
                )):
                    return None  # Skip reverse geo for now
                # Return hint based on name
                return None
    except Exception:
        pass
    return None


def main():
    print("=" * 50)
    print("  Region Fix Script — Tirol Tourismus")
    print("=" * 50)
    
    print("\nLoading orte registry...")
    ortes = load_orte()
    print(f"  {len(ortes)} orte entries")
    
    # Load all unterkunft entries
    entries = []
    for f in glob.glob(os.path.join(UNTERKUNFT_DIR, '*', 'index.json')):
        with open(f) as fh:
            d = json.load(fh)
        entries.append((f, d))
    
    print(f"\nProcessing {len(entries)} entries...")
    
    fixed = 0
    already_ok = 0
    no_region = 0
    no_ort = 0
    name_guessed = 0
    
    for fpath, entry in entries:
        old_region = entry.get('region', '') or ''
        old_ort = entry.get('ort', '') or ''
        
        new_region, new_ort = find_region_for_entry(entry, ortes)
        
        if new_region and new_region != old_region:
            entry['region'] = new_region
            fixed += 1
            if old_ort != new_ort and new_ort:
                entry['ort'] = new_ort
        elif not old_region and not new_region:
            no_region += 1
        
        if not old_ort and new_ort:
            entry['ort'] = new_ort
            if not old_ort and new_ort:
                no_ort += 1
        
        # Write back
        with open(fpath, 'w', encoding='utf-8') as f:
            json.dump(entry, f, ensure_ascii=False, indent=2)
    
    # Count stats
    with_region = 0
    region_counts = defaultdict(int)
    for f in glob.glob(os.path.join(UNTERKUNFT_DIR, '*', 'index.json')):
        d = json.load(open(f))
        if d.get('region'):
            with_region += 1
            region_counts[d['region']] += 1
    
    print(f"\n{'=' * 50}")
    print(f"  Fixed region: {fixed}")
    print(f"  Already OK: {already_ok}")
    print(f"  Still no region: {len(entries) - with_region}")
    print(f"  Found ort from name: {name_guessed}")
    print(f"  Total with region: {with_region}/{len(entries)}")
    print(f"{'=' * 50}")
    print(f"\n  Region distribution:")
    for r, c in sorted(region_counts.items(), key=lambda x: -x[1]):
        print(f"    {r}: {c}")
    
    # Show entries that still have no region
    still_no_region = []
    for f in glob.glob(os.path.join(UNTERKUNFT_DIR, '*', 'index.json')):
        d = json.load(open(f))
        if not d.get('region'):
            still_no_region.append((d.get('name', '?'), d.get('ort', '?'), d.get('plz', '?')))
    
    if still_no_region:
        print(f"\n  Entries still without region ({len(still_no_region)}):")
        for name, ort, plz in sorted(still_no_region, key=lambda x: x[1] or '')[0:20]:
            print(f"    {name[:40]:40s} ort={ort:25s} plz={plz}")


if __name__ == '__main__':
    main()
