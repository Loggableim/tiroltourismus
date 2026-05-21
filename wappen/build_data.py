#!/usr/bin/env python3
"""Build clean data JSON for the HTML page with proper umlaut handling."""
import json, os, re

# Read original data
with open('wappen_data.json', 'r', encoding='utf-8') as f:
    raw_data = json.load(f)

bezirk_display = {
    "Imst": "Imst",
    "Statutarstadt Innsbruck": "Innsbruck Stadt",
    "Innsbruck-Land": "Innsbruck-Land",
    "Kitzbühel": "Kitzbühel",
    "Kufstein": "Kufstein",
    "Landeck": "Landeck",
    "Lienz": "Lienz (Osttirol)",
    "Reutte": "Reutte (Außerfern)",
    "Schwaz": "Schwaz"
}

bezirk_keys = {
    "Imst": "imst",
    "Statutarstadt Innsbruck": "statutarstadt_innsbruck",
    "Innsbruck-Land": "innsbruck-land",
    "Kitzbühel": "kitzbühel",
    "Kufstein": "kufstein",
    "Landeck": "landeck",
    "Lienz": "lienz",
    "Reutte": "reutte",
    "Schwaz": "schwaz"
}

# Scan actual files
all_files = {}
base = 'img/orte'
for dirname in os.listdir(base):
    dirpath = os.path.join(base, dirname)
    if not os.path.isdir(dirpath):
        continue
    for f in os.listdir(dirpath):
        if f.endswith('.png'):
            name_no_ext = os.path.splitext(f)[0]
            fp = os.path.join('img/orte', dirname, f).replace(os.sep, '/')
            if dirname not in all_files:
                all_files[dirname] = {}
            all_files[dirname][name_no_ext] = fp

def normalize_name(n):
    """Normalize a name for comparison."""
    n = n.lower().replace(' ', '_')
    return n

def find_file(ort_name, dir_key, file_index):
    if dir_key not in file_index:
        return None
    
    name_lower = ort_name.lower().replace(' ', '_')
    
    # Generate all possible variations
    variations = [name_lower]
    variations.append(name_lower.replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue').replace('ß', 'ss'))
    # With st. instead of st_
    variations.append(name_lower.replace('st.', 'st_'))
    
    for fn, fp in file_index[dir_key].items():
        fn_lower = fn.lower()
        for cand in variations:
            if fn_lower == cand:
                return fp
            # Also try without any special chars
            fn_clean = re.sub(r'[^a-z0-9_]', '', fn_lower)
            cand_clean = re.sub(r'[^a-z0-9_]', '', cand)
            if fn_clean == cand_clean:
                return fp
    
    return None

# Build HTML data
html_data = {"bezirke": []}
missing = []

for raw_key in bezirk_display:
    display_name = bezirk_display[raw_key]
    dir_key = bezirk_keys[raw_key]
    
    bezirk_entry = {
        "name": display_name,
        "key": dir_key,
        "orte": []
    }
    
    for ort in raw_data.get(raw_key, []):
        name = ort['name']
        if name == 'Lage' or name == 'Stadtwappen':
            continue
        
        fp = find_file(name, dir_key, all_files)
        if fp:
            bezirk_entry["orte"].append({"name": name, "img": fp})
        else:
            missing.append(f"{raw_key}/{name}")
    
    html_data["bezirke"].append(bezirk_entry)

# Fix Innsbruck Stadt
for b in html_data["bezirke"]:
    if b['name'] == 'Innsbruck Stadt' and len(b['orte']) == 0:
        if 'statutarstadt_innsbruck' in all_files and 'stadtwappen' in all_files['statutarstadt_innsbruck']:
            b['orte'].append({
                "name": "Innsbruck",
                "img": all_files['statutarstadt_innsbruck']['stadtwappen']
            })

# Summary
total = sum(len(b['orte']) for b in html_data['bezirke'])
print(f"Bezirke: {len(html_data['bezirke'])}")
print(f"Orte mit Wappen: {total}")
print(f"Fehlende: {len(missing)}")
for m in missing:
    print(f"  FEHLT: {m}")
for b in html_data['bezirke']:
    print(f"  {b['name']}: {len(b['orte'])} Orte")

# Save
with open('wappen_page_data.json', 'w', encoding='utf-8') as f:
    json.dump(html_data, f, indent=2, ensure_ascii=False)
print(f"\nGespeichert!")
