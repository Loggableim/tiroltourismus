import json
import os

# Final check: what's missing
LANGS = ['en', 'fr', 'cs', 'nl', 'it', 'es', 'zh']

print("=== MISSING DESCRIPTIONS (orte) ===\n")
for lang in LANGS:
    base = f'src/data/{lang}/orte'
    if not os.path.exists(base):
        continue
    no_kb = []
    no_be = []
    for d in sorted(os.listdir(base)):
        f = f'{base}/{d}/index.json'
        if not os.path.exists(f):
            continue
        try:
            data = json.load(open(f, encoding='utf-8'))
            kb = (data.get('kurzbeschreibung') or '').strip()
            be = (data.get('beschreibung') or '').strip()
            if len(kb) < 20:
                no_kb.append(d)
            if len(be) < 50:
                no_be.append(d)
        except Exception:
            pass
    print(f"{lang}: no_kb={len(no_kb)} {no_kb}")
    print(f"{lang}: no_be={len(no_be)} {no_be[:15]}")
    print()
