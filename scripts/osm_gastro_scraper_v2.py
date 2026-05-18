#!/usr/bin/env python3
"""GASTRO-OSM v2: Holt Gastro aus Overpass, Region für Region.
Kein Budget-Problem — jeder Request ist klein + schnell."""
import json, os, sys, glob, urllib.request, time, re

PROJECT = "F:/tiroltourismus"
DATA_DIR = f"{PROJECT}/src/data/gastro"
CACHE_DIR = f"{PROJECT}/scripts/osm_cache"
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# Backup alte Daten
backup_dir = f"{PROJECT}/src/data/gastro_backup"
if not os.path.exists(backup_dir) and len(glob.glob(f"{DATA_DIR}/*/index.json")) > 10:
    os.system(f'cp -r "{DATA_DIR}" "{backup_dir}"')
    print(f"✅ Backup: {backup_dir}")

# Ort → Region Mapping
ort_region = {}
for f in glob.glob(f"{PROJECT}/src/data/orte/*/index.json"):
    d = json.load(open(f, encoding="utf-8"))
    name = d.get("name", "").lower().strip()
    region = d.get("region", "")
    bezirk = d.get("bezirk", "")
    if name and region:
        ort_region[name] = region
        # Ohne Umlaute
        for a, b in [("ö","oe"),("ü","ue"),("ä","ae"),("ß","ss")]:
            ort_region[name.replace(a, b)] = region

# Bounding Box für ganz Tirol in 8 Sub-Regionen
REGIONS = {
    "west": "47.0,10.1,47.4,10.8",    # Arlberg, Landeck, Paznaun
    "nordwest": "47.3,10.3,47.6,10.9", # Außerfern, Lechtal
    "nord": "47.4,10.9,47.6,11.7",     # Innsbruck, Hall
    "nordost": "47.4,11.7,47.6,12.4",  # Kufstein, Kitzbühel
    "mitte": "47.1,10.9,47.4,11.5",    # Stubaital, Wipptal
    "ost": "47.0,11.5,47.4,12.6",      # Kitzbühel, Zillertal, Schwaz
    "suedwest": "46.8,10.5,47.1,11.0", # Ötztal, Kaunertal, Imst
    "suedost": "46.7,11.8,47.0,12.8",  # Osttirol
}

cafe_emoji = {"restaurant":"🍽️","cafe":"☕","pub":"🍺","bar":"🍸","fast_food":"🍔","bistrot":"🥐","ice_cream":"🍦"}
kategorie_map = {"restaurant":"restaurant","cafe":"cafe","pub":"pub","bar":"bar","fast_food":"imbiss","bistrot":"bistro","ice_cream":"eiscafe"}

converted = 0
seen_names = set()

for region_name, bbox in REGIONS.items():
    print(f"\n🌍 Region: {region_name} (bbox: {bbox})")
    
    overpass_query = f"""
    [out:json][timeout:120];
    (
      node["amenity"~"restaurant|cafe|pub|bar|bistrot|fast_food|ice_cream"]({bbox});
    );
    out body;
    """
    
    try:
        req = urllib.request.Request(
            "https://overpass-api.de/api/interpreter",
            data=("data=" + overpass_query).encode(),
            headers={"User-Agent": "TirolTourismus/2.0"},
            method="POST"
        )
        resp = urllib.request.urlopen(req, timeout=120)
        data = json.loads(resp.read())
        elements = data.get("elements", [])
        print(f"   Gefunden: {len(elements)} Einträge")
        
        for elem in elements:
            tags = elem.get("tags", {})
            name = (tags.get("name", "") or "").strip()
            if not name:
                continue
            
            name_lower = name.lower()
            if name_lower in seen_names:
                continue
            seen_names.add(name_lower)
            
            amenity = tags.get("amenity", "restaurant")
            typ = kategorie_map.get(amenity, "restaurant")
            emoji = cafe_emoji.get(amenity, "🍽️")
            
            lat = elem.get("lat", 0)
            lon = elem.get("lon", 0)
            
            ort = tags.get("addr:city", "") or tags.get("addr:town", "") or tags.get("addr:village", "") or ""
            region = "?"
            if ort:
                region = ort_region.get(ort.lower().strip(), "?")
                if region == "?":
                    for key, val in ort_region.items():
                        if ort.lower()[:5] in key:
                            region = val
                            break
            
            addr = f"{tags.get('addr:street','') or ''} {tags.get('addr:housenumber','') or ''}".strip()
            plz = tags.get("addr:postcode", "")
            phone = tags.get("phone", "") or ""
            website = tags.get("website", "") or tags.get("contact:website", "") or ""
            cuisine = tags.get("cuisine", "")
            
            tags_list = ["gastro"]
            if cuisine:
                tags_list.append(cuisine.split(";")[0].strip().lower().replace(",",""))
            
            try:
                phone_clean = phone.replace(" ", "").replace("/", "").replace("-", "")
                if phone_clean.startswith("+43") or phone_clean.startswith("0043") or phone_clean.startswith("0"):
                    pass
                else:
                    phone = ""
            except:
                phone = ""
            
            slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')[:35]
            if not slug:
                slug = f"gastro-{converted}"
            
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
                "kurzbeschreibung": f"{name} in {ort or 'Tirol'}",
                "beschreibung": "",
                "ort": ort,
                "region": region,
                "plz": plz,
                "adresse": addr,
                "telefon": phone,
                "email": "",
                "webseite": website,
                "preis": "€€",
                "tags": tags_list,
                "koordinaten": {"lat": lat, "lng": lon},
                "status": "published"
            }
            
            os.makedirs(f"{DATA_DIR}/{slug}", exist_ok=True)
            json.dump(entry, open(f"{DATA_DIR}/{slug}/index.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
            converted += 1
        
        time.sleep(2)  # Politesse zwischen Regionen
        
    except Exception as e:
        print(f"   ❌ Fehler: {e}")
        time.sleep(5)
        continue

print(f"\n✅ Fertig! {converted} neue Gastro-Einträge aus OSM")
print(f"   Gesamt jetzt: {len(glob.glob(f'{DATA_DIR}/*/index.json'))} Einträge")
