import json
for slug in ['waldcafe-2', 'waldfrieden', 'waldheim-2']:
    f = f'src/data/unterkuenfte/{slug}/index.json'
    data = json.load(open(f, encoding='utf-8'))
    print(f'{slug}:')
    print(f'  beschreibung: {str(data.get("beschreibung",""))[:80]!r}')
    print(f'  tier: {data.get("tier")}')
    print(f'  tags: {data.get("tags")}')
    print()
