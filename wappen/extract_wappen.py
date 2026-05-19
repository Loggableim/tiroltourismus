#!/usr/bin/env python3
"""Extrahiert alle Wappen (Bezirke + Gemeinden) aus der Wikipedia-Liste."""
import requests
import json
import re
import sys
import os
from bs4 import BeautifulSoup

url = "https://de.wikipedia.org/wiki/Liste_der_Wappen_in_Tirol"
print(f"Rufe {url} ab...", file=sys.stderr)
response = requests.get(url, headers={'User-Agent': 'TirolWappenBot/1.0'})
soup = BeautifulSoup(response.text, 'lxml')

data = {}
current_bezirk = None

for h2 in soup.find_all('h2'):
    span = h2.find('span', class_='mw-headline')
    if not span:
        continue
    headline = span.get('id', '')
    if headline.startswith('Bezirk_') or headline == 'Statutarstadt_Innsbruck':
        bezirk_name = headline.replace('_', ' ')
        # Bezirksname normalisieren
        display_name = bezirk_name.replace('Bezirk ', '')
        print(f"\n=== {display_name} ===", file=sys.stderr)
        
        # Find the next ul with list items containing coat of arms
        ul = h2.find_next('ul')
        if ul:
            orte = []
            for li in ul.find_all('li', recursive=False):
                img_tag = li.find('img')
                a_tag = li.find('a')
                if img_tag and a_tag:
                    img_url = img_tag.get('src', '')
                    if img_url.startswith('//'):
                        img_url = 'https:' + img_url
                    # Get the highest resolution version
                    img_url = re.sub(r'/\d+px-', '/800px-', img_url)
                    
                    ort_name = a_tag.get('title', '')
                    if not ort_name:
                        ort_name = a_tag.text.strip()
                    
                    print(f"  {ort_name}", file=sys.stderr)
                    orte.append({
                        'name': ort_name,
                        'wappen_url': img_url,
                    })
            if orte:
                data[display_name] = orte

# Save to JSON
out_dir = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(out_dir, 'wappen_data.json')
with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"\n--- GESAMT ---", file=sys.stderr)
total = 0
for k, v in data.items():
    print(f"{k}: {len(v)} Orte", file=sys.stderr)
    total += len(v)
print(f"Gesamt: {total} Wappen in {len(data)} Bezirken", file=sys.stderr)
print(f"\nJSON gespeichert: {json_path}", file=sys.stderr)
print(json.dumps(data, indent=2, ensure_ascii=False))
