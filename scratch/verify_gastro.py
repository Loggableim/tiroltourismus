import json, os

base = "F:/tiroltourismus/src/data/gastro"
new_slugs = [
    "gasthof-kufstein",
    "seerestaurant-thiersee",
    "gasthof-soell",
    "wirtshaus-ebbs",
    "restaurant-wilde-kaiser",
    "gasthof-stubai",
    "restaurant-fulpmes",
    "alpengasthof-arlberg",
    "gasthof-umhausen",
    "restaurant-ellmau",
    "gasthof-st-johann",
]

print("=== VERIFYING NEW GASTRO ENTRIES ===")
all_ok = True
required_keys = ["name", "slug", "region", "ort", "kategorie", "kurzbeschreibung", "emoji", "farbe", "tags", "status", "koordinaten"]
valid_kategorien = ["tirolerisch", "cafe", "almwirtschaft", "bar", "regional", "international", "eissalon", "pizzeria"]
valid_statuses = ["published", "draft"]
total_new = 0

for slug in new_slugs:
    path = os.path.join(base, slug, "index.json")
    if not os.path.exists(path):
        print(f"  ❌ {slug}: NOT FOUND")
        all_ok = False
        continue
    
    with open(path) as f:
        data = json.load(f)
    
    total_new += 1
    issues = []
    
    for key in required_keys:
        if key not in data:
            issues.append(f"missing key: {key}")
    
    if data.get("slug") != slug:
        issues.append(f"slug mismatch: expected '{slug}', got '{data.get('slug')}'")
    
    if data.get("status") not in valid_statuses:
        issues.append(f"invalid status: {data.get('status')}")
    
    if data.get("kategorie") not in valid_kategorien:
        issues.append(f"new kategorie: {data.get('kategorie')}")
    
    if "lat" not in data.get("koordinaten", {}):
        issues.append("koordinaten missing lat")
    if "lng" not in data.get("koordinaten", {}):
        issues.append("koordinaten missing lng")
    
    if not data.get("tags"):
        issues.append("no tags")
    
    if issues:
        print(f"  ⚠️  {slug}: {'; '.join(issues)}")
    else:
        print(f"  ✅ {slug}: {data.get('name')} ({data.get('region')}/{data.get('ort')})")

# Now re-run the full analysis to show the improvement
print(f"\n\n=== NEW TOTAL: {total_new} entries created ===")

from collections import Counter

# Count gastro by region
gastro_regions = Counter()
for slug in os.listdir(base):
    path = os.path.join(base, slug, "index.json")
    if os.path.exists(path):
        with open(path) as f:
            g = json.load(f)
        gastro_regions[g.get("region", "?")] += 1

print("\n=== UPDATED GASTRO BY REGION ===")
for r, c in sorted(gastro_regions.items(), key=lambda x: -x[1]):
    ok = "✅" if c >= 3 else "⚠️"
    print(f"  {ok} {r:20s}: {c}")
