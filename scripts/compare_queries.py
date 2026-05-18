#!/usr/bin/env python3
"""Compare queries between test_bbox and scraper."""

# Working query from test_bbox.py
q_working_ways = """[out:json][timeout:120];(node(46.4,10.1,47.6,12.9)[amenity=restaurant];node(46.4,10.1,47.6,12.9)[amenity=cafe];node(46.4,10.1,47.6,12.9)[amenity=pub];node(46.4,10.1,47.6,12.9)[amenity=bar];node(46.4,10.1,47.6,12.9)[amenity=bistro];node(46.4,10.1,47.6,12.9)[amenity=fast_food];way(46.4,10.1,47.6,12.9)[amenity=restaurant];way(46.4,10.1,47.6,12.9)[amenity=cafe];);out center body;"""

# Build the scraper query
s, w, n, e = 46.4, 10.1, 47.6, 12.9
amenity_types = ["restaurant", "cafe", "pub", "bar", "bistro", "fast_food", "food_court"]
timeout = 180

lines = [f"[out:json][timeout:{timeout}];"]
lines.append("(")
for amenity in amenity_types:
    lines.append(f'  node({s},{w},{n},{e})[amenity={amenity}];')
for amenity in amenity_types:
    lines.append(f'  way({s},{w},{n},{e})[amenity={amenity}];')
lines.append(");")
lines.append("out center body;")
q_scraper = "\n".join(lines)

lines2 = [f"[out:json][timeout:{timeout}];"]
lines2.append("(")
for amenity in amenity_types:
    lines2.append(f'  node({s},{w},{n},{e})[amenity={amenity}];')
lines2.append(");")
lines2.append("out center body;")
q_scraper_nodes = "\n".join(lines2)

print("=== Working query ===")
print(repr(q_working_ways))
print()
print("=== Scraper query (with ways) ===")
print(repr(q_scraper))
print()
print("=== Scraper query (nodes only) ===")
print(repr(q_scraper_nodes))

# Test both
import requests
ov = "https://overpass-api.de/api/interpreter"
hdrs = {"User-Agent": "Test/1.0", "Accept": "application/json"}

for name, q in [("working_ways", q_working_ways), ("scraper", q_scraper), ("scraper_nodes", q_scraper_nodes)]:
    print(f"\n--- Testing: {name} ({len(q)} chars) ---", flush=True)
    r = requests.post(ov, data={"data": q}, headers=hdrs, timeout=30)
    print(f"Status: {r.status_code}", flush=True)
    if r.status_code == 200:
        data = r.json()
        print(f"Elements: {len(data.get('elements',[]))}", flush=True)
    else:
        print(f"Body: {r.text[:200]}", flush=True)
