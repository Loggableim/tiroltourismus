#!/usr/bin/env python3
"""Check which entries still need descriptions."""
import json, glob, os

DATA_DIR = os.path.join('src', 'data', 'unterkuenfte')
pending = []
for f in sorted(glob.glob(os.path.join(DATA_DIR, '*', 'index.json'))):
    data = json.load(open(f, encoding='utf-8'))
    if not data.get('beschreibung') or len(data.get('beschreibung', '').strip()) < 10:
        slug = os.path.basename(os.path.dirname(f))
        pending.append((slug, data.get('name','?'), data.get('ort',''), data.get('region','')))
print(f'{len(pending)} pending:')
for s, n, o, r in pending:
    print(f'  {s}: {n} / {o} / {r}')
