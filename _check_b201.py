import json
for slug in ['waldfrieden', 'waldheim-2', 'waldcafe']:
    f = f'F:/tiroltourismus/src/data/unterkuenfte/{slug}/index.json'
    data = json.load(open(f, encoding='utf-8'))
    desc = data.get('beschreibung', '')
    print(f'{slug}: beschreibung={desc[:100]!r}... len={len(desc)}')
