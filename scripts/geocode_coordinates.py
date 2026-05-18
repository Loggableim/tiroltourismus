#!/usr/bin/env python3
"""
Geocode Orte und Unterkünfte via Nominatim and add 'koordinaten' field
to their index.json if not already present.
Respects 1 req/s rate limit.
"""
import json, os, time, urllib.request, urllib.parse, sys

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src', 'data')

def geocode(query, retries=3):
    """Geocode a place name to {lat, lng} using Nominatim."""
    url = 'https://nominatim.openstreetmap.org/search?' + urllib.parse.urlencode({
        'q': query,
        'format': 'json',
        'limit': 1,
    })
    headers = {'User-Agent': 'TirolTourismus/2.0 (geocoding@tiroltourismus.com)'}
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
            if data and len(data) > 0:
                return {'lat': data[0]['lat'], 'lng': data[0]['lon']}
            return None
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2)
            else:
                print(f"  Fehler: {e}")
                return None

def add_coordinates_to_collection(collection, fields_for_query_func):
    """Geocode all entries in a collection that don't have koordinaten."""
    dir_path = os.path.join(DATA_DIR, collection)
    if not os.path.isdir(dir_path):
        return
    
    for item in sorted(os.listdir(dir_path)):
        json_path = os.path.join(dir_path, item, 'index.json')
        if not os.path.exists(json_path):
            continue
        
        with open(json_path, 'r', encoding='utf-8') as f:
            entry = json.load(f)
        
        if 'koordinaten' in entry and entry['koordinaten']:
            print(f"  ✅ {item}: bereits vorhanden")
            continue
        
        query = fields_for_query_func(entry, item)
        if not query:
            print(f"  ⏭️  {item}: keine Query möglich")
            continue
        
        print(f"  🔍 {item}: geocode \"{query}\"...", end=' ', flush=True)
        coords = geocode(f"{query}, Tirol, Österreich")
        if coords:
            entry['koordinaten'] = coords
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(entry, f, indent=2, ensure_ascii=False)
            print(f"✅ {coords['lat']}, {coords['lng']}")
        else:
            print("❌ nicht gefunden")
        
        time.sleep(1.1)  # Rate limit: max 1 req/s

print("=== Orte ===")
add_coordinates_to_collection('orte', lambda e, s: f"{e.get('name', s)}, Tirol")

print("\n=== Unterkünfte ===")
add_coordinates_to_collection('unterkuenfte', lambda e, s: 
    f"{e.get('name', s)} in {e.get('ort', 'Tirol')}, Tirol")

print("\n=== Gastro ===")
add_coordinates_to_collection('gastro', lambda e, s: 
    f"{e.get('name', s)} in {e.get('ort', 'Tirol')}, Tirol")

print("\n=== Sehenswürdigkeiten ===")
add_coordinates_to_collection('sehenswuerdigkeiten', lambda e, s: 
    f"{e.get('name', s)}, Tirol")

print("\n✅ Geocoding complete!")
