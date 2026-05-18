import json, os

# --- Orte regions ---
path = 'src/data/orte'
slugs = [s for s in os.listdir(path) if os.path.isdir(os.path.join(path, s))]
regions = {}
for s in slugs:
    d = json.load(open(os.path.join(path, s, 'index.json')))
    r = d.get('region', '?')
    regions.setdefault(r, []).append(d['name'])

print(f'Total orte: {len(slugs)}')
print(f'Regions ({len(regions)}):')
for r in sorted(regions):
    print(f'  {r}: {len(regions[r])} orte')

# Build city->region mapping
print('\nCITY->REGION mapping (first 50):')
city_region = {}
for s in sorted(slugs):
    d = json.load(open(os.path.join(path, s, 'index.json')))
    city_region[d['name'].lower()] = d.get('region', '?')
    city_region[s.lower()] = d.get('region', '?')

# Also index by slug
for s in sorted(slugs)[:50]:
    d = json.load(open(os.path.join(path, s, 'index.json')))
    print(f"  {d['name']} (slug={s}) -> region={d.get('region','?')}")

# --- Gastro schemas ---
print('\n--- Gastro schema analysis ---')
path2 = 'src/data/gastro'
gastro_slugs = sorted([s for s in os.listdir(path2) if os.path.isdir(os.path.join(path2, s))])
print(f'Total gastro: {len(gastro_slugs)}')
fields_set = set()
kategorien = set()
for s in gastro_slugs:
    d = json.load(open(os.path.join(path2, s, 'index.json')))
    fields_set.update(d.keys())
    if d.get('kategorie'): kategorien.add(d['kategorie'])

print('Fields:', sorted(fields_set))
print('Kategorien:', sorted(kategorien))
