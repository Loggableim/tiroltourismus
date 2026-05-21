#!/usr/bin/env python3
"""
Assign coordinates by Ort lookup.
For entries without coordinates, use their 'ort' field to look up coordinates
from the Orte collection (which we already geocoded successfully).
"""
import json, os

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src', 'data')

# Load all Ort coordinates into a lookup dict
ort_coords = {}
orte_dir = os.path.join(DATA_DIR, 'orte')
if os.path.isdir(orte_dir):
    for item in os.listdir(orte_dir):
        json_path = os.path.join(orte_dir, item, 'index.json')
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                entry = json.load(f)
            if 'koordinaten' in entry:
                name = entry.get('name', '').lower()
                ort_coords[name] = entry['koordinaten']
                # Also map by slug
                ort_coords[item.lower()] = entry['koordinaten']

# Also add manual defaults for known Tirol towns
manual_coords = {
    'innsbruck': {'lat': '47.2654296', 'lng': '11.3927685'},
    'kitzbühel': {'lat': '47.4463585', 'lng': '12.3911473'},
    'kitzbuehel': {'lat': '47.4463585', 'lng': '12.3911473'},
    'längenfeld': {'lat': '47.0731881', 'lng': '10.9712246'},
    'laengenfeld': {'lat': '47.0731881', 'lng': '10.9712246'},
    'mayrhofen': {'lat': '47.1672188', 'lng': '11.8638664'},
    'neustift im stubaital': {'lat': '47.1106408', 'lng': '11.3075790'},
    'neustift': {'lat': '47.1106408', 'lng': '11.3075790'},
    'sölden': {'lat': '46.9666319', 'lng': '11.0072845'},
    'soelden': {'lat': '46.9666319', 'lng': '11.0072845'},
    'st. anton am arlberg': {'lat': '47.1288996', 'lng': '10.2663669'},
    'st. anton': {'lat': '47.1288996', 'lng': '10.2663669'},
    'st-anton': {'lat': '47.1288996', 'lng': '10.2663669'},
}
ort_coords.update(manual_coords)

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
        
        ort_name = entry.get('ort', '').strip().lower()
        coords = ort_coords.get(ort_name)
        
        if coords:
            entry['koordinaten'] = coords
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(entry, f, indent=2, ensure_ascii=False)
            print(f"  ✅ {item}: übernommen von Ort \"{ort_name}\" -> {coords}")
        else:
            print(f"  ❌ {item}: Ort \"{ort_name}\" nicht gefunden in Koordinaten-Lookup")
            # Try a broader search in manual
            for key, val in manual_coords.items():
                if ort_name in key or key in ort_name:
                    entry['koordinaten'] = val
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(entry, f, indent=2, ensure_ascii=False)
                    print(f"    -> manuell gematcht mit \"{key}\"")
                    break

print("=== Unterkünfte ===")
process_collection('unterkuenfte')

print("\n=== Gastro ===")
process_collection('gastro')

print("\n=== Sehenswürdigkeiten ===")
process_collection('sehenswuerdigkeiten')

print("\n✅ Done!")
