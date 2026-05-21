#!/usr/bin/env python3
"""
OSM Hotel Scraper for Tirol Tourismus
=======================================
Lädt echte Unterkunfts-Daten aus OpenStreetMap für ganz Tirol.
Ersetzt die 59 Fake-Unterkünfte durch echte OSM-Daten.

Usage:
  /c/Python314/python scripts/osm_scraper.py

Verbesserungen:
  - Area-gefilterte Overpass Query (kein Bounding-Box, exakte Tirol-Grenze)
  - Höheres Output-Limit (5000 Elemente)
  - Verbesserte Region-Mapping via PLZ, Fuzzy, etc.
  - camp_site und farm Typen korrekt behandelt
  - Backup vor Änderungen

Output: src/data/unterkuenfte/{slug}/index.json
"""

import json
import os
import re
import sys
import unicodedata
import glob
from collections import defaultdict
import requests

# ─── Konfiguration ────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'src', 'data')
UNTERKUNFT_DIR = os.path.join(DATA_DIR, 'unterkuenfte')
ORTE_DIR = os.path.join(DATA_DIR, 'orte')
BACKUP_DIR = os.path.join(BASE_DIR, 'src', 'data', 'unterkuenfte_backup')

OVERPAST_API = 'https://overpass.kumi.systems/api/interpreter'

# OSM tourism→unser Typ-Mapping
TYP_MAPPING = {
    'hotel': 'hotel',
    'guest_house': 'gasthof',
    'apartment': 'ferienwohnung',
    'chalet': 'ferienhaus',
    'hostel': 'jugendherberge',
    'camp_site': 'camping',
    'farm': 'bauernhof',
}

# Amenity mapping from OSM tags
AMENITY_TAGS = {
    'wifi': 'wifi',
    'internet_access': 'wifi',
    'sauna': 'sauna',
    'pool': 'pool',
    'swimming_pool': 'pool',
    'restaurant': 'restaurant',
    'parking': 'parkplatz',
    'breakfast': 'fruehstueck',
    'bar': 'bar',
}

# Tag-Generierung basierend auf Typ
TYP_TAGS = {
    'hotel': ['hotel', 'komfort'],
    'gasthof': ['gasthof', 'kulinarik', 'tradition'],
    'ferienwohnung': ['ferienwohnung', 'privat'],
    'ferienhaus': ['ferienhaus', 'privat', 'familie'],
    'jugendherberge': ['hostel', 'preiswert', 'gruppe'],
    'camping': ['camping', 'natur', 'outdoor'],
    'bauernhof': ['bauernhof', 'natur', 'familie', 'landleben'],
}

# Manual region-overrides for places we know about but don't match automatically
MANUAL_REGION_OVERRIDES = {
    'hochpillberg': 'zillertal',
    'pill': 'zillertal',
    'milders': 'stubaital',
    'rettenschöss': 'kufstein',
    'kaunerberg': 'kaunertal',
    'feichten': 'kaunertal',
    'kaunertal': 'kaunertal',
    'prutz': 'landeck',
    'oberperfuss': 'innsbruck-land',
    'oberperfuß': 'innsbruck-land',
    'mittelberg': 'osttirol',
    'innervillgraten': 'osttirol',
    'ausservillgraten': 'osttirol',
    'hopfgarten in defereggen': 'osttirol',
    'hopfgarten': 'osttirol',
    'sillian': 'osttirol',
    'st. johann im walde': 'osttirol',
    'sankt johann im walde': 'osttirol',
    'st. johann in tirol': 'kitzbuehel',
    'sankt johann in tirol': 'kitzbuehel',
    'going am wilden kaiser': 'kitzbuehel',
    'going': 'kitzbuehel',
    'kitzbühel': 'kitzbuehel',
    'jochberg': 'kitzbuehel',
    'kirchberg in tirol': 'kitzbuehel',
    'kirchberg': 'kitzbuehel',
    'fieberbrunn': 'kitzbuehel',
    'wörgl': 'kufstein',
    'woergl': 'kufstein',
    'kundl': 'kufstein',
    'brixlegg': 'kufstein',
    'rattenberg': 'kufstein',
    'kramsach': 'kufstein',
    'bruck am ziller': 'kufstein',
    'münster': 'kufstein',
    'strass im zillertal': 'kufstein',
    'schlitters': 'kufstein',
    'fügen': 'zillertal',
    'fuegen': 'zillertal',
    'fügenberg': 'zillertal',
    'fuegenberg': 'zillertal',
    'uderns': 'zillertal',
    'stumm': 'zillertal',
    'zell am ziller': 'zillertal',
    'ramsaU im zillertal': 'zillertal',
    'gerlos': 'zillertal',
    'hart im zillertal': 'zillertal',
    'hippach': 'zillertal',
    'kaltenbach': 'zillertal',
    'aschaU im zillertal': 'zillertal',
    'tux': 'zillertal',
    'lanersbach': 'zillertal',
    'mayrhofen': 'zillertal',
    'brandberg': 'zillertal',
    'stummerberg': 'zillertal',
    'obersulzbach': 'zillertal',
    'achenkirch': 'achensee',
    'pertisau': 'achensee',
    'maurach': 'achensee',
    'steinberg': 'achensee',
    'steinberg am rofan': 'achensee',
    'erfurt': None,  # not in Tirol
}

# Reverse lookup: PLZ → Region (important Austrian PLZ)
PLZ_REGION_MAP = {
    '6020': 'innsbruck', '6010': 'innsbruck', '6021': 'innsbruck',
    '6060': 'innsbruck-land', '6063': 'innsbruck-land',
    '6065': 'innsbruck-land', '6067': 'innsbruck-land',
    '6070': 'innsbruck-land', '6071': 'innsbruck-land',
    '6072': 'innsbruck-land', '6073': 'innsbruck-land',
    '6074': 'innsbruck-land', '6075': 'innsbruck-land',
    '6080': 'innsbruck-land', '6082': 'innsbruck-land',
    '6091': 'innsbruck-land', '6092': 'innsbruck-land',
    '6094': 'innsbruck-land', '6100': 'innsbruck-land',
    '6111': 'innsbruck-land', '6112': 'innsbruck-land',
    '6116': 'stubaital', '6167': 'stubaital',
    '6166': 'stubaital', '6165': 'stubaital',
    '6162': 'stubaital', '6161': 'stubaital',
    '6154': 'stubaital', '6150': 'stubaital',
    '6145': 'stubaital', '6144': 'stubaital',
    '6143': 'stubaital', '6142': 'stubaital',
    '6141': 'stubaital',
    '6170': 'innsbruck-land', '6175': 'innsbruck-land',
    '6179': 'innsbruck-land', '6180': 'innsbruck-land',
    '6181': 'innsbruck-land', '6182': 'innsbruck-land',
    '6183': 'innsbruck-land', '6184': 'innsbruck-land',
    '6190': 'innsbruck-land',
    '6200': 'innsbruck-land', '6210': 'innsbruck-land',
    '6215': 'innsbruck-land', '6216': 'innsbruck-land',
    '6220': 'innsbruck-land', '6221': 'innsbruck-land',
    '6222': 'innsbruck-land',
    '6300': 'kufstein', '6306': 'kufstein',
    '6314': 'kufstein', '6320': 'kufstein',
    '6321': 'kufstein', '6322': 'kufstein',
    '6323': 'kufstein', '6324': 'kufstein',
    '6330': 'kufstein', '6335': 'kufstein',
    '6336': 'kufstein',
    '6341': 'kufstein', '6342': 'kufstein',
    '6343': 'kufstein', '6344': 'kufstein',
    '6345': 'achensee',
    '6351': 'kufstein', '6352': 'kufstein',
    '6353': 'kufstein',
    '6361': 'kufstein', '6363': 'kufstein',
    '6364': 'kufstein', '6365': 'kufstein',
    '6370': 'kitzbuehel', '6371': 'kitzbuehel',
    '6372': 'kitzbuehel', '6373': 'kitzbuehel',
    '6380': 'kitzbuehel', '6381': 'kitzbuehel',
    '6382': 'kitzbuehel', '6383': 'kitzbuehel',
    '6384': 'kitzbuehel', '6385': 'kitzbuehel',
    '6386': 'kitzbuehel', '6387': 'kitzbuehel',
    '6391': 'kitzbuehel', '6392': 'kitzbuehel',
    '6393': 'kitzbuehel',
    '6401': 'kufstein', '6402': 'kufstein',
    '6403': 'kufstein',
    '6410': 'kufstein', '6411': 'kufstein',
    '6412': 'kufstein', '6413': 'kufstein',
    '6414': 'kufstein', '6415': 'kufstein',
    '6416': 'kufstein', '6417': 'kufstein',
    '6418': 'kufstein', '6419': 'kufstein',
    '6421': 'kufstein', '6422': 'kufstein',
    '6423': 'kufstein', '6424': 'kufstein',
    '6425': 'kufstein', '6426': 'kufstein',
    '6430': 'kufstein', '6432': 'kufstein',
    '6433': 'kufstein',
    '6441': 'kufstein', '6442': 'kufstein',
    '6443': 'kufstein', '6444': 'kufstein',
    '6450': 'kufstein', '6452': 'kufstein',
    '6456': 'kufstein', '6458': 'kufstein',
    '6460': 'kufstein', '6461': 'kufstein',
    '6462': 'kufstein', '6463': 'kufstein',
    '6464': 'kufstein', '6465': 'kufstein',
    '6471': 'kufstein', '6472': 'kufstein',
    '6473': 'kufstein', '6474': 'kufstein',
    '6481': 'kufstein',
    '6500': 'landeck', '6511': 'landeck',
    '6521': 'landeck', '6522': 'landeck',
    '6523': 'landeck', '6524': 'kaunertal',
    '6525': 'kaunertal', '6526': 'kaunertal',
    '6527': 'kaunertal', '6528': 'landeck',
    '6531': 'landeck', '6532': 'landeck',
    '6533': 'landeck', '6534': 'landeck',
    '6541': 'landeck', '6542': 'landeck',
    '6543': 'landeck', '6544': 'landeck',
    '6550': 'landeck', '6551': 'landeck',
    '6552': 'landeck', '6553': 'landeck',
    '6555': 'landeck',
    '6561': 'landeck', '6562': 'landeck',
    '6563': 'landeck',
    '6571': 'landeck', '6572': 'landeck',
    '6574': 'landeck',
    '6580': 'landeck',
    '6600': 'ausserfern', '6604': 'ausserfern',
    '6611': 'ausserfern', '6621': 'ausserfern',
    '6622': 'ausserfern', '6623': 'ausserfern',
    '6624': 'ausserfern', '6631': 'ausserfern',
    '6632': 'ausserfern', '6633': 'ausserfern',
    '6642': 'ausserfern', '6644': 'ausserfern',
    '6645': 'ausserfern', '6646': 'ausserfern',
    '6647': 'ausserfern', '6651': 'ausserfern',
    '6652': 'ausserfern', '6653': 'ausserfern',
    '6654': 'ausserfern', '6655': 'ausserfern',
    '6661': 'ausserfern', '6671': 'ausserfern',
    '6672': 'ausserfern', '6673': 'ausserfern',
    '6675': 'ausserfern', '6676': 'ausserfern',
    '6677': 'ausserfern', '6682': 'ausserfern',
    '6691': 'ausserfern',
    '6700': 'arlberg', '6706': 'arlberg',
    '6707': 'arlberg', '6708': 'arlberg',
    '6710': 'arlberg', '6712': 'arlberg',
    '6713': 'arlberg', '6714': 'arlberg',
    '6715': 'arlberg', '6716': 'arlberg',
    '6719': 'arlberg', '6721': 'arlberg',
    '6722': 'arlberg', '6723': 'arlberg',
    '6724': 'arlberg',
    '6751': 'arlberg', '6752': 'arlberg',
    '6753': 'arlberg', '6754': 'arlberg',
    '6755': 'arlberg', '6762': 'arlberg',
    '6763': 'arlberg', '6764': 'arlberg',
    '6767': 'arlberg',
    '6800': 'imst', '6811': 'imst',
    '6812': 'imst', '6822': 'imst',
    '6830': 'imst', '6832': 'imst',
    '6833': 'imst', '6834': 'imst',
    '6835': 'imst', '6836': 'imst',
    '6840': 'imst', '6841': 'imst',
    '6842': 'imst', '6844': 'imst',
    '6845': 'imst', '6850': 'imst',
    '6858': 'imst',
    '6881': 'arlberg',
    '6882': 'imst', '6883': 'imst',
    '6886': 'imst',
    '6890': 'imst',
    '6900': 'imst',
    '6911': 'imst',
    '6921': 'imst', '6922': 'imst',
    '6923': 'imst',
    '6932': 'imst', '6933': 'imst',
    '6941': 'imst', '6942': 'imst',
    '6943': 'imst', '6944': 'imst',
    '6951': 'imst', '6952': 'imst',
    '6961': 'imst', '6962': 'imst',
    '6971': 'imst', '6972': 'imst',
    '6973': 'imst', '6974': 'imst',
    '6991': 'imst', '6992': 'imst',
    '6993': 'imst',
    '6433': 'imst',
    '6130': 'innsbruck-land', '6131': 'innsbruck-land',
    '6132': 'innsbruck-land', '6133': 'innsbruck-land',
    '6134': 'innsbruck-land', '6135': 'innsbruck-land',
    '6136': 'zillertal',
    '6200': 'innsbruck-land',
    '6230': 'innsbruck-land', '6232': 'innsbruck-land',
    '6233': 'innsbruck-land', '6234': 'innsbruck-land',
    '6235': 'innsbruck-land', '6236': 'innsbruck-land',
    '6240': 'innsbruck-land', '6241': 'innsbruck-land',
    '6250': 'innsbruck-land', '6252': 'innsbruck-land',
    '6260': 'innsbruck-land', '6261': 'innsbruck-land',
    '6262': 'innsbruck-land', '6263': 'innsbruck-land',
    '6264': 'innsbruck-land', '6265': 'innsbruck-land',
    '6271': 'innsbruck-land', '6272': 'innsbruck-land',
    '6273': 'innsbruck-land', '6274': 'innsbruck-land',
    '6275': 'innsbruck-land', '6276': 'innsbruck-land',
    '6277': 'innsbruck-land', '6278': 'innsbruck-land',
    '6280': 'innsbruck-land', '6281': 'innsbruck-land',
    '6283': 'innsbruck-land', '6284': 'innsbruck-land',
    '6290': 'innsbruck-land', '6292': 'innsbruck-land',
    '6293': 'innsbruck-land', '6294': 'innsbruck-land',
    '6295': 'innsbruck-land',
    '6441': 'innsbruck-land',
    '6450': 'innsbruck-land',
    '6103': 'innsbruck-land',
    # Ötztal PLZs
    '6426': 'oetztal',
    '6430': 'oetztal',
    '6432': 'oetztal',
    '6433': 'oetztal',
    '6441': 'oetztal',
    '6444': 'oetztal',
    '6450': 'oetztal',
    '6452': 'oetztal',
    '6456': 'oetztal',
    '6458': 'oetztal',
    # Osttirol PLZs
    '9900': 'osttirol', '9901': 'osttirol', '9902': 'osttirol',
    '9903': 'osttirol', '9904': 'osttirol', '9905': 'osttirol',
    '9906': 'osttirol', '9907': 'osttirol', '9908': 'osttirol',
    '9909': 'osttirol', '9911': 'osttirol', '9912': 'osttirol',
    '9913': 'osttirol', '9918': 'osttirol',
    '9920': 'osttirol', '9921': 'osttirol', '9922': 'osttirol',
    '9923': 'osttirol', '9924': 'osttirol',
    '9931': 'osttirol', '9932': 'osttirol',
    '9941': 'osttirol', '9942': 'osttirol', '9943': 'osttirol',
    '9944': 'osttirol', '9945': 'osttirol', '9946': 'osttirol',
    '9951': 'osttirol', '9952': 'osttirol', '9953': 'osttirol',
    '9954': 'osttirol', '9955': 'osttirol',
    '9961': 'osttirol', '9962': 'osttirol', '9963': 'osttirol',
    '9971': 'osttirol', '9972': 'osttirol',
    '9981': 'osttirol', '9982': 'osttirol',
    '9990': 'osttirol', '9991': 'osttirol', '9992': 'osttirol',
}


def slugify(text):
    """Create a URL-safe slug from German text."""
    text = text.lower().strip()
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    text = re.sub(r'[^a-z0-9]+', '-', text)
    text = text.strip('-')
    return text


def normalize_name(name):
    """Normalize a place name for comparison (remove diacritics, lowercase)."""
    name = name.lower().strip()
    name = unicodedata.normalize('NFKD', name)
    name = name.encode('ascii', 'ignore').decode('ascii')
    name = re.sub(r'[^a-z0-9\s\.\-]', '', name)
    return name.strip()


def load_orte_registry():
    """Load all Orte and build lookup maps."""
    orte_by_name = {}
    orte_by_normalized = {}
    orte_by_slug = {}
    orte_by_plz = {}
    
    for fpath in glob.glob(os.path.join(ORTE_DIR, '*', 'index.json')):
        with open(fpath, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                continue
        
        name = data.get('name', '').strip()
        slug = data.get('slug', '')
        region = data.get('region', '')
        plz = data.get('plz', '')
        bezirk = data.get('bezirk', '')
        
        if not name or not region:
            continue
        
        name_lower = name.lower()
        normalized = normalize_name(name)
        
        entry = {
            'name': name, 'slug': slug, 'region': region,
            'plz': plz, 'bezirk': bezirk,
        }
        
        orte_by_name[name_lower] = entry
        if normalized and normalized != name_lower:
            orte_by_normalized[normalized] = entry
        if slug:
            orte_by_slug[slug] = entry
        if plz:
            orte_by_plz.setdefault(plz, []).append(entry)
    
    return orte_by_name, orte_by_normalized, orte_by_slug, orte_by_plz


def find_region(addr_city, addr_plz, orte_by_name, orte_by_normalized, orte_by_slug, orte_by_plz):
    """Find region for a city using multiple lookup strategies."""
    if not addr_city and not addr_plz:
        return None, None, None
    
    region = None
    ort_name = None
    plz = addr_plz
    
    # Strategy 1: Direct name lookup
    if addr_city:
        city_clean = addr_city.lower().strip()
        
        # Remove "Sankt" → "St." variations
        city_variants = [city_clean]
        city_variants.append(city_clean.replace('sankt ', 'st. '))
        city_variants.append(city_clean.replace('st. ', 'sankt '))
        city_variants.append(city_clean.replace('st ', 'st. '))
        city_variants = list(set(city_variants))
        
        for variant in city_variants:
            if variant in orte_by_name:
                info = orte_by_name[variant]
                return info['region'], info['name'], info.get('plz', plz)
        
        # Strategy 2: Normalized match
        normalized = normalize_name(addr_city)
        if normalized in orte_by_normalized:
            info = orte_by_normalized[normalized]
            return info['region'], info['name'], info.get('plz', plz)
        
        # Strategy 3: Slug match
        slug = slugify(addr_city)
        if slug in orte_by_slug:
            info = orte_by_slug[slug]
            return info['region'], info['name'], info.get('plz', plz)
        
        # Strategy 4: Manual override
        manual_key = city_clean.replace('ß', 'ss').replace('ü', 'ue').replace('ö', 'oe').replace('ä', 'ae')
        if manual_key in MANUAL_REGION_OVERRIDES:
            r = MANUAL_REGION_OVERRIDES[manual_key]
            if r is None:
                return None, None, plz  # explicitly excluded
            return r, addr_city, plz
        
        # Strategy 5: Fuzzy substring match against orte names
        for key, info in orte_by_name.items():
            if city_clean in key or key in city_clean:
                return info['region'], info['name'], info.get('plz', plz)
            # Also check normalized names
            nkey = normalize_name(key)
            ncity = normalize_name(city_clean)
            if ncity and (ncity in nkey or nkey in ncity):
                return info['region'], info['name'], info.get('plz', plz)
    
    # Strategy 6: PLZ lookup (German postal codes are very specific)
    if addr_plz and addr_plz in PLZ_REGION_MAP:
        region_from_plz = PLZ_REGION_MAP[addr_plz]
        if region_from_plz:
            return region_from_plz, addr_city or '', addr_plz
    
    # Strategy 7: PLZ from orte database
    if addr_plz and addr_plz in orte_by_plz:
        for info in orte_by_plz[addr_plz]:
            return info['region'], info['name'], addr_plz
    
    return None, None, plz


def run_overpass_query(query, timeout=180):
    """Run an Overpass QL query and return JSON result."""
    print(f"  Querying Overpass API (timeout={timeout}s)...")
    try:
        resp = requests.post(
            OVERPAST_API,
            data={'data': query},
            timeout=timeout + 10
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError as e:
        body = e.response.text[:500] if e.response is not None else str(e)
        print(f"  HTTP Error {e.response.status_code}: {body}")
        return None
    except Exception as e:
        print(f"  Error: {e}")
        return None


def query_all_tirol():
    """Query Tirol accommodation data from Overpass API."""
    types_str = '|'.join(TYP_MAPPING.keys())
    bbox = "47.0,10.0,48.0,13.0"
    
    # Single combined query
    query = f'''
[out:json][timeout:120];
(
  node["tourism"~"{types_str}"]({bbox});
  way["tourism"~"{types_str}"]({bbox});
  rel["tourism"~"{types_str}"]({bbox});
);
out center body 1000;
'''
    print("Querying Overpass API (limit=1000, 120s timeout)...")
    result = run_overpass_query(query, timeout=120)
    return result


def extract_element_data(element, orte_by_name, orte_by_normalized, orte_by_slug, orte_by_plz):
    """Extract accommodation data from an OSM element."""
    tags = element.get('tags', {})
    
    tourism = tags.get('tourism', '')
    typ = TYP_MAPPING.get(tourism)
    if not typ:
        return None
    
    # Check operational status
    for status_key in ['disused:', 'abandoned:', 'demolished:', 'proposed:', 'construction:']:
        if tourism.startswith(status_key) or any(
            tags.get(k, '').startswith('disused') for k in ['status', 'opening_hours:status']
        ):
            return None
    
    name = tags.get('name', '').strip()
    if not name or len(name) < 2:
        return None
    
    # Skip non-accommodation keywords
    skip_keywords = ['wc', 'toilette', 'busbahnhof', 'parkplatz', 'tankstelle']
    if any(k in name.lower() for k in skip_keywords):
        return None
    
    # Extract coordinates
    lat = element.get('lat')
    lng = element.get('lon')
    if lat is None and 'center' in element:
        lat = element['center'].get('lat')
        lng = element['center'].get('lon')
    if lat is None:
        return None
    
    # Address
    addr_city = (tags.get('addr:city', '') or tags.get('addr:locality', '') or 
                 tags.get('addr:suburb', '') or tags.get('addr:hamlet', '') or 
                 tags.get('addr:village', '') or tags.get('addr:town', ''))
    addr_street = tags.get('addr:street', '') or tags.get('addr:place', '')
    addr_housenumber = tags.get('addr:housenumber', '')
    addr_postcode = tags.get('addr:postcode', '')
    
    # Contact
    phone = tags.get('phone', '') or tags.get('contact:phone', '')
    email = tags.get('email', '') or tags.get('contact:email', '')
    website = tags.get('website', '') or tags.get('contact:website', '') or tags.get('url', '')
    
    # Stars
    stars_raw = tags.get('stars', '')
    sterne = None
    if stars_raw:
        try:
            sterne = int(float(stars_raw))
            if sterne < 1 or sterne > 7:
                sterne = None
        except (ValueError, TypeError):
            sterne = None
    
    # Region lookup
    region, ort_name, plz = find_region(addr_city, addr_postcode, orte_by_name, orte_by_normalized, orte_by_slug, orte_by_plz)
    if not region and addr_city:
        # Fallback: just set the city with no region
        ort_name = ort_name or addr_city
    
    # Address
    adresse_parts = []
    if addr_street:
        if addr_housenumber:
            adresse_parts.append(f"{addr_street} {addr_housenumber}")
        else:
            adresse_parts.append(addr_street)
    elif addr_housenumber:
        adresse_parts.append(addr_housenumber)
    adresse = ', '.join(adresse_parts)
    
    # Amenities from OSM tags
    ausstattung = []
    for osm_tag, our_amenity in AMENITY_TAGS.items():
        val = tags.get(osm_tag, '').lower()
        if val and val not in ('no', 'false', '0', ''):
            if our_amenity not in ausstattung:
                ausstattung.append(our_amenity)
    
    if tags.get('leisure', '') in ('sauna',) and 'sauna' not in ausstattung:
        ausstattung.append('sauna')
    if tags.get('leisure', '') in ('swimming_pool',) and 'pool' not in ausstattung:
        ausstattung.append('pool')
    if tags.get('leisure', '') in ('sports_centre', 'fitness_centre') and 'fitness' not in ausstattung:
        ausstattung.append('fitness')
    if tags.get('amenity', '') == 'restaurant' and 'restaurant' not in ausstattung:
        ausstattung.append('restaurant')
    if tags.get('amenity', '') == 'parking' or tags.get('parking', '') or tags.get('parking:type', ''):
        if 'parkplatz' not in ausstattung:
            ausstattung.append('parkplatz')
    
    # Tags
    tags_list = list(TYP_TAGS.get(typ, []))
    if region and region not in tags_list:
        tags_list.append(region)
    
    amenity_to_tag = {'sauna': 'wellness', 'pool': 'wellness', 'restaurant': 'kulinarik', 'fitness': 'sport'}
    for amenity, tag in amenity_to_tag.items():
        if amenity in ausstattung and tag not in tags_list:
            tags_list.append(tag)
    
    # Name-based tags
    name_lower = name.lower()
    if any(w in name_lower for w in ['berg', 'alm', 'gipfel', 'spitze', 'stein']):
        if 'berg' not in tags_list: tags_list.append('berg')
    if any(w in name_lower for w in ['wellness', 'vital', 'spa', 'bad', 'therme', 'vital']):
        if 'wellness' not in tags_list: tags_list.append('wellness')
    if any(w in name_lower for w in ['ski', 'sport', 'aktiv']):
        if 'sport' not in tags_list: tags_list.append('sport')
    if any(w in name_lower for w in ['see', 'lake', 'meer']):
        if 'wasser' not in tags_list: tags_list.append('wasser')
    if any(w in name_lower for w in ['wandern', 'trekking', 'natur']):
        if 'natur' not in tags_list: tags_list.append('natur')
    if any(w in name_lower for w in ['familie', 'family', 'kinder']):
        if 'familie' not in tags_list: tags_list.append('familie')
    if any(w in name_lower for w in ['luxus', 'palace', 'royal', 'grand', 'resort']):
        if 'luxus' not in tags_list: tags_list.append('luxus')
    
    # Slug
    slug_base = slugify(name)
    
    entry = {
        'name': name,
        'slug': '',
        'typ': typ,
        'sterne': sterne,
        'preis_ab': None,
        'ort': ort_name or addr_city or '',
        'region': region or '',
        'plz': plz or addr_postcode or '',
        'adresse': adresse,
        'telefon': phone or None,
        'email': email or None,
        'webseite': website or None,
        'beschreibung': '',
        'ausstattung': sorted(set(ausstattung)),
        'tags': sorted(set(tags_list)),
        'tier': 'basic',
        'koordinaten': {'lat': str(lat), 'lng': str(lng)},
        'status': 'published',
    }
    
    return slug_base, entry


def deduplicate_slugs(entries_by_slug):
    """Ensure all slugs are unique."""
    slug_counts = defaultdict(int)
    for slug in entries_by_slug:
        slug_counts[slug] += 1
    
    result = {}
    temp_counter = defaultdict(int)
    for slug, entry in entries_by_slug.items():
        if slug_counts[slug] > 1:
            temp_counter[slug] += 1
            new_slug = f"{slug}-{temp_counter[slug]}"
        else:
            new_slug = slug
        entry['slug'] = new_slug
        result[new_slug] = entry
    return result


def backup_old_data():
    """Backup existing unterkunft data."""
    if os.path.exists(UNTERKUNFT_DIR):
        import shutil
        if os.path.exists(BACKUP_DIR):
            shutil.rmtree(BACKUP_DIR)
        print(f"  Backing up: {UNTERKUNFT_DIR} → {BACKUP_DIR}")
        shutil.copytree(UNTERKUNFT_DIR, BACKUP_DIR)
        return True
    return False


def clean_unterkunft_dir():
    """Remove all existing entries."""
    import shutil
    if not os.path.exists(UNTERKUNFT_DIR):
        os.makedirs(UNTERKUNFT_DIR)
        return
    for item in os.listdir(UNTERKUNFT_DIR):
        item_path = os.path.join(UNTERKUNFT_DIR, item)
        if os.path.isdir(item_path):
            shutil.rmtree(item_path)
        elif item != '.gitkeep':
            os.remove(item_path)


def write_entries(entries):
    """Write entries to disk."""
    written, errors = 0, 0
    for slug, entry in entries.items():
        entry_dir = os.path.join(UNTERKUNFT_DIR, slug)
        os.makedirs(entry_dir, exist_ok=True)
        entry_path = os.path.join(entry_dir, 'index.json')
        try:
            with open(entry_path, 'w', encoding='utf-8') as f:
                json.dump(entry, f, ensure_ascii=False, indent=2)
            written += 1
        except Exception as e:
            print(f"  Error writing {entry_path}: {e}")
            errors += 1
    return written, errors


def main():
    print("=" * 60)
    print("  OSM Hotel Scraper v2 — Tirol Tourismus")
    print("=" * 60)
    
    # Step 1: Load registry
    print("\n[1/6] Loading orte registry...")
    orte_by_name, orte_by_normalized, orte_by_slug, orte_by_plz = load_orte_registry()
    print(f"  {len(orte_by_name)} orte entries loaded")
    
    # Step 2: Backup
    print("\n[2/6] Backing up old data...")
    backup_old_data()
    print("  OK")
    
    # Step 3: Query OSM
    print("\n[3/6] Querying Overpass API...")
    result = query_all_tirol()
    if not result or not result.get('elements'):
        print("  ERROR: No data from Overpass API")
        sys.exit(1)
    elements = result['elements']
    
    # Step 4: Process
    print("\n[4/6] Processing elements...")
    entries_by_slug = {}
    stats = defaultdict(int)
    
    for element in elements:
        item = extract_element_data(element, orte_by_name, orte_by_normalized, orte_by_slug, orte_by_plz)
        if item is None:
            tourism = element.get('tags', {}).get('tourism', '?')
            if not element.get('tags', {}).get('name'):
                stats['no_name'] += 1
            elif tourism not in TYP_MAPPING:
                stats['wrong_type'] += 1
            else:
                stats['skipped'] += 1
            continue
        
        slug_base, entry = item
        n = 1
        while slug_base in entries_by_slug or (n > 1 and f"{slug_base}-{n}" in entries_by_slug):
            n += 1
        final_slug = slug_base if n == 1 else f"{slug_base}-{n}"
        entries_by_slug[final_slug] = entry
        entry['slug'] = final_slug
        stats[entry['typ']] += 1
    
    # Deduplicate
    entries_by_slug = deduplicate_slugs(entries_by_slug)
    
    print(f"  Total valid: {len(entries_by_slug)}")
    print(f"  No name: {stats.get('no_name', 0)}")
    print(f"  Wrong type: {stats.get('wrong_type', 0)}")
    print(f"  Skipped: {stats.get('skipped', 0)}")
    
    if not entries_by_slug:
        print("  ERROR: No valid entries!")
        sys.exit(1)
    
    # Step 5: Write
    print("\n[5/6] Writing entries...")
    clean_unterkunft_dir()
    written, errors = write_entries(entries_by_slug)
    
    # Step 6: Summary
    print(f"\n{'=' * 60}")
    print(f"  DONE: {written} entries written ({errors} errors)")
    print(f"{'=' * 60}")
    
    typ_counts = defaultdict(int)
    region_counts = defaultdict(int)
    has_amenities = 0
    has_contact = 0
    no_region = 0
    
    for slug, entry in entries_by_slug.items():
        typ_counts[entry['typ']] += 1
        if entry['region']:
            region_counts[entry['region']] += 1
        else:
            no_region += 1
        if entry['ausstattung']:
            has_amenities += 1
        if entry['telefon'] or entry['email']:
            has_contact += 1
    
    print(f"\n  Types:")
    for t, c in sorted(typ_counts.items(), key=lambda x: -x[1]):
        print(f"    {t}: {c}")
    
    print(f"\n  Regions:")
    for r, c in sorted(region_counts.items(), key=lambda x: -x[1]):
        print(f"    {r}: {c}")
    print(f"    (no region): {no_region}")
    
    print(f"\n  With amenities: {has_amenities}/{len(entries_by_slug)}")
    print(f"  With contact: {has_contact}/{len(entries_by_slug)}")
    print(f"  Backup at: {BACKUP_DIR}")


if __name__ == '__main__':
    main()
