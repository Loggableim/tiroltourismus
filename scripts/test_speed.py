"""Quick responsiveness test."""
import requests, time

ov = "https://overpass-api.de/api/interpreter"
hdrs = {"User-Agent": "OverpassTurbo/1.0", "Accept": "application/json"}
q = '[out:json][timeout:30];(node(46.4,10.1,47.6,12.9)[amenity=restaurant];node(46.4,10.1,47.6,12.9)[amenity=cafe];node(46.4,10.1,47.6,12.9)[amenity=pub];node(46.4,10.1,47.6,12.9)[amenity=bar];node(46.4,10.1,47.6,12.9)[amenity=bistro];node(46.4,10.1,47.6,12.9)[amenity=fast_food];);out center body;'

print(f"Query: {len(q)} chars", flush=True)
t0 = time.time()
r = requests.post(ov, data={"data": q}, headers=hdrs, timeout=120)
elapsed = time.time() - t0
print(f"Status: {r.status_code} in {elapsed:.1f}s", flush=True)
if r.status_code == 200:
    data = r.json()
    print(f"Elements: {len(data.get('elements',[]))}", flush=True)
    # Show some random names
    for e in data.get("elements", [])[:5]:
        name = e.get("tags", {}).get("name", "?")
        print(f"  Sample: {name}", flush=True)
else:
    print(f"Body: {r.text[:200]}", flush=True)
