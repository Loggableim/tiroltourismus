#!/usr/bin/env python3
"""Download all coat of arms images from Wikipedia with rate limiting."""
import json, requests, os, re, sys, time

def download_image(url, filepath, retries=3):
    """Download with proper headers and rate limiting."""
    # Clean URL - remove query params
    url = url.split('?')[0]
    if url.startswith('//'):
        url = 'https:' + url
    # Use smaller size that definitely works
    url = re.sub(r'/\d+px-', '/250px-', url)
    
    headers = {
        'User-Agent': 'TirolWappenBot/1.0 (https://tiroltourismus.com)',
        'Accept': 'image/webp,image/png,image/*,*/*;q=0.8',
    }
    
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=headers, timeout=30)
            if r.status_code == 200:
                content_type = r.headers.get('content-type', '')
                if 'text/html' in content_type:
                    return False
                with open(filepath, 'wb') as f:
                    f.write(r.content)
                return True
            elif r.status_code == 429:
                wait = (attempt + 1) * 5
                print(f"    429 - warte {wait}s...", file=sys.stderr)
                time.sleep(wait)
            else:
                print(f"    HTTP {r.status_code}", file=sys.stderr)
                return False
        except Exception as e:
            print(f"    Error: {e}", file=sys.stderr)
            if attempt < retries - 1:
                time.sleep(5)
    return False

# Download Bezirksbilder
print("=== Bezirksbilder ===", file=sys.stderr)
with open('bezirk_wappen.json', 'r', encoding='utf-8') as f:
    bezirke = json.load(f)

for i, (name, url) in enumerate(bezirke.items()):
    filename = name.lower().replace(' ', '_')
    filename = ''.join(c for c in filename if c.isalnum() or c in '._-')
    filepath = f"img/bezirke/{filename}.png"
    
    print(f"  ({i+1}/9) {name}... ", end='', file=sys.stderr)
    if download_image(url, filepath):
        size = os.path.getsize(filepath)
        print(f"OK ({size} bytes)", file=sys.stderr)
    else:
        print(f"FAILED", file=sys.stderr)
    time.sleep(1.5)  # Rate limit

# Download Ortswappen
print("\n=== Ortswappen ===", file=sys.stderr)
with open('wappen_data.json', 'r', encoding='utf-8') as f:
    bezirke_orte = json.load(f)

total = sum(len(orte) for orte in bezirke_orte.values())
done = 0
count = 0
for bezirk, orte in bezirke_orte.items():
    bezirk_dir = bezirk.lower().replace(' ', '_')
    bezirk_dir = ''.join(c for c in bezirk_dir if c.isalnum() or c in '_-')
    os.makedirs(f"img/orte/{bezirk_dir}", exist_ok=True)
    
    for ort in orte:
        name = ort['name']
        url = ort['wappen_url']
        
        filename = name.lower().replace(' ', '_')
        filename = ''.join(c for c in filename if c.isalnum() or c in '._-')
        filepath = f"img/orte/{bezirk_dir}/{filename}.png"
        
        if os.path.exists(filepath) and os.path.getsize(filepath) > 100:
            done += 1
            continue
        
        count += 1
        if count % 5 == 0:
            print(f"  ({done}/{total}) - warte kurz...", file=sys.stderr)
            time.sleep(2)  # Extra pause every 5
        
        print(f"  {bezirk}/{name}... ", end='', file=sys.stderr)
        if download_image(url, filepath):
            done += 1
            print(f"OK", file=sys.stderr)
        else:
            print(f"FAILED", file=sys.stderr)
        
        time.sleep(1.2)  # Rate limit between requests

print(f"\nFertig! {done}/{total} Wappen heruntergeladen", file=sys.stderr)
