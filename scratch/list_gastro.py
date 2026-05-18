import json, os
base = "F:/tiroltourismus/src/data/gastro"
for slug in sorted(os.listdir(base)):
    path = os.path.join(base, slug, "index.json")
    if os.path.exists(path):
        with open(path) as f:
            d = json.load(f)
        print(f"  {slug:35s} | ort={d.get('ort',''):25s} | region={d.get('region',''):15s} | kat={d.get('kategorie',''):15s}")
