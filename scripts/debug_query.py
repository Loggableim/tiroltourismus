"""Debug: build scraper query exactly and test it."""
import requests, json

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OVERPASS_TIMEOUT = 180
bbox = (46.4, 10.1, 47.6, 12.9)
s, w, n, e = bbox
amenity_types = ["restaurant", "cafe", "pub", "bar", "bistro", "fast_food"]

# Build query exactly like the scraper does
parts = [f"[out:json][timeout:{OVERPASS_TIMEOUT}];("]
for amenity in amenity_types:
    parts.append(f"node({s},{w},{n},{e})[amenity={amenity}];")
for amenity in amenity_types:
    parts.append(f"way({s},{w},{n},{e})[amenity={amenity}];")
parts.append(");out center body;")
query = "".join(parts)

print(f"Query ({len(query)} chars):")
print(repr(query))
print()

# Test with scraper headers
hdrs = {
    "User-Agent": "TirolTourismus-GastroScraper/1.0",
    "Accept": "application/json",
}
print("Sending with scraper headers...", flush=True)
r = requests.post(OVERPASS_URL, data={"data": query}, headers=hdrs, timeout=30)
print(f"Status: {r.status_code}", flush=True)
if r.status_code == 200:
    data = r.json()
    print(f"Elements: {len(data.get('elements',[]))}", flush=True)
else:
    print(f"Body: {r.text[:300]}", flush=True)
