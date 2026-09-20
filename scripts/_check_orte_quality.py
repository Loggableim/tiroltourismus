import json
import os
import re

# Check for: empty kurzbeschreibung, mismatched content (description mentions different place)
print("=== CHECK: Empty or mismatched kurzbeschreibung in IT orte ===\n")

base = 'src/data/it/orte'
empty = []
mismatch = []
too_long = []

for d in sorted(os.listdir(base)):
    f = f'{base}/{d}/index.json'
    if not os.path.exists(f):
        continue
    try:
        data = json.load(open(f, encoding='utf-8'))
        name = data.get('name') or d
        kb = data.get('kurzbeschreibung') or ''
        be = data.get('beschreibung') or ''

        if len(kb) < 20:
            empty.append((d, len(kb), kb[:60]))
        elif len(kb) > 500:
            too_long.append((d, len(kb)))
        else:
            # Check if description mentions a DIFFERENT major place
            # (e.g. Alpbach card showing Innsbruck text)
            other_places = ['Innsbruck', 'Ötztal', 'Zillertal', 'Kitzbühel', 'Achensee', 'Stubaital']
            name_norm = name.lower().replace(' ', '')
            for op in other_places:
                if op.lower() in kb.lower() and op.lower() not in name_norm:
                    # Description mentions another place prominently
                    if kb.lower().find(op.lower()) < 80:  # early mention = likely wrong
                        mismatch.append((d, name, op, kb[:80]))
                        break
    except Exception:
        pass

print(f"EMPTY (<20 chars): {len(empty)}")
for d, l, p in empty[:10]:
    print(f"  {d}: {l} chars | {p}")

print(f"\nTOO LONG (>500 chars): {len(too_long)}")
for d, l in too_long[:10]:
    print(f"  {d}: {l} chars")

print(f"\nMISMATCH (mentions other place): {len(mismatch)}")
for d, name, op, p in mismatch[:10]:
    print(f"  {d} ({name}) mentions {op}: {p}")
