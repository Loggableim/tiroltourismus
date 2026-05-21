import json
for slug in ['waldheim-2', 'weinhaus-happ', 'weirather']:
    f = f'F:/tiroltourismus/src/data/unterkuenfte/{slug}/index.json'
    entry = json.load(open(f, encoding='utf-8'))
    desc = entry.get('beschreibung', '')
    print(f'{slug}: len={len(desc)} val={desc[:120]!r}')
