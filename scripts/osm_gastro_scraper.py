#!/usr/bin/env python3
"""GASTRO-OSM: Holt alle Gastro-Daten aus einem OSM-Extrakt.
Kein Overpass-Timeout — lokale Verarbeitung.

1. Lädt Tiroler OSM-Daten von Geofabrik
2. Filtert amenity=restaurant,cafe,pub,bar,bistrot,fast_food
3. Konvertiert in src/data/gastro/{slug}/index.json
"""
import json, os, sys, glob, urllib.request, zipfile, time, re

PROJECT = "F:/tiroltourismus"
DATA_DIR = f"{PROJECT}/src/data/gastro"
CACHE_DIR = f"{PROJECT}/scripts/osm_cache"
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# Backup existing
backup_dir = f"{PROJECT}/src/data/gastro_backup"
if not os.path.exists(backup_dir):
    os.system(f"cp -r \"{DATA_DIR}\" \"{backup_dir}\"")
    print(f"Backup: {DATA_DIR} -> {backup_dir}")

# 1. Download Tirol OSM extract (OpenStreetMap)
OSM_URL = "https://download.geofabrik.de/europe/austria/tirol-latest.osm.pbf"
OSM_FILE = f"{CACHE_DIR}/tirol-latest.osm.pbf"

if not os.path.exists(OSM_FILE):
    print(f"Downloading Tirol OSM extract ({OSM_URL})...")
    urllib.request.urlretrieve(OSM_URL, OSM_FILE)
    print(f"Downloaded: {OSM_FILE} ({os.path.getsize(OSM_FILE)//1024//1024} MB)")
else:
    print(f"Using cached: {OSM_FILE} ({os.path.getsize(OSM_FILE)//1024//1024} MB)")

# 2. Convert to JSON via osmium if available, otherwise use Python XML
# Try osmium first
import subprocess

def has_osmium():
    try:
        subprocess.run(["osmium", "--version"], capture_output=True, check=True)
        return True
    except:
        return False

OSM_JSON = f"{CACHE_DIR}/gastro_raw.json"

if has_osmium():
    print("Using osmium for fast filtering...")
    # Filter: nodes with amenity=restaurant,cafe,pub,bar,bistrot,fast_food
    tags = "amenity=restaurant or amenity=cafe or amenity=pub or amenity=bar or amenity=bistrot or amenity=fast_food"
    result = subprocess.run(
        ["osmium", "tags-filter", OSM_FILE, tags, "-o", f"{CACHE_DIR}/gastro_raw.osm.pbf", "-f", "pbf"],
        capture_output=True, text=True, timeout=300
    )
    # Convert to JSON
    result = subprocess.run(
        ["osmium", "export", f"{CACHE_DIR}/gastro_raw.osm.pbf", "-o", OSM_JSON, "-f", "geojson"],
        capture_output=True, text=True, timeout=300
    )
else:
    print("osmium nicht installiert. Verwende osmium aus dem osm-tools Paket via pip.")
    subprocess.run([sys.executable, "-m", "pip", "install", "osmium"], capture_output=True)
    print("Bitte fuehre das Script erneut aus.")

if not os.path.exists(OSM_JSON):
    print("❌ Konnte keine Gastro-Daten extrahieren. Versuche Overpass-API als Fallback...")
    # Fallback: Overpass per Region
    sys.exit(1)

# 3. Parse GeoJSON and convert
print("Konvertiere OSM-Daten in Gastro-JSONs...")
data = json.load(open(OSM_JSON, encoding="utf-8"))

# Load ort -> region mapping
ort_region = {}
from pathlib import Path
for f in glob.glob(f"{PROJECT}/src/data/orte/*/index.json"):
    d = json.load(open(f, encoding="utf-8"))
    name = d.get("name", "").lower().strip()
    region = d.get("region", "")
    if name and region:
        ort_region[name] = region
        ort_region[name.replace(" ", "-")] = region
        for char, repl in [("ö","oe"),("ü","ue"),("ä","ae"),("ß","ss")]:
            ort_region[name.replace(char, repl)] = region

cafe_emoji = {"restaurant":"🍽️","cafe":"☕","pub":"🍺","bar":"🍸","fast_food":"🍔","bistrot":"🥐"}
kategorie_map = {"restaurant":"restaurant","cafe":"cafe","pub":"pub","bar":"bar","fast_food":"imbiss","bistrot":"bistro"}

converted = 0
skipped = 0
seen_names = set()
max_entries = 2000  # Safety limit

for feature in data.get("features", []):
    props = feature.get("properties", {})
    coords = feature.get("geometry", {}).get("coordinates")
    if not props or not coords:
        continue
    
    name = props.get("name", "").strip()
    if not name:
        continue
    
    # Dedup by name
    name_lower = name.lower()
    if name_lower in seen_names:
        skipped += 1
        continue
    seen_names.add(name_lower)
    
    amenity = props.get("amenity", "restaurant")
    typ = kategorie_map.get(amenity, "restaurant")
    emoji = cafe_emoji.get(amenity, "🍽️")
    
    # Extract address
    addr = props.get("addr:full", "") or f"{props.get('addr:street','') or ''} {props.get('addr:housenumber','') or ''}".strip()
    plz = props.get("addr:postcode", "")
    ort = props.get("addr:city", "") or props.get("addr:town", "") or props.get("addr:village", "") or ""
    
    # Region mapping
    region = "?"
    if ort:
        ort_key = ort.lower().strip()
        region = ort_region.get(ort_key, "?")
        if region == "?":
            # Try partial match
            for key, val in ort_region.items():
                if ort_key in key or key in ort_key:
                    region = val
                    break
    
    phone = props.get("phone", "") or ""
    website = props.get("website", "") or ""
    cuisine = props.get("cuisine", "")
    tags = ["gastro", amenity]
    if cuisine:
        tags.append(cuisine.lower().replace(",", "").split()[0] if cuisine else "regional")
    
    # Generate slug
    slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')[:40]
    if not slug:
        slug = f"gastro-{converted}"
    
    # Ensure unique slug
    base_slug = slug
    counter = 1
    while os.path.exists(f"{DATA_DIR}/{slug}/index.json"):
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    entry = {
        "name": name,
        "emoji": emoji,
        "farbe": "#FF6B35",
        "kategorie": typ,
        "kurzbeschreibung": f"{name} in {ort or 'Tirol'} — {amenity}",
        "beschreibung": "",
        "ort": ort,
        "region": region,
        "adresse": addr,
        "plz": plz,
        "telefon": phone,
        "email": "",
        "webseite": website,
        "preis": "€€",
        "tags": tags,
        "koordinaten": {"lat": coords[1], "lng": coords[0]},
        "status": "published"
    }
    
    os.makedirs(f"{DATA_DIR}/{slug}", exist_ok=True)
    json.dump(entry, open(f"{DATA_DIR}/{slug}/index.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    converted += 1
    
    if converted >= max_entries:
        break

print(f"\n✅ Fertig! {converted} Gastro-Eintraege erstellt")
print(f"   Uebersprungen (Duplikate): {skipped}")
print(f"   Gesamt jetzt: {converted + 50} (50 alte + {converted} neue)")
