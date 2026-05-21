#!/usr/bin/env python3
"""
Second pass: geocode entries that failed the first time.
For Unterkünfte/Gastro: fall back to just the Ort if the venue name didn't work.
"""
import json, os, time, urllib.request, urllib.parse

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src', 'data')

def geocode(query, retries=3):
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
                return None

def process_collection(collection):
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
            continue
        
        # Fallback: use just the Ort name plus Tirol
        fallback = f"{entry.get('ort', '')}, Tirol"
        if fallback.strip() == ", Tirol":
            # Last resort: try the entry name itself
            fallback = f"{entry.get('name', item)}, Tirol, Österreich"
        
        print(f"  🔍 {item}: geocode \"{fallback}\"...", end=' ', flush=True)
        coords = geocode(fallback)
        if coords:
            entry['koordinaten'] = coords
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(entry, f, indent=2, ensure_ascii=False)
            print(f"✅ {coords['lat']}, {coords['lng']}")
        else:
            print("❌ immer noch nicht gefunden")
        time.sleep(1.1)

print("=== Unterkünfte (2. Versuch) ===")
process_collection('unterkuenfte')

print("\n=== Gastro (2. Versuch) ===")
process_collection('gastro')

print("\n=== Sehenswürdigkeiten (2. Versuch) ===")
process_collection('sehenswuerdigkeiten')

print("\n✅ Done!")
