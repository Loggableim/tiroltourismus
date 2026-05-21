"""Test if User-Agent makes a difference."""
import requests

ov = "https://overpass-api.de/api/interpreter"
q = '[out:json][timeout:120];(node(46.4,10.1,47.6,12.9)[amenity=restaurant];node(46.4,10.1,47.6,12.9)[amenity=cafe];node(46.4,10.1,47.6,12.9)[amenity=pub];node(46.4,10.1,47.6,12.9)[amenity=bar];node(46.4,10.1,47.6,12.9)[amenity=bistro];node(46.4,10.1,47.6,12.9)[amenity=fast_food];);out center body;'

configs = [
    ("Test/1.0 + Accept json", {"User-Agent": "Test/1.0", "Accept": "application/json"}),
    ("scraper UA + Accept json", {"User-Agent": "TirolTourismus-GastroScraper/1.0", "Accept": "application/json"}),
    ("only Accept json", {"User-Agent": "", "Accept": "application/json"}),
    ("default UA (python-requests)", {}),
    ("curl-like", {"User-Agent": "curl/8.17.0", "Accept": "*/*"}),
]

for name, hdrs in configs:
    # Remove empty values
    hdrs = {k: v for k, v in hdrs.items() if v}
    print(f"--- {name} ---", flush=True)
    try:
        r = requests.post(ov, data={"data": q}, headers=hdrs, timeout=30)
        print(f"  Status: {r.status_code}", flush=True)
        if r.status_code == 200:
            print(f"  Elements: {len(r.json().get('elements',[]))}", flush=True)
        else:
            print(f"  Body: {r.text[:80]}", flush=True)
    except Exception as e:
        print(f"  Error: {e}", flush=True)
