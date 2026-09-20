import json
import os

# Check ALL languages for empty/missing descriptions in orte
print("=== CHECK: Missing descriptions in orte (all languages) ===\n")

LANGS = ['de', 'en', 'fr', 'cs', 'nl', 'it', 'es', 'zh']

for lang in LANGS:
    base = 'src/data/orte' if lang == 'de' else f'src/data/{lang}/orte'
    if not os.path.exists(base):
        print(f"{lang}: NO DIR")
        continue
    no_kb = []
    no_be = []
    total = 0
    for d in sorted(os.listdir(base)):
        f = f'{base}/{d}/index.json'
        if not os.path.exists(f):
            continue
        try:
            data = json.load(open(f, encoding='utf-8'))
            total += 1
            kb = (data.get('kurzbeschreibung') or '').strip()
            be = (data.get('beschreibung') or '').strip()
            if len(kb) < 20:
                no_kb.append(d)
            if len(be) < 50:
                no_be.append(d)
        except Exception:
            pass
    print(f"{lang}: {total} orte | no kurzbeschreibung: {len(no_kb)} | no beschreibung: {len(no_be)}")
    if no_kb:
        print(f"    no kb: {no_kb[:8]}")
    if no_be:
        print(f"    no be: {no_be[:8]}")
