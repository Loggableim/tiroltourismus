#!/usr/bin/env python3
"""Update the page data to include bezirk-level images."""
import json

# Read current page data
with open('wappen_page_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Bezirk image mapping (district maps + Innsbruck COA)
bezirk_images = {
    "imst": "img/bezirke/imst.png",
    "statutarstadt_innsbruck": "img/bezirke/innsbruck_stadt.png",
    "innsbruck-land": "img/bezirke/innsbruck-land.png",
    "kitzbühel": "img/bezirke/kitzbühel.png",
    "kufstein": "img/bezirke/kufstein.png",
    "landeck": "img/bezirke/landeck.png",
    "lienz": "img/bezirke/lienz.png",
    "reutte": "img/bezirke/reutte.png",
    "schwaz": "img/bezirke/schwaz.png",
}

for b in data['bezirke']:
    if b['key'] in bezirk_images:
        b['img'] = bezirk_images[b['key']]
    else:
        # Fallback to first ort
        b['img'] = b['orte'][0]['img'] if b['orte'] else ''

with open('wappen_page_data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("Bezirksbilder hinzugefügt!")
for b in data['bezirke']:
    print(f"  {b['name']}: {b['img']}")
