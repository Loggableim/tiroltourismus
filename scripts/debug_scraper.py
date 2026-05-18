"""Debug: run the scraper in a more controlled way."""
import sys
sys.path.insert(0, "F:/tiroltourismus/scripts")

# Execute the scraper as a module but with debug output
import importlib.util
spec = importlib.util.spec_from_file_location("scraper", "F:/tiroltourismus/scripts/osm_gastro_scraper.py")
mod = importlib.util.module_from_spec(spec)

# Adjust settings before running
import os
os.environ["DRY_RUN"] = "1"
os.environ["OSM_TIMEOUT"] = "120"

spec.loader.exec_module(mod)

# Now manually call parts
import json, requests
from collections import defaultdict

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OVERPASS_TIMEOUT = 120
TIROL_BBOX = (46.4, 10.1, 47.6, 12.9)
s, w, n, e = TIROL_BBOX

node_types = ["restaurant", "cafe", "pub", "bar", "bistro", "fast_food"]
parts = [f"[out:json][timeout:{OVERPASS_TIMEOUT}];("]
for amenity in node_types:
    parts.append(f"node({s},{w},{n},{e})[amenity={amenity}];")
parts.append(");out center body;")
query = "".join(parts)

print(f"Query len: {len(query)}", flush=True)
print(f"Sending...", flush=True)

import time
t0 = time.time()
resp = requests.post(
    OVERPASS_URL,
    data={"data": query},
    headers={"User-Agent": "OverpassTurbo/1.0", "Accept": "application/json"},
    timeout=150,
)
elapsed = time.time() - t0
print(f"Response: HTTP {resp.status_code} in {elapsed:.1f}s", flush=True)
if resp.status_code == 200:
    data = resp.json()
    print(f"Elements: {len(data.get('elements',[]))}", flush=True)
else:
    print(f"Body: {resp.text[:200]}", flush=True)
