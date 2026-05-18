import json, os
path='src/data/gastro'
for s in os.listdir(path):
    fp=os.path.join(path,s,'index.json')
    if os.path.exists(fp):
        d=json.load(open(fp))
        if 'beschreibung' in d:
            print(f'{s}: beschreibung={repr(d["beschreibung"][:80]) if d["beschreibung"] else "empty"}')
        if 'webseite' in d and d['webseite']:
            print(f'{s}: webseite={d["webseite"]}')
        if 'email' in d and d['email']:
            print(f'{s}: email={d["email"]}')
