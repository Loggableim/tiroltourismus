import json
# Create the 5 missing entries from batch files
missing = [
    ("zeh-am-see", "Zeh am See", "Waltenhofen", "ferienwohnung", ""),
    ("zeltplatz-falkencamp", "Zeltplatz Falkencamp", "Schwangau", "camping", ""),
    ("zeltplatz-leitzachtal", "Zeltplatz Leitzachtal", "Weyarn", "camping", ""),
    ("zeltplatz-oberhart", "Zeltplatz Oberhart", "Kolbermoor", "camping", ""),
    ("zentralalpen-stellplatz-trins-im-gschnitztal", "Zentralalpen-Stellplatz Trins im Gschnitztal", "Trins", "camping", "innsbruck"),
]

base = "F:/tiroltourismus/src/data/unterkuenfte"
for slug, name, ort, typ, region in missing:
    fpath = base + "/" + slug + "/index.json"
    dirpath = base + "/" + slug
    import os
    os.makedirs(dirpath, exist_ok=True)
    entry = {
        "name": name,
        "slug": slug,
        "typ": typ,
        "ort": ort,
        "region": region,
        "beschreibung": "",
        "tags": [],
        "ausstattung": [],
        "tier": "basic"
    }
    json.dump(entry, open(fpath, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print("Created: " + fpath)
